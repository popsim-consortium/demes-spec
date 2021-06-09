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
import itertools
import operator
from typing import Dict, List, Union


# Validator functions. These are used as arguments to the pop_x functions and
# check properties of the values.


def is_positive(value):
    return value > 0


def is_non_negative(value):
    return value >= 0


def is_fraction(value):
    return 0 <= value <= 1


def is_nonempty(value):
    return len(value) > 0


def is_identifier(value):
    return value.isidentifier()


def validate_item(name, value, required_type, validator=None):
    if not isinstance(value, required_type):
        raise TypeError(
            f"Attribute '{name}' must be a {required_type}; "
            f"current type is {type(value)}."
        )
    if validator is not None and not validator(value):
        validator_name = validator.__name__[3:]  # Strip off is_ from function name
        raise ValueError(f"Attribute '{name}' is not {validator_name}")


# We need to use this trick because None is a meaninful input value for these
# pop_x functions.
NO_DEFAULT = object()


def pop_item(data, name, *, required_type, default=NO_DEFAULT, validator=None):
    if name in data:
        value = data.pop(name)
        if value is None and default is None:
            # This is treated the same as not specifying the value
            return value
        validate_item(name, value, required_type, validator)
    else:
        if default is NO_DEFAULT:
            raise KeyError(f"Attribute '{name}' is required")
        value = default
    return value


def pop_list(data, name, default=NO_DEFAULT, required_type=None, validator=None):
    value = pop_item(data, name, default=default, required_type=list)
    if required_type is not None and default is not None:
        for item in value:
            validate_item(name, item, required_type, validator)
    return value


def pop_object(data, name, default=NO_DEFAULT):
    return pop_item(data, name, default=default, required_type=dict)


def pop_string(data, name, default=NO_DEFAULT, validator=None):
    return pop_item(data, name, default=default, required_type=str, validator=validator)


def pop_number(data, name, default=NO_DEFAULT, validator=None):
    return pop_item(
        data, name, default=default, required_type=numbers.Number, validator=validator
    )


def check_empty(data):
    if len(data) != 0:
        raise ValueError(f"Extra fields are not permitted:{data}")


def check_defaults(defaults, allowed_fields):
    for key in defaults.keys():
        if key not in allowed_fields:
            raise ValueError(
                f"Only fields {allowed_fields} can be specified in the defaults"
            )


def insert_defaults(data, defaults):
    for key, value in defaults.items():
        if key not in data:
            data[key] = value


@dataclasses.dataclass
class Epoch:
    end_time: Union[float, None]
    start_size: Union[float, None]
    end_size: Union[float, None]
    size_function: str
    selfing_rate: float
    cloning_rate: float

    def asdict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class Deme:
    name: str
    start_time: Union[None, float]
    description: Union[str, None]
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

    def exists_at(self, time):
        return self.start_time >= time >= self.end_time

    def asdict(self) -> dict:
        # It's easier to make our own asdict here to avoid recursion issues
        # with dataclasses.asdict through the ancestors list
        return {
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time,
            "epochs": [epoch.asdict() for epoch in self.epochs],
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
            if not ancestor.exists_at(self.start_time):
                raise ValueError(
                    f"Deme {ancestor.name} (end_time={ancestor.end_time}) doesn't "
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

        # TODO validate the size_function. E.g., if the size_function is constant
        # and the values aren't the same then it should be an error.
        # Or, just check if it's "exponential". See
        # https://github.com/popsim-consortium/demes-spec/issues/34

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

    def validate(self):
        if len(self.proportions) != len(self.ancestors):
            raise ValueError("proportions must be same length as ancestors")
        if len(self.ancestors) > 0:
            if not math.isclose(sum(self.proportions), 1):
                raise ValueError("Sum of proportions must be approximately 1")


@dataclasses.dataclass
class Pulse:
    source: Deme
    dest: Deme
    time: float
    proportion: float

    def asdict(self) -> dict:
        d = dataclasses.asdict(self)
        d["source"] = self.source.name
        d["dest"] = self.dest.name
        return d

    def validate(self):
        if self.source == self.dest:
            raise ValueError("Cannot have source deme equal to dest")
        if not (self.source.start_time > self.time >= self.source.end_time):
            raise ValueError(
                f"Deme {self.source.name} does not exist at time {self.time}"
            )
        if not (self.dest.start_time >= self.time > self.dest.end_time):
            raise ValueError(
                f"Deme {self.dest.name} does not exist at time {self.time}"
            )


@dataclasses.dataclass
class Migration:
    rate: Union[float, None]
    start_time: Union[float, None]
    end_time: Union[float, None]

    def _resolve(self, demes):
        if self.start_time is None:
            self.start_time = min(deme.start_time for deme in demes)
        if self.end_time is None:
            self.end_time = max(deme.end_time for deme in demes)

    def _validate(self, demes):
        if self.start_time <= self.end_time:
            raise ValueError("start_time must be > end_time")
        if len(set([deme.name for deme in demes])) != len(demes):
            raise ValueError("Cannot migrate from a deme to itself")
        for deme in demes:
            if self.start_time > deme.start_time or self.end_time < deme.end_time:
                raise ValueError(
                    "Migration time interval must be within the each deme's "
                    "time interval"
                )


@dataclasses.dataclass
class SymmetricMigration(Migration):
    demes: List[Deme]

    def asdict(self) -> dict:
        d = dataclasses.asdict(self)
        d["demes"] = [deme.name for deme in self.demes]
        return d

    def resolve(self):
        self._resolve(self.demes)

    def validate(self):
        self._validate(self.demes)


@dataclasses.dataclass
class AsymmetricMigration(Migration):
    source: Deme
    dest: Deme

    def asdict(self) -> dict:
        d = dataclasses.asdict(self)
        d["source"] = self.source.name
        d["dest"] = self.dest.name
        return d

    def resolve(self):
        self._resolve([self.source, self.dest])

    def validate(self):
        self._validate([self.source, self.dest])


@dataclasses.dataclass
class Graph:
    time_units: str
    generation_time: Union[float, None]
    doi: List[str]
    description: Union[str, None]
    demes: Dict[str, Deme] = dataclasses.field(default_factory=dict)
    migrations: List[Migration] = dataclasses.field(default_factory=list)
    pulses: List[Pulse] = dataclasses.field(default_factory=list)

    def add_deme(
        self,
        name: str,
        description: Union[str, None],
        start_time: Union[float, None],
        ancestors: List[str],
        proportions: Union[List[float], None],
    ) -> Deme:
        deme = Deme(
            name=name,
            description=description,
            start_time=start_time,
            ancestors=[self.demes[deme_id] for deme_id in ancestors],
            proportions=proportions,
        )
        if deme.name in self.demes:
            raise ValueError("Duplicate deme ID")
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
    ) -> Migration:
        migration: Migration
        if source is not None and dest is not None:
            migration = AsymmetricMigration(
                rate=rate,
                start_time=start_time,
                end_time=end_time,
                source=self.demes[source],
                dest=self.demes[dest],
            )
            if demes is not None:
                raise ValueError("Cannot specify both demes and source/dest")
        elif demes is not None:
            migration = SymmetricMigration(
                rate=rate,
                start_time=start_time,
                end_time=end_time,
                demes=[self.demes[deme_id] for deme_id in demes],
            )
        else:
            raise ValueError("Must specify either source and dest, or demes")
        self.migrations.append(migration)
        return migration

    def add_pulse(self, source: str, dest: str, time: float, proportion: float):
        pulse = Pulse(
            source=self.demes[source],
            dest=self.demes[dest],
            time=time,
            proportion=proportion,
        )
        self.pulses.append(pulse)
        return pulse

    def __str__(self):
        data = self.asdict()
        return pprint.pformat(data, indent=2)

    def asdict(self):
        d = dataclasses.asdict(self)
        d["demes"] = [deme.asdict() for deme in self.demes.values()]
        d["migrations"] = [migration.asdict() for migration in self.migrations]
        d["pulses"] = [pulse.asdict() for pulse in self.pulses]
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
        for deme in self.demes.values():
            deme.validate()
        for pulse in self.pulses:
            pulse.validate()
        for migration in self.migrations:
            migration.validate()

        # A deme can't receive more than 100% of its ancestry from pulses at
        # any given time.
        for (dest, time), pulses in itertools.groupby(
            self.pulses, key=operator.attrgetter("dest", "time")
        ):
            if sum(pulse.proportion for pulse in pulses) > 1:
                raise ValueError(
                    f"Pulse proportions into {dest.name} at time {time} "
                    "sum to more than 1"
                )

    def resolve(self):
        # A demes ancestors must be listed before it, so any deme we
        # visit must always be visited after its ancestors.
        for deme in self.demes.values():
            deme.resolve()
        for migration in self.migrations:
            migration.resolve()


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
        description=pop_string(data, "description", None),
        time_units=pop_string(data, "time_units", None),
        doi=pop_list(data, "doi", [], str, is_nonempty),
        generation_time=pop_number(data, "generation_time", None, is_positive),
    )
    check_defaults(
        deme_defaults, ["description", "start_time", "ancestors", "proportions"]
    )

    for deme_data in pop_list(data, "demes"):
        insert_defaults(deme_data, deme_defaults)
        deme = graph.add_deme(
            name=pop_string(deme_data, "name", validator=is_identifier),
            description=pop_string(deme_data, "description", None),
            start_time=pop_number(deme_data, "start_time", None),
            ancestors=pop_list(deme_data, "ancestors", [], str, is_identifier),
            proportions=pop_list(
                deme_data, "proportions", None, numbers.Number, is_fraction
            ),
        )

        local_defaults = pop_object(deme_data, "defaults", {})
        local_epoch_defaults = pop_object(local_defaults, "epoch", {})
        check_empty(local_defaults)
        epoch_defaults = global_epoch_defaults.copy()
        epoch_defaults.update(local_epoch_defaults)

        check_defaults(
            epoch_defaults,
            [
                "end_time",
                "start_size",
                "end_size",
                "selfing_rate",
                "cloning_rate",
                "size_function",
            ],
        )
        # There is always at least one epoch defined with the default values.
        for epoch_data in pop_list(deme_data, "epochs", [{}]):
            insert_defaults(epoch_data, epoch_defaults)
            deme.add_epoch(
                end_time=pop_number(epoch_data, "end_time", None, is_non_negative),
                start_size=pop_number(epoch_data, "start_size", None, is_positive),
                end_size=pop_number(epoch_data, "end_size", None, is_positive),
                selfing_rate=pop_number(epoch_data, "selfing_rate", 0, is_fraction),
                cloning_rate=pop_number(epoch_data, "cloning_rate", 0, is_fraction),
                size_function=pop_string(epoch_data, "size_function", "exponential"),
            )
            check_empty(epoch_data)
        check_empty(deme_data)

    check_defaults(
        migration_defaults,
        ["rate", "start_time", "end_time", "source", "dest", "demes"],
    )
    for migration_data in pop_list(data, "migrations", []):
        insert_defaults(migration_data, migration_defaults)
        graph.add_migration(
            rate=pop_number(migration_data, "rate", validator=is_fraction),
            start_time=pop_number(migration_data, "start_time", None, is_positive),
            end_time=pop_number(migration_data, "end_time", None, is_non_negative),
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

    check_defaults(pulse_defaults, ["source", "dest", "time", "proportion"])
    for pulse_data in pop_list(data, "pulses", []):
        insert_defaults(pulse_data, pulse_defaults)
        graph.add_pulse(
            source=pop_string(pulse_data, "source", validator=is_identifier),
            dest=pop_string(pulse_data, "dest", validator=is_identifier),
            time=pop_number(pulse_data, "time", validator=is_non_negative),
            proportion=pop_number(pulse_data, "proportion", validator=is_fraction),
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
