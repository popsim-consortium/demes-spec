# A simple parser that builds a fully-qualified Demes Graph from an input JSON
# string.
#
# Requires Python 3.7+.
#
# This implementation is NOT recommended for use in any downstream software and
# is provided purely as reference material for parser writers (i.e., in other
# programming languages). Python users should use the "demes" package in their
# software: https://github.com/popsim-consortium/demes-python
#
# The entry point is the ``parse`` function, which returns a fully-qualified
# Graph. The implementation is written with clarity and correctness as the main
# priorities. Its main purpose is to remove any potential ambiguities that may
# exist in the written specification and to simplify the process of writing
# other parsers. In the interest of simplicity, the parser does not generate
# useful error messages in all cases (but we would hope that practical
# implementations would).
#
# Type annotations are used where they help with readability, but not applied
# exhaustively.
from __future__ import annotations

import math
import numbers
import copy
import pprint
import dataclasses
from typing import Dict, List, Union

# Numerical wiggle room.
EPSILON = 1e-6

# JSON does not provide a way to encode IEEE infinity values, which we
# require to describe start_time values. To work around this we use the
# string "Infinity" to represent IEEE positive infinity.
JSON_INFINITY_STR = "Infinity"


def parse(data: dict) -> Graph:
    # Parsing is done by popping items out of the input data dictionary and
    # creating the appropriate Python objects. We ensure that extra items
    # have not been included in the data payload by checking if the objects
    # are empty once we have removed all the values defined in the
    # specification. Type and range validation of simple items (e.g., the
    # value must be a positive integer) is performed at the same time,
    # using the pop_x functions. Once the full object model of the input
    # data has been built, the rules for creating a fully-qualified Demes
    # graph are applied in the "resolve" functions. Finally, we validate
    # the fully-qualified graph to ensure that relationships between the
    # entities have been specified correctly.
    data = copy.deepcopy(data)

    defaults = pop_object(data, "defaults", {})
    deme_defaults = pop_object(defaults, "deme", {})
    migration_defaults = pop_object(defaults, "migration", {})
    pulse_defaults = pop_object(defaults, "pulse", {})
    # epoch defaults may also be specified within a Deme definition.
    global_epoch_defaults = pop_object(defaults, "epoch", {})
    check_empty(defaults)

    graph = Graph(
        description=pop_string(data, "description", ""),
        time_units=pop_string(data, "time_units", None),
        doi=pop_list(data, "doi", [], str, is_nonempty),
        generation_time=pop_number(
            data, "generation_time", None, is_positive_and_finite
        ),
        metadata=pop_object(data, "metadata", {}),
    )
    check_defaults(
        deme_defaults,
        dict(
            description=(str, None),
            start_time=((str, numbers.Number), is_positive_or_json_infinity),
            ancestors=(list, is_list_of_identifiers),
            proportions=(list, is_list_of_fractions),
        ),
    )

    allowed_epoch_defaults = dict(
        end_time=(numbers.Number, is_non_negative_and_finite),
        start_size=(numbers.Number, is_positive_and_finite),
        end_size=(numbers.Number, is_positive_and_finite),
        selfing_rate=(numbers.Number, is_fraction),
        cloning_rate=(numbers.Number, is_fraction),
        size_function=(str, None),
    )
    check_defaults(global_epoch_defaults, allowed_epoch_defaults)

    for deme_data in pop_list(data, "demes"):
        insert_defaults(deme_data, deme_defaults)
        deme = graph.add_deme(
            name=pop_string(deme_data, "name", validator=is_identifier),
            description=pop_string(deme_data, "description", ""),
            start_time=pop_number(
                deme_data,
                "start_time",
                None,
                is_positive_or_json_infinity,
                allow_inf=True,
            ),
            ancestors=pop_list(deme_data, "ancestors", [], str, is_identifier),
            proportions=pop_list(
                deme_data, "proportions", None, numbers.Number, is_fraction
            ),
        )

        local_defaults = pop_object(deme_data, "defaults", {})
        local_epoch_defaults = pop_object(local_defaults, "epoch", {})
        check_empty(local_defaults)
        check_defaults(local_epoch_defaults, allowed_epoch_defaults)
        epoch_defaults = global_epoch_defaults.copy()
        epoch_defaults.update(local_epoch_defaults)
        check_defaults(epoch_defaults, allowed_epoch_defaults)

        # There is always at least one epoch defined with the default values.
        for epoch_data in pop_list(deme_data, "epochs", [{}]):
            insert_defaults(epoch_data, epoch_defaults)
            deme.add_epoch(
                end_time=pop_number(
                    epoch_data, "end_time", None, is_non_negative_and_finite
                ),
                start_size=pop_number(
                    epoch_data, "start_size", None, is_positive_and_finite
                ),
                end_size=pop_number(
                    epoch_data, "end_size", None, is_positive_and_finite
                ),
                selfing_rate=pop_number(epoch_data, "selfing_rate", 0, is_fraction),
                cloning_rate=pop_number(epoch_data, "cloning_rate", 0, is_fraction),
                size_function=pop_string(epoch_data, "size_function", None),
            )
            check_empty(epoch_data)
        check_empty(deme_data)

        if len(deme.epochs) == 0:
            raise ValueError(f"no epochs for deme {deme.name}")

    if len(graph.demes) == 0:
        raise ValueError("the graph must have one or more demes")

    check_defaults(
        migration_defaults,
        dict(
            rate=(numbers.Number, is_fraction),
            start_time=((numbers.Number, str), is_positive_or_json_infinity),
            end_time=(numbers.Number, is_non_negative_and_finite),
            source=(str, is_identifier),
            dest=(str, is_identifier),
            demes=(list, is_list_of_identifiers),
        ),
    )
    for migration_data in pop_list(data, "migrations", []):
        insert_defaults(migration_data, migration_defaults)
        graph.add_migration(
            rate=pop_number(migration_data, "rate", validator=is_fraction),
            start_time=pop_number(
                migration_data,
                "start_time",
                None,
                is_positive_or_json_infinity,
                allow_inf=True,
            ),
            end_time=pop_number(
                migration_data, "end_time", None, is_non_negative_and_finite
            ),
            source=pop_string(migration_data, "source", None, is_nonempty),
            dest=pop_string(migration_data, "dest", None, is_nonempty),
            demes=pop_list(
                migration_data,
                "demes",
                default=None,
                required_type=str,
                validator=is_identifier,
            ),
        )
        check_empty(migration_data)

    check_defaults(
        pulse_defaults,
        dict(
            sources=(list, is_nonempty_list_of_identifiers),
            dest=(str, is_identifier),
            time=(numbers.Number, is_positive_and_finite),
            proportions=(list, is_nonempty_list_of_fractions_with_sum_less_than_1),
        ),
    )
    for pulse_data in pop_list(data, "pulses", []):
        insert_defaults(pulse_data, pulse_defaults)
        graph.add_pulse(
            sources=pop_list(
                pulse_data,
                "sources",
                default=[],
                required_type=str,
                validator=is_identifier,
            ),
            dest=pop_string(pulse_data, "dest", validator=is_identifier),
            time=pop_number(pulse_data, "time", validator=is_positive_and_finite),
            proportions=pop_list(
                pulse_data,
                "proportions",
                default=[],
                required_type=numbers.Number,
                validator=is_fraction,
            ),
        )
        check_empty(pulse_data)

    check_empty(data)

    # The input object model has now been fully populated, and local type and
    # value checking done. Default values (either from the schema or set explicitly
    # by the user via "defaults" sections) have been assigned. We now "resolve"
    # the model so that any values that can be imputed from the structure of the
    # model are set explicitly. Once this is done, we then validate the model to
    # check that the relationships between various entities make sense. Note that
    # there isn't a clean separation between resolution and validation here, since
    # some validation is simplest to perform as part of the resolution logic in
    # this particular implementation.
    graph.resolve()
    graph.validate()

    return graph


def encode_inf(value):
    if math.isinf(value):
        return JSON_INFINITY_STR
    return value


# Validator functions. These are used as arguments to the pop_x functions and
# check properties of the values.


def is_positive_or_json_infinity(value):
    return value == JSON_INFINITY_STR or value > 0


def is_positive_and_finite(value):
    return value > 0 and not math.isinf(value)


def is_non_negative_and_finite(value):
    return value >= 0 and not math.isinf(value)


def is_fraction(value):
    return 0 <= value <= 1


def is_nonempty(value):
    return len(value) > 0


def is_identifier(value):
    return value.isidentifier()


def is_list_of_identifiers(value):
    return all(isinstance(v, str) and is_identifier(v) for v in value)


def is_nonempty_list_of_identifiers(value):
    return is_list_of_identifiers(value) and len(value) > 0


def is_list_of_fractions(value):
    return all(isinstance(v, numbers.Number) and is_fraction(v) for v in value)


def is_nonempty_list_of_fractions_with_sum_less_than_1(value):
    return is_list_of_fractions(value) and len(value) > 0 and sum(value) <= 1


def validate_item(name, value, required_type, validator=None):
    if not isinstance(value, required_type):
        raise TypeError(
            f"Attribute '{name}' must be a {required_type}; "
            f"current type is {type(value)}."
        )
    if validator is not None and not validator(value):
        validator_name = validator.__name__[3:]  # Strip off is_ from function name
        raise ValueError(f"Attribute '{name}' is not {validator_name}")


# We need to use this trick because None is a meaningful input value for these
# pop_x functions.
NO_DEFAULT = object()


def pop_item(data, name, *, required_type, default=NO_DEFAULT, validator=None):
    if name in data:
        value = data.pop(name)
        validate_item(name, value, required_type, validator)
    else:
        if default is NO_DEFAULT:
            raise KeyError(f"Attribute '{name}' is required")
        value = default
    return value


def pop_list(data, name, default=NO_DEFAULT, required_type=None, validator=None):
    value = pop_item(data, name, default=default, required_type=list)
    if required_type is not None and value is not None:
        for item in value:
            validate_item(name, item, required_type, validator)
    return value


def pop_object(data, name, default=NO_DEFAULT):
    return pop_item(data, name, default=default, required_type=dict)


def pop_string(data, name, default=NO_DEFAULT, validator=None):
    return pop_item(data, name, default=default, required_type=str, validator=validator)


def pop_number(data, name, default=NO_DEFAULT, validator=None, allow_inf=False):
    # If infinite values are allowed for this number, the string "Infinity"
    # is also accepted, and so str is an accepted type. There is a small loophole
    # here in which string numbers like "1000" will be accepted by the type
    # checking machinery, but the is_positive_or_json_infinity validator
    # will catch this and raise a TypeError when it tries to compare with 0.
    if allow_inf:
        assert validator is is_positive_or_json_infinity
    required_type = (numbers.Number, str) if allow_inf else numbers.Number
    value = pop_item(
        data,
        name,
        default=default,
        required_type=required_type,
        validator=validator,
    )
    if value == JSON_INFINITY_STR:
        return math.inf
    return value


def check_empty(data):
    if len(data) != 0:
        raise ValueError(f"Extra fields are not permitted:{data}")


def check_defaults(defaults, allowed_fields):
    for key, value in defaults.items():
        if key not in allowed_fields:
            raise ValueError(
                f"Only fields {list(allowed_fields.keys())} can be specified "
                "in the defaults"
            )
        required_type, validator = allowed_fields[key]
        validate_item(key, value, required_type, validator)


def insert_defaults(data, defaults):
    for key, value in defaults.items():
        if key not in data:
            data[key] = value


@dataclasses.dataclass
class Interval:
    """
    A half-open time interval (start_time, end_time].
    """

    start_time: float
    end_time: float

    def __init__(self, start_time, end_time):
        assert start_time > end_time
        self.start_time = start_time
        self.end_time = end_time

    def intersects(self, other):
        """True if self and other intersect, False otherwise."""
        assert isinstance(other, self.__class__)
        return not (
            self.end_time >= other.start_time or other.end_time >= self.start_time
        )

    def is_subinterval(self, other):
        """True if self is completely contained within other, False otherwise."""
        assert isinstance(other, self.__class__)
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def __contains__(self, time):
        return self.start_time > time >= self.end_time


@dataclasses.dataclass
class Epoch:
    end_time: Union[float, None]
    start_size: Union[float, None]
    end_size: Union[float, None]
    size_function: str
    selfing_rate: float
    cloning_rate: float

    def as_json_dict(self) -> dict:
        return dataclasses.asdict(self)

    def resolve(self):
        if self.size_function is None:
            if self.start_size == self.end_size:
                self.size_function = "constant"
            else:
                self.size_function = "exponential"

    def validate(self):
        if self.size_function not in ("constant", "exponential", "linear"):
            raise ValueError(f"unknown size_function '{self.size_function}'")
        if self.size_function == "constant" and self.start_size != self.end_size:
            raise ValueError(
                "size_function is constant but "
                f"start_size ({self.start_size}) != end_size ({self.end_size})"
            )


@dataclasses.dataclass
class Deme:
    name: str
    start_time: Union[None, float]
    description: str
    ancestors: List[Deme]
    proportions: Union[List[float], None]
    epochs: List[Epoch] = dataclasses.field(default_factory=list)

    def add_epoch(
        self,
        end_time: Union[float, None],
        start_size: Union[float, None],
        end_size: Union[float, None],
        selfing_rate: float,
        cloning_rate: float,
        size_function: str,
    ) -> Epoch:
        epoch = Epoch(
            end_time=end_time,
            start_size=start_size,
            end_size=end_size,
            selfing_rate=selfing_rate,
            cloning_rate=cloning_rate,
            size_function=size_function,
        )
        self.epochs.append(epoch)
        return epoch

    @property
    def end_time(self):
        return self.epochs[-1].end_time

    @property
    def time_interval(self):
        return Interval(self.start_time, self.end_time)

    def as_json_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "start_time": encode_inf(self.start_time),
            "epochs": [epoch.as_json_dict() for epoch in self.epochs],
            "proportions": self.proportions,
            "ancestors": [deme.name for deme in self.ancestors],
        }

    def __resolve_times(self):
        if self.start_time is None:
            default = math.inf
            if len(self.ancestors) == 1:
                default = self.ancestors[0].epochs[-1].end_time
            elif len(self.ancestors) > 1:
                raise ValueError(
                    "Must explicitly set Deme.start_time when > 1 ancestor"
                )
            self.start_time = default
        if len(self.ancestors) == 0 and not math.isinf(self.start_time):
            raise ValueError(
                f"deme {self.name} has finite start_time, but no ancestors"
            )

        for ancestor in self.ancestors:
            if self.start_time not in ancestor.time_interval:
                raise ValueError(
                    f"Deme {ancestor.name} ({ancestor.time_interval}) doesn't "
                    f"exist at deme {self.name}'s start_time ({self.start_time})"
                )

        # The last epoch has a default end_time of 0
        last_epoch = self.epochs[-1]
        if last_epoch.end_time is None:
            last_epoch.end_time = 0
        last_time = self.start_time
        for epoch in self.epochs:
            if epoch.end_time is None:
                raise ValueError("Epoch end_time must be specified")
            if epoch.end_time >= last_time:
                raise ValueError("Epoch end_times must be in decreasing order.")
            last_time = epoch.end_time

    def __resolve_sizes(self):
        first_epoch = self.epochs[0]
        # The first epoch must specify either start_size or end_size
        if first_epoch.start_size is None and first_epoch.end_size is None:
            raise ValueError(
                "Must specify one or more of start_size and end_size "
                "for the initial epoch"
            )
        if first_epoch.start_size is None:
            first_epoch.start_size = first_epoch.end_size
        if first_epoch.end_size is None:
            first_epoch.end_size = first_epoch.start_size
        last_epoch = first_epoch
        for epoch in self.epochs[1:]:
            if epoch.start_size is None:
                epoch.start_size = last_epoch.end_size
            if epoch.end_size is None:
                epoch.end_size = epoch.start_size
            last_epoch = epoch

        if self.start_time == math.inf:
            if first_epoch.start_size != first_epoch.end_size:
                raise ValueError(
                    "Cannot have varying population size in an infinite time interval"
                )

    def __resolve_proportions(self):
        if self.proportions is None:
            if len(self.ancestors) == 0:
                self.proportions = []
            elif len(self.ancestors) == 1:
                self.proportions = [1]
            else:
                raise ValueError("Must specify proportions for > 1 ancestor demes")

    def resolve(self):
        self.__resolve_times()
        self.__resolve_sizes()
        self.__resolve_proportions()
        for epoch in self.epochs:
            epoch.resolve()

    def validate(self):
        if len(self.proportions) != len(self.ancestors):
            raise ValueError("proportions must be same length as ancestors")
        if len(self.ancestors) > 0:
            if not math.isclose(sum(self.proportions), 1):
                raise ValueError("Sum of proportions must be approximately 1")
        if len(set(anc.name for anc in self.ancestors)) != len(self.ancestors):
            raise ValueError("ancestors list contains duplicates")
        for epoch in self.epochs:
            epoch.validate()


@dataclasses.dataclass
class Pulse:
    sources: List[Deme]
    dest: Deme
    time: float
    proportions: List[float]

    def as_json_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["sources"] = [source.name for source in self.sources]
        d["dest"] = self.dest.name
        return d

    def validate(self):
        sources_names = set(source.name for source in self.sources)
        if self.dest.name in sources_names:
            raise ValueError("Cannot have source deme equal to dest")
        if len(sources_names) != len(self.sources):
            raise ValueError("Duplicate deme in sources")
        if len(self.sources) == 0:
            raise ValueError("Must have one or more source demes")
        if len(self.sources) != len(self.proportions):
            raise ValueError("Sources and proportions must have same lengths")
        for source in self.sources:
            if self.time not in source.time_interval:
                raise ValueError(
                    f"Deme {source.name} does not exist at time {self.time}"
                )
        # Time limits for the destination deme are different to the source deme,
        # because the destination deme is affected immediately after the time
        # of the pulse. Thus, a pulse can occur at the destination deme's
        # start_time, but not at the destination deme's end_time.
        if not (self.dest.start_time >= self.time > self.dest.end_time):
            raise ValueError(
                f"Deme {self.dest.name} does not exist at time {self.time}"
            )

        if sum(self.proportions) > 1 + EPSILON:
            raise ValueError(
                f"Pulse proportions into {self.dest.name} at time {self.time} "
                "sum to more than 1"
            )


@dataclasses.dataclass
class Migration:
    rate: Union[float, None]
    start_time: Union[float, None]
    end_time: Union[float, None]
    source: Deme
    dest: Deme

    @property
    def time_interval(self):
        return Interval(self.start_time, self.end_time)

    def as_json_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["start_time"] = encode_inf(self.start_time)
        d["source"] = self.source.name
        d["dest"] = self.dest.name
        return d

    def resolve(self):
        if self.start_time is None:
            self.start_time = min(self.source.start_time, self.dest.start_time)
        if self.end_time is None:
            self.end_time = max(self.source.end_time, self.dest.end_time)

    def validate(self):
        if self.start_time <= self.end_time:
            raise ValueError("start_time must be > end_time")
        if self.source.name == self.dest.name:
            raise ValueError("Cannot migrate from a deme to itself")
        for deme in [self.source, self.dest]:
            if not self.time_interval.is_subinterval(deme.time_interval):
                raise ValueError(
                    "Migration time interval must be within the each deme's "
                    "time interval"
                )


@dataclasses.dataclass
class Graph:
    time_units: str
    generation_time: Union[float, None]
    doi: List[str]
    description: str
    metadata: dict
    demes: Dict[str, Deme] = dataclasses.field(default_factory=dict)
    migrations: List[Migration] = dataclasses.field(default_factory=list)
    pulses: List[Pulse] = dataclasses.field(default_factory=list)

    def add_deme(
        self,
        name: str,
        description: str,
        start_time: Union[float, None],
        ancestors: List[str],
        proportions: Union[List[float], None],
    ) -> Deme:
        deme = Deme(
            name=name,
            description=description,
            start_time=start_time,
            ancestors=[self.demes[deme_name] for deme_name in ancestors],
            proportions=proportions,
        )
        if deme.name in self.demes:
            raise ValueError(f"Duplicate deme name '{deme.name}'")
        self.demes[deme.name] = deme
        return deme

    def add_migration(
        self,
        *,
        rate: float,
        start_time: Union[float, None],
        end_time: Union[float, None],
        source: Union[str, None],
        dest: Union[str, None],
        demes: Union[List[str], None],
    ) -> List[Migration]:
        migrations: List[Migration] = []
        if not (
            # symmetric
            (demes is not None and source is None and dest is None)
            # asymmetric
            or (demes is None and source is not None and dest is not None)
        ):
            raise ValueError("Must specify either source and dest, or demes")
        if source is not None:
            assert dest is not None
            migrations.append(
                Migration(
                    rate=rate,
                    start_time=start_time,
                    end_time=end_time,
                    source=self.demes[source],
                    dest=self.demes[dest],
                )
            )
        else:
            assert demes is not None
            if len(demes) < 2:
                raise ValueError("Must specify two or more deme names")
            for j, deme_a in enumerate(demes, 1):
                for deme_b in demes[j:]:
                    migration_ab = Migration(
                        rate=rate,
                        start_time=start_time,
                        end_time=end_time,
                        source=self.demes[deme_a],
                        dest=self.demes[deme_b],
                    )
                    migration_ba = Migration(
                        rate=rate,
                        start_time=start_time,
                        end_time=end_time,
                        source=self.demes[deme_b],
                        dest=self.demes[deme_a],
                    )
                    migrations.extend([migration_ab, migration_ba])
        self.migrations.extend(migrations)
        return migrations

    def add_pulse(
        self, sources: List[str], dest: str, time: float, proportions: List[float]
    ):
        pulse = Pulse(
            sources=[self.demes[source] for source in sources],
            dest=self.demes[dest],
            time=time,
            proportions=proportions,
        )
        self.pulses.append(pulse)
        return pulse

    def __str__(self):
        data = self.as_json_dict()
        return pprint.pformat(data, indent=2)

    def as_json_dict(self):
        d = dataclasses.asdict(self)
        d["demes"] = [deme.as_json_dict() for deme in self.demes.values()]
        d["migrations"] = [migration.as_json_dict() for migration in self.migrations]
        d["pulses"] = [pulse.as_json_dict() for pulse in self.pulses]
        return d

    def validate(self):
        if self.generation_time is None:
            if self.time_units == "generations":
                self.generation_time = 1
            else:
                raise ValueError(
                    "Must specify Graph.generation_time if time_units is not "
                    "'generations'"
                )
        if self.time_units == "generations" and self.generation_time != 1:
            raise ValueError(
                "If time_units are in generations, generation_time must be 1"
            )
        for deme in self.demes.values():
            deme.validate()
        for pulse in self.pulses:
            pulse.validate()
        for migration in self.migrations:
            migration.validate()

        # Migrations involving the same source and dest can't overlap temporally.
        for j, migration_a in enumerate(self.migrations, 1):
            for migration_b in self.migrations[j:]:
                if (
                    migration_a.source == migration_b.source
                    and migration_a.dest == migration_b.dest
                    and migration_a.time_interval.intersects(migration_b.time_interval)
                ):
                    start_time = min(migration_a.end_time, migration_b.end_time)
                    end_time = max(migration_a.start_time, migration_b.start_time)
                    raise ValueError(
                        f"Competing migration definitions for {migration_a.source.name} "
                        f"and {migration_a.dest.name} during time interval "
                        f"({start_time}, {end_time}]"
                    )

        # The rate of migration entering a deme cannot be more than 1 in any
        # given interval of time.
        time_boundaries = set()
        time_boundaries.update(migration.start_time for migration in self.migrations)
        time_boundaries.update(migration.end_time for migration in self.migrations)
        time_boundaries.discard(math.inf)
        end_times = sorted(time_boundaries, reverse=True)
        start_times = [math.inf] + end_times[:-1]
        ingress_rates = {deme_name: [0.0] * len(end_times) for deme_name in self.demes}
        for j, (start_time, end_time) in enumerate(zip(start_times, end_times)):
            current_interval = Interval(start_time, end_time)
            for migration in self.migrations:
                if current_interval.intersects(migration.time_interval):
                    rate = ingress_rates[migration.dest.name][j] + migration.rate
                    if rate > 1 + EPSILON:
                        raise ValueError(
                            f"Migration rates into {migration.dest.name} sum to "
                            "more than 1 during the time inverval "
                            f"({start_time}, {end_time}]"
                        )
                    ingress_rates[migration.dest.name][j] = rate

    def resolve(self):
        # A deme's ancestors must be listed before it, so any deme we
        # visit must always be visited after its ancestors.
        for deme in self.demes.values():
            deme.resolve()
        for migration in self.migrations:
            migration.resolve()

        # Sort pulses from oldest to youngest.
        # In a discrete-time setting, non-integer pulse times that are distinct
        # could be rounded to the same time value. If the input file has the pulses
        # in time-ascending order, then the pulses would occur in the opposite order
        # compared to a continuous-time simulator. Sorting before the rounding
        # occurs avoids this ambiguity, so we explicitly require pulses to be
        # sorted as part of the parser.
        # Note that Python implements "stable" sorting, which maintains the order
        # of pulses that have the same time value to start with (as required by
        # the spec).
        self.pulses.sort(key=lambda pulse: pulse.time, reverse=True)
