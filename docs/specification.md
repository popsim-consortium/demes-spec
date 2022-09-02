(sec_spec)=

# Specification


## Introduction

Demes is a specification for describing population genetic models
of demographic history. This specification precisely defines the
population genetics model and its assumptions, along with
the data model used for interchange and the required behaviour
of implementations.

The Demes standard is largely agnostic to the processes that occur
within populations, and provides a minimal set of parameters that
can accommodate a wide spectrum of population genetic models.


:::{admonition} Who is this specification for?
This specification is intended to provide a detailed and definitive resource
for the following groups:

- Those implementing support for Demes as an input or output format in their programs
- Those implementing a Demes parser

As such, this specification contains a lot of detail that is not
interesting to most users.
If you wish to learn how to understand and create your own
Demes models, please see the {ref}`sec_tutorial` instead.
:::

## Note to Readers

To provide feedback on this specification, please use the
[issue tracker](https://github.com/popsim-consortium/demes-spec/issues).


(sec_spec_terminology)=

## Conventions and Terminology

The term "Demes" in this document is to be interpreted as a
reference to this specification. A {ref}`deme<sec_spec_mdm_deme>`
refers to a set of individuals that can be modelled by a fixed
set of parameters; to avoid confusion with name of the specification
we will usually use the term "population", in the understanding that
the terms are equivalent for the purposes of this document.

:::{todo}
Define the human and machine data models. And link to assumptions.
:::

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

The terms "JSON", "JSON text", "JSON value", "member", "element", "object",
"array", "number", "string", "boolean", "true", "false", and "null" in this
document are to be interpreted as defined in
[RFC 8259](https://datatracker.ietf.org/doc/html/rfc8259).

The term "JSON Schema" in this document is to be interpreted as defined
in the JSON Schema
[core specification](https://json-schema.org/draft/2020-12/json-schema-core.html).


(sec_spec_infinity)=
### Infinity

JSON does not define an encoding for infinite-valued numbers.
However, infinite values are used in Demes for start times.
When **writing** a Demes model to a format that does not permit infinity,
such as JSON, the string "Infinity" must be used to encode infinity.
When writing to formats that do support infinity, such as YAML, the native
encoding for infinity should be used instead (`.inf` in YAML).
When **reading** a Demes model, the string "Infinity" must be decoded to mean
an infinite-valued number. When reading from formats that do support infinity,
the format's native encoding for infinite-valued numbers must also be
supported.

(sec_spec_mdm)=
## Machine Data Model

The Demes Machine Data Model (MDM) is a
formal representation of the Demes model as
a JSON document.
The MDM is designed to be
used as input by programs such as population genetics simulators,
and explicitly includes all necessary details.
The structure of JSON
documents conforming to the specification is formally defined
in the {ref}`sec_spec_mdm_schema`, and the detailed requirements for each of the
elements in this data model are defined in this section.

The Demes {ref}`Human Data Model <sec_spec_hdm>` (HDM)
is a closely related specification that is intended
to be easily human-readable and writable.
An MDM document is also a valid HDM document.
An MDM document is constructed by {ref}`resolving <sec_spec_hdm_resolution>`
and {ref}`validating <sec_spec_hdm_validation>` an HDM document.

(sec_spec_defs_common)=

### Common concepts

This section provides details on properties that occur in multiple
contexts.

(sec_spec_mdm_time)=
#### Time

Times are specified as units in the past, so that time zero
corresponds to the final generation or "now", and event times in the past are
values greater than zero with larger values for events that occur in the more
distant past.
By default, time is measured in generations, but other values ("years",
for example) are allowed.
When time units
are not given in generations, the generation time must also be specified so
that times can be converted into generations. In general, as time flows from
the past to the present, populations, epochs, and migration events should be
specified in their order of appearance, so that their times are in descending
order.

(sec_spec_mdm_population_sizes)=
#### Population sizes

A fundamental concept in demes is the population size.

:::{todo}
Things to cover:

- We're counting **individuals** not genomes
- We usually mean the population size in expectation, but there's
  no hard requirements. For example, it's up the implementation whether it thinks
  a population size of 0.33 is meaningful. Clarify with
  some examples from forward and backward sims.
- What do proportions mean? Similar point to pop size above. Give forward
  pointers to sections we mention proportions in.
- What do we mean by migration of individuals? Forward pointers to sections.
:::

(sec_spec_mdm_metadata)=
#### Metadata

:::{todo}
Discussion of metadata. What's it for?
:::

### MDM documents

The top-level MDM document describes a single instance of a Demes model.

Each MDM document contains the following list of properties. All
properties MUST be specified, and additional properties MUST NOT be
included in these documents. Please see the {ref}`sec_spec_mdm_schema`
for definitive details on the types and structure of these properties.

#### description
A concise description of the demographic model.

#### doi
The DOI(s) of the publication(s) in which the model was inferred or
originally described.

#### metadata
An object containing arbitrary additional properties and values.
May be empty.

(sec_spec_mdm_time_units)=
#### time_units
The units of time used to specify times and time intervals. These
SHOULD be one of "generations" or "years".

#### generation_time
The number by which times must be divided, to convert them to have
units of generations.
Hence ``generation_time`` uses the same time units specified by ``time_units``.

#### demes
The list of {ref}`demes<sec_spec_mdm_deme>` in the model.
At least one deme MUST be specified.

#### pulses
The list of {ref}`pulses <sec_spec_mdm_pulse>` in the model.

#### migrations
The list of {ref}`migrations<sec_spec_mdm_migration>` in the model.

(sec_spec_mdm_deme)=

### Deme

A Deme is a single population (see the {ref}`sec_spec_terminology` for
clarification of these two terms) that exists for some non-empty
time interval. A population is defined operationally as some set
of individuals that can be modelled by a set of fixed parameters
over a series of {ref}`epochs<sec_spec_mdm_epoch>`.
Population parameters are defined per epoch, and are defined in the
{ref}`sec_spec_mdm_epoch` section below.

A population may have one
or more ancestors, which are other populations that exist at the population's
start time. If one ancestor is specified, the first generation is constructed
by randomly sampling parents from the ancestral population to contribute to
offspring in the newly generated population.

If more than one ancestor is
specified, the proportions of ancestry from each contributing population must
be provided, and those proportions must sum to one. In this case, parents are
chosen randomly from each ancestral population with probability given by those
proportions. If no ancestors are specified, the population is assumed to have
start time equal to infinity.

The deme may be a descendant of one or more demes in the graph, and may
be an ancestor to others. The deme exists over the half-open time interval
``(start_time, end_time]``, and it may continue to exist after
contributing ancestry to a descendant deme. The deme's ``end_time`` is
implicit (there is no ``end_time`` deme property), but for convenience we
define it as the ``end_time`` of the deme's last epoch.

#### name
A string identifier for a deme, which MUST be unique among all demes in a document.
Must be a valid
[python identifier](https://docs.python.org/3/reference/lexical_analysis.html#identifiers)

#### description
A concise description of the deme.

(sec_spec_mdm_deme_ancestors)=

#### ancestors
The list of ancestors of the deme at the start of the deme's first epoch.
May be an empty list if the deme has no ancestors in the graph,
in which case the ``start_time`` must be infinite.
Each ancestor must be in the graph, and each ancestor must be
specified only once. A deme must not be one of its own ancestors.

(sec_spec_mdm_deme_proportions)=

#### proportions
The proportions of ancestry derived from each of the ``ancestors``
at the start of the deme's first epoch.
The ``proportions`` must be ordered to correspond with the
order of ``ancestors``. The proportions must be an empty list or sum to 1
(within a reasonable tolerance, e.g. 1e-9). See the
{ref}`sec_spec_mdm_population_sizes` section for more details on
how these proportions should be interpreted.

(sec_spec_mdm_deme_start_time)=

#### start_time

The most ancient {ref}`time<sec_spec_mdm_time>`
at which the deme exists, in {ref}`sec_spec_mdm_time_units`
before the present. Demes with no ancestors are root demes and must
have an infinite ``start_time``. Otherwise, the ``start_time`` must
correspond with the interval of existence
for each of the deme's ``ancestors``. I.e. the ``start_time`` must
be within the half-open interval ``(deme.start_time, deme.end_time]``
for each deme in ``ancestors``.

#### epochs
The list of {ref}`epochs<sec_spec_mdm_epoch>` for this deme.
There MUST be at least one epoch for each deme.

(sec_spec_mdm_epoch)=

### Epoch

A deme-specific period of time spanning the half-open interval
``(start_time, end_time]``, in which a fixed set of population parameters
apply. The epoch's ``start_time`` is implicit (there is no ``start_time``
epoch property), but for convenience we define it as the ``end_time`` of the
previous epoch, or the deme's ``start_time`` if it is the first epoch.

Each epoch specifies the {ref}`population size<sec_spec_mdm_population_sizes>`
over that interval, which can be a constant value or function defined by start
and end sizes that must remain positive.  If an epoch has a start time of
infinity, the population size for that epoch must be constant.

Epochs can also
specify parameters for nonrandom mating, such as selfing or cloning rates,
which give the probability that offspring are generated from one generation to
the next by self-fertilisation or cloning of an individual. Selfing and cloning
rates take values between zero and one.

#### end_time
The most recent {ref}`time<sec_spec_mdm_time>` of the epoch,
in {ref}`sec_spec_mdm_time_units` before the present.

#### start_size
The population size at the epoch's ``start_time``.

#### end_size
The population size at the epoch's ``end_time``.

#### size_function
A function describing the population size change between
``start_time`` and ``end_time``.
This may be any string, but the values "constant" and "exponential"
are explicitly acknowledged to have the following meanings.

* ``constant``: the deme's size does not change over the epoch.
  ``start_size`` and ``end_size`` must be equal.
* ``exponential``: the deme's size changes exponentially from
  ``start_size`` to ``end_size`` over the epoch.
  If `t` is a time within the span of the epoch,
  the deme size `N` at time `t` can be calculated as:

  ```
  dt = (epoch.start_time - t) / (epoch.start_time - epoch.end_time)
  r = log(epoch.end_size / epoch.start_size)
  N = epoch.start_size * exp(r * dt)
  ```

``size_function`` must be ``constant`` if the epoch has an infinite ``start_time``.

#### cloning_rate
The proportion of offspring in each generation that
are expected to be generated through clonal reproduction.
`1 - cloning_rate` are expected to arise through sexual reproduction.

#### selfing_rate
Within the sexually-reproduced offspring,
`selfing_rate` are born via self-fertilisation while the rest
have parents drawn at random from the previous generation.

:::{note}
Depending on the simulator, this random drawing of parent may occur
either with or without replacement. When drawing occurs with replacement, a small
amount of residual selfing is expected, so that even with `cloning_rate=0`
and `selfing_rate=0`, selfing may still occur with probability `1/N`.
Simulators that allow variable rates of selfing are expected to clearly
document their behaviour.
:::

(sec_spec_mdm_pulse)=

### Pulse

An instantaneous pulse of migration at ``time``, from a list of source demes
(``sources``) into the destination deme (``dest``).

Pulse
migration events specify the instantaneous replacement of a given fraction of
individuals in a destination population by individuals with parents from
a source population.  The fraction must be between zero and one, and if more
than one pulse occurs at the same time, those replacement events are applied
sequentially in the order that they are specified in the model.
The list of pulses must be sorted in time-descending order.

#### sources
The list of deme names of the migration sources.

#### dest
The deme name of the migration destination.

#### time
The time of migration, in
in {ref}`sec_spec_mdm_time_units` before the present.
The demes defined by ``sources`` and ``dest`` must both exist at the given
``time``.  I.e. ``time`` must be contained in the
``(deme.start_time, deme.end_time]`` interval of the ``sources``
demes and the ``dest`` deme.

#### proportions
The proportions of ancestry in the ``dest`` deme derived from the demes
in ``sources`` immediately after the ``time`` of migration.
The ``proportions`` must be ordered to correspond with the order of
``sources``. The proportions must sum to less than or equal to 1
(within a reasonable tolerance, e.g. 1e-9).
See the
{ref}`sec_spec_mdm_population_sizes` section for more details on
how proportions should be interpreted.

#### Example: sequential application of pulses

Consider the following model:

```yaml
time_units: generations
demes:
 - name: A
   epochs:
    - start_size: 1000
 - name: B
   epochs:
    - start_size: 1000
 - name: C
   epochs:
    - start_size: 1000
pulses:
- sources: [A]
  dest: C
  proportions: [0.25]
  time: 10
- sources: [B]
  dest: C
  proportions: [0.2]
  time: 10
```

Ten (10) generations ago, pulse events occur from source demes `A` and `B`
into destination deme `C`.

We need to arrive at the final ancestry proportions for destination deme `C` after this time.
Software implementing pulse events must generate output that is equivalent to the following
procedure.

The steps are:

1. Initialize an array of zeros with length equal to the number of demes.
2. Set the ancestry proportion of the destination deme to 1.
3. For each pulse:
   a. Multiply the array by one (1) minus the sum of proportions.
   b. For each source, add its proportion to the array.

For the above model, the steps are:

```
1. x = [0, 0, 0]
2. x = [0, 0, 1]
3. p = 1 - 0.25
   x = x*p = [0, 0, 0.75]
   x[A] += 0.25, x = [0.25, 0, 0.75]
   p = 1 - 0.2
   x = x*p = [0.2, 0, 0.6]
   x[B] += 0.2, x = [0.2, 0.2, 0.6]
```

Thus, our final ancestry proportions for deme `C` after time 10 are `[0.2, 0.2, 0.6]`.

#### Important considerations

* The final ancestry proportions depend on the order of the pulses in the model!
  If we reverse the above model such that:

  ```yaml
  pulses:
  - sources: [B]
    dest: C
    proportions: [0.2]
    time: 10
  - sources: [A]
    dest: C
    proportions: [0.25]
    time: 10
  ```

  We get `[0.25, 0.15, 0.6]` as our ancestry proportions due to pulses.

  The fact that the outcome of applying sequential pulses depends on
  the order is why `demes-python` emits a warning when resolving such models.

* Given the procedure used to apply sequential pulses at the same time,
  the followng two sets of `Pulses` are not equivalent:

  ```yaml
  pulses:
  - sources: [A]
    dest: C
    proportions: [0.2]
    time: 10
  - sources: [B]
    dest: C
    proportions: [0.2]
    time: 10
  ```

  ```yaml
  pulses:
  - sources: [B, A]
    dest: C
    proportions: [0.2, 0.2]
    time: 10
  ```

* Therefore, we strongly recommend that models be represented using the following
  syntax that makes the intended outcome of the model explicit:

  ```yaml
  pulses:
  - sources: [A, B]
    dest: C
    proportions: [0.2, 0.2]
    time: 10
  ```

(sec_spec_mdm_migration)=

### Migration

Continuous asymmetric migration over the half-open time interval
``(start_time, end_time]``, from the deme with name ``source`` to the
deme with name ``dest``.
Rates are defined as the probability that parents in the "destination"
population are chosen from the "source" population.  Migration rates are thus
per generation and must be less than or equal to one.
There must be at most one migration specified per source/destination pair
for any given time interval.
Furthermore, if more than one source
population have continuous migration into the same destination population, the
sum of those migration rates must also be less than or equal to one, as rates define
probabilities. The probability that parents come from the same population is
just one minus the sum of incoming migration rates.

:::{warning}
When continuous migration occurs over a time period that includes a pulse,
the continuous migration probabilities define the probability of choosing
parents from each deme conditional on individuals not arriving via the pulse.
:::


#### source
The deme name of the asymmetric migration source.

#### dest
The deme name of the asymmetric migration destination.

#### start_time
The time at which migration begins,
in {ref}`sec_spec_mdm_time_units` before the present.
The ``start_time`` must be contained in the
``[deme.start_time, deme.end_time)`` interval of the ``source`` deme
and the ``dest`` deme.

#### end_time
The time at which migration stops,
in {ref}`sec_spec_mdm_time_units` before the present.
The ``end_time`` must be contained in the
``(deme.start_time, deme.end_time]`` interval of the ``source`` deme
and the ``dest`` deme.

#### rate
The rate of migration per generation.

(sec_spec_mdm_schema)=

### Schema

The schema listed here is definitive in terms of types and the
structure of the JSON documents that are considered to be
valid instances of the MDM

```{eval-rst}
.. literalinclude:: ../schema/mdm-v1.0.yaml
    :language: yaml
```

(sec_spec_hdm)=
## Human Data Model

The Demes Human Data Model (HDM) is an extension of the {ref}`sec_spec_mdm`
that is designed for human readability. The HDM provides default values
for many parameters, removes redundant information in the MDM via rules described
in this section and also provides a default value replacement mechanism.
JSON documents conforming to the HDM are intended to be processed by a parser,
which outputs the corresponding MDM document.

This section defines the structure of HDM documents, the rules by
which they are transformed into MDM documents, and the error conditions
that should be detected by parsers.

We also provide a {ref}`reference implementation<sec_spec_reference_implementation>`
of a parser
for the HDM (which also parses the MDM, by definition) written in Python.
This implementation
is intended to clarify any ambiguities there may be in this specification,
but is not intended to be used directly in downstream software. Please
use the {external+demes:doc}`demes<introduction>` Python library instead.



(sec_spec_hdm_defaults)=
### Defaults

Repeated values such as shared population sizes represent a significant opportunity
for error in human-generated models. The HDM provides the default value
propagation mechanism to avoid this repetition. The essential idea is that
we declare default values hierarchically within the document, and that
the ultimate value assigned to a property is prioritised by proximity
within the document hierarchy.

Default values can be provided in two places within a HDM document:
at the top-level or within a deme definition.

:::{seealso}
See the {ref}`tutorial<sec_tutorial_defaults>`
for examples of how the defaults section can be used.
:::

:::{seealso}
See the {ref}`reference implementation<sec_spec_reference_implementation>`
for a practical example of how defaults in the HDM can be implemented.
:::

(sec_spec_hdm_defaults_top_level)=
#### Top-level defaults

The top-level HDM document may contain a propery ``defaults``,
which defines values to use for entities within rest of the document
*unless otherwise specified*. The ``defaults`` object can have
the following properties:

- epoch: this can specify any property valid for an
  {ref}`MDM epoch<sec_spec_mdm_epoch>`. All epochs in the
  document will be assigned these properties, unless specified
  within the epoch or the {ref}`deme defaults<sec_spec_hdm_defaults_deme>`.

- migration: this can specify any property valid for an
  {ref}`MDM migration<sec_spec_mdm_migration>`. All migrations in the
  document will be assigned these properties, unless specified
  within the migration itself.

- pulse: this can specify any property valid for an
  {ref}`MDM pulse<sec_spec_mdm_pulse>`. All pulses in the
  document will be assigned these properties, unless specified
  within the pulse itself.

- deme: this can specify the following properties for a
  {ref}`deme<sec_spec_mdm_deme>` only: ``description``,
  ``ancestors``, ``proportions`` and ``start_time``.

:::{seealso}
See the {ref}`schema<sec_spec_hdm_schema>`
for definitive information on the structural properties of the
top level ``defaults`` section.
:::

(sec_spec_hdm_defaults_deme)=
#### Deme defaults

Deme defaults operate in the same manner as
{ref}`top-level defaults<sec_spec_hdm_defaults_top_level>`: the specified
values will be used if omitted in any epochs within the deme. Defaults
specified within a deme override any values specified in the
{ref}`top level<sec_spec_hdm_defaults_top_level>` ``deme`` defaults.


This can specify any property valid for an
{ref}`MDM epoch<sec_spec_mdm_epoch>`. Any epochs in the
deme will be assigned these properties, unless specified
within an epoch itself.


:::{seealso}
See the {ref}`schema<sec_spec_hdm_schema>`
for definitive information on the structural properties of the
deme ``defaults`` section.
:::

(sec_spec_hdm_resolution)=
### Resolution

The Demes {ref}`machine data model<sec_spec_mdm>` contains many
values that are technically redundant, in that they can be reliably
inferred from other values in the model. For example, if a deme's
``size_function`` is ``"constant"`` during an {ref}`sec_spec_mdm_epoch`,
then clearly the ``start_size`` and ``end_size`` will be equal.
The MDM still requires that both be specified, because it is intended
for *machine* consumption, and having a fully specified and complete
data model allows code that consumes this model to be simple and
straightforward. However, such redundancy is a significant
downside for *human* consumption, where having repeated
or redundant values leads to poorer readability and increases
the probability of errors.
Thus, one of the differences
between the Demes {ref}`sec_spec_hdm` and {ref}`sec_spec_mdm`
is that the HDM tries to remove as much redundancy as possible.
A major part of a Demes parser implementation's task is to
fill in the redundant information, a process that we refer to
as model "resolution".
Please consult the
{ref}`reference implementation<sec_spec_reference_implementation>`
for more detailed information.

Resolution is idempotent; that is, resolution of an already
resolved model (i.e., in MDM form) MUST result in identical output.
Thus a parser need not know if a model is in HDM or MDM form a priori.

Resolution happens in a set of steps in a defined order:
- {ref}`time_units <sec_spec_hdm_resolution_time_units>`
- {ref}`generation_time <sec_spec_hdm_resolution_generation_time>`
- {ref}`metadata <sec_spec_hdm_resolution_metadata>`
- {ref}`description <sec_spec_hdm_resolution_description>`
- {ref}`doi <sec_spec_hdm_resolution_doi>`
- {ref}`defaults <sec_spec_hdm_resolution_defaults>`
- {ref}`demes <sec_spec_hdm_resolution_deme>`
- {ref}`migrations <sec_spec_hdm_resolution_migration>`
- {ref}`pulses <sec_spec_hdm_resolution_pulse>`

:::{todo}
Resolution order matters for some things, but not for others.
Clarify where order matters (and why).
:::

(sec_spec_hdm_resolution_time_units)=
#### time_units
``time_units`` must be specified. The value "generations" is special,
in that it implies that the ``generation_time`` will be 1 and may thus be omitted.

(sec_spec_hdm_resolution_generation_time)=
#### generation_time
If ``time_units`` is not "generations", then ``generation_time``
MUST be specified.

If ``time_units`` is "generations", then
- ``generation_time`` may be omitted, in which case it
  shall be given the value 1.
- an error shall be raised if ``generation_time`` is not 1.

(sec_spec_hdm_resolution_metadata)=
#### metadata

If ``metadata`` is omitted, it shall be given the value of an
empty dictionary.
If ``metadata`` is present, the value must be a dictionary,
but metadata is otherwise transferred to the output
without further processing. Errors may be raised if metadata is not
parsable (e.g. invalid YAML), but the parser shall not attempt
to validate fields within the metdata.

(sec_spec_hdm_resolution_description)=
#### description
If ``description`` is omitted, it shall be given the value of an empty string.

(sec_spec_hdm_resolution_doi)=
#### doi
If ``doi`` is omitted, it shall be given the value of an empty list.

(sec_spec_hdm_resolution_defaults)=
#### defaults
If top-level ``defaults`` is provided, default values shall be validated
to the extent possible, to avoid propagating invalid values.
E.g. ``defaults.epoch.start_size`` cannot be negative.

(sec_spec_hdm_resolution_deme)=
#### Deme resolution

Each deme is resolved in the order that
it occurs in the input. A deme can only be resolved if its
ancestor demes have already been resolved,
and the parser MUST raise an error if a deme is encountered that
has unresolved ancestors. Thus, valid input files
list the demes in topologically sorted order, such that
ancestors are listed before their descendants.

Resolution order:
- {ref}`defaults <sec_spec_hdm_resolution_deme_defaults>`
- {ref}`description <sec_spec_hdm_resolution_deme_description>`
- {ref}`ancestors <sec_spec_hdm_resolution_deme_ancestors>`
- {ref}`proportions <sec_spec_hdm_resolution_deme_proportions>`
- {ref}`start_time <sec_spec_hdm_resolution_deme_start_time>`
- {ref}`epochs <sec_spec_hdm_resolution_epoch>`

(sec_spec_hdm_resolution_deme_defaults)=
##### defaults
If deme-level ``defaults`` is provided, default values shall be validated
to the extent possible, to avoid propagating invalid values.
E.g. ``defaults.epoch.start_size`` cannot be negative.

For each deme, deme-level ``defaults`` override top-level defaults.

(sec_spec_hdm_resolution_deme_description)=
##### description

If ``description`` is omitted,
- If the ``deme.description`` defaults field is present, ``description``
  shall be given this value.
- Otherwise, ``description`` shall be given the value of the empty string.

(sec_spec_hdm_resolution_deme_ancestors)=
##### ancestors

If ``ancestors`` is omitted,
- If the ``deme.ancestors`` defaults field is present, ``ancestors``
  shall be given this value.
- Otherwise, ``ancestors`` shall be given the value of the empty list.

(sec_spec_hdm_resolution_deme_proportions)=
##### proportions

If ``proportions`` is omitted,
- If the ``deme.proportions`` defaults field is present, ``proportions``
  shall be given this value.
- Otherwise, if ``ancestors`` has length one, ``proportions`` shall be
  a single-element list containing the element ``1.0``.
- Otherwise, if ``ancestors`` has length zero,
  ``proportions`` shall be given the value of the empty list.
- Otherwise, ``proportions`` cannot be determined and an error
  MUST be raised.

(sec_spec_hdm_resolution_deme_start_time)=
##### start_time

If ``start_time`` is omitted,
- If the ``epoch.start_time`` defaults field is present, ``start_time``
  shall be given this value.
- Otherwise, if ``ancestors`` has length one and the ancestor has an
  ``end_time > 0``, the ancestor's ``end_time`` value shall be used.
- Otherwise, if ``ancestors`` has length zero, ``start_time`` shall be
  given the value ``infinity``.
- Otherwise, ``start_time`` cannot be determined and an
  error MUST be raised.

(sec_spec_hdm_resolution_epoch)=
##### Epoch resolution

Epochs are listed in time-descending order (from oldest to youngest),
and population sizes are inherited from older epochs.
Resolution order:
 - {ref}`end_time <sec_spec_hdm_resolution_epoch_end_time>`
 - {ref}`start_size, end_size <sec_spec_hdm_resolution_epoch_size>`
 - {ref}`size_function <sec_spec_hdm_resolution_epoch_size_function>`
 - {ref}`selfing_rate <sec_spec_hdm_resolution_epoch_selfing_rate>`
 - {ref}`cloning_rate <sec_spec_hdm_resolution_epoch_cloning_rate>`

If a deme's ``epochs`` field is omitted, it will be given the value of
a single-element list, where the list element has the value of an epoch with
all fields omitted. This may produce a valid epoch during subsequent resolution,
e.g. if the ``epoch.start_size`` defaults field has a value.

(sec_spec_hdm_resolution_epoch_end_time)=
###### end_time

If ``end_time`` is omitted,
- If the ``epoch.end_time`` defaults field is present, ``end_time``
  shall be given this value.
- Otherwise, if this is the last epoch, ``end_time`` shall be
  given the value ``0``.
- Otherwise, ``end_time`` cannot be determined and an error MUST
  be raised.

The ``end_time`` value of the first epoch MUST be strictly
smaller than the deme's `start_time`.
The ``end_time`` values of successive epochs MUST be strictly decreasing.

(sec_spec_hdm_resolution_epoch_size)=
###### start_size, end_size

:::{note}
Sizes are never inherited from ancestors.
:::

If ``start_size`` is omitted and the ``epoch.start_size`` defaults field
is present, then the epoch's ``start_size`` shall be given this value.
If ``end_size`` is omitted and the ``epoch.end_size`` defaults field
is present, then the epoch's ``end_size`` shall be given this value.

In the first epoch,
- at least one of ``start_size`` or ``end_size``
  MUST be specified (possibly via a defaults field).
- If ``start_size`` is omitted (and no default exists),
  it shall be given the same value as ``end_size``.
- If ``end_size`` is omitted (and no default exists),
  it shall be given the same value as ``start_size``.
- If the deme's ``start_time`` is infinite, ``start_size``
  MUST have the same value as ``end_size``.

In subsequent epochs,
- If ``start_size`` is omitted (and no defaults exist),
  it shall be given the same value as the previous epoch's ``end_size``.
- If ``end_size`` is omitted (and no defaults exist),
  it shall be given the same value as ``start_size``.

(sec_spec_hdm_resolution_epoch_size_function)=
###### size_function

If ``size_function`` is omitted,
- if the ``epoch.size_function`` defaults field is present,
  ``size_function`` shall be given this value.
- Otherwise, if ``start_size`` has the same value as ``end_size``,
  ``size_function`` will be given the value ``"constant"``.
- Otherwise, ``size_function`` will be given the value ``"exponential"``.

(sec_spec_hdm_resolution_epoch_selfing_rate)=
###### selfing_rate

If ``selfing_rate`` is omitted,
- if the ``epoch.selfing_rate`` defaults field is present,
  ``selfing_rate`` shall be given this value.
- Otherwise, ``selfing_rate`` shall be given the value ``0``.

(sec_spec_hdm_resolution_epoch_cloning_rate)=
###### cloning_rate

If ``cloning_rate`` is omitted,
- if the ``epoch.cloning_rate`` defaults field is present,
  ``cloning_rate`` shall be given this value.
- Otherwise, ``cloning_rate`` shall be given the value ``0``.

(sec_spec_hdm_resolution_migration)=
#### Migration resolution

Migrations must be resolved after all demes are resolved.
Asymmetric migration can be specified using the ``source``
and ``dest`` properties, or symmetric migration can be
specified using the ``demes`` property to list the names
of the participating demes. Each symmetric migration is resolved
into two asymmetric migrations (one in each direction) for each
pair of participating demes.

Resolution order:
- {ref}`rate <sec_spec_hdm_resolution_migration_rate>`
- {ref}`source <sec_spec_hdm_resolution_migration_source>`
- {ref}`dest <sec_spec_hdm_resolution_migration_dest>`
- {ref}`demes <sec_spec_hdm_resolution_migration_demes>`
- {ref}`Symmetric migration <sec_spec_hdm_resolution_migration_symmetric>`
- {ref}`start_time <sec_spec_hdm_resolution_migration_start_time>`
- {ref}`end_time <sec_spec_hdm_resolution_migration_end_time>`

(sec_spec_hdm_resolution_migration_rate)=
##### rate

If the ``rate`` is omitted,
- if the ``migration.rate`` defaults field is present,
  ``rate`` shall be given this value.
- Otherwise, an error MUST be raised.

(sec_spec_hdm_resolution_migration_source)=
##### source

If ``source`` is omitted and the ``migration.source`` defaults field is present,
``source`` shall be given this value.

(sec_spec_hdm_resolution_migration_dest)=
##### dest

If ``dest`` is omitted and the ``migration.dest`` defaults field is present,
``dest`` shall be given this value.

(sec_spec_hdm_resolution_migration_demes)=
##### demes

If ``demes`` is omitted and the ``migration.demes`` defaults field is present,
``demes`` shall be given this value.

(sec_spec_hdm_resolution_migration_symmetric)=
##### Symmetric migration

The following rules shall determine the mode of migration
(either asymmetric or symmetric):
- If ``demes`` does not have a value, and both ``source`` and ``dest`` have values,
  the migration is asymmetric.
  Resolution continues from {ref}`sec_spec_hdm_resolution_migration_start_time`.
- If ``demes`` has a value, and neither ``source`` nor ``dest`` have values,
  the migration is symmetric.
- Otherwise, the mode of migration cannot be determined,
  and an error MUST be raised.

If the migration is symmetric, ``demes`` MUST be validated
before further resolution:
- ``demes`` MUST be a list of at least two deme names.
- Each element of ``demes`` must be unique.
- Each element of ``demes`` must be the name of a resolved deme.

If any of the previous conditions are not met, an error MUST be raised.

If the migration is symmetric, two new asymmetric migrations shall be
constructed for each pair of deme names in ``demes``.
E.g. if ``demes = ["a", "b", "c"]``, then asymmetric migrations shall
be constructed for the following cases:
- ``source="a"``, ``dest="b"``,
- ``source="b"``, ``dest="a"``,
- ``source="a"``, ``dest="c"``,
- ``source="c"``, ``dest="a"``,
- ``source="b"``, ``dest="c"``,
- ``source="c"``, ``dest="b"``.

Values for ``rate``, ``start_time``, and ``end_time`` for the new asymmetric
migrations shall be taken from the symmetric migration.
If ``start_time`` and/or ``end_time`` are omitted from the symmetric
migration, these shall also be omitted for the new asymmetric migrations.
Resolution now proceeds separately for each distinct asymmetric migration.

:::{note}
The symmetric migration shall not appear in the MDM output.
Once the symmetric migration has been resolved into the corresponding
asymmetric migrations, the symmetric migration may be discarded.
:::

(sec_spec_hdm_resolution_migration_start_time)=
##### start_time

If ``start_time`` is omitted,
- If the ``migration.start_time`` defaults field has a value,
  ``start_time`` shall be given this value.
- Otherwise, ``start_time`` shall be the oldest time at which
  both the ``source`` and ``dest`` demes exist.
  I.e. ``min(source.start_time, dest.start_time)``.

(sec_spec_hdm_resolution_migration_end_time)=
##### end_time

If ``end_time`` is omitted,
- If the ``migration.end_time`` defaults field has a value,
  ``end_time`` shall be given this value.
- Otherwise, ``end_time`` shall be the most recent time at which
  both the ``source`` and ``dest`` demes exist.
  I.e. ``max(source.end_time, dest.end_time)``.

(sec_spec_hdm_resolution_pulse)=
#### Pulse resolution

Pulses must be resolved after all demes are resolved.

Resolution order:
- {ref}`sources <sec_spec_hdm_resolution_pulse_sources>`
- {ref}`proportions <sec_spec_hdm_resolution_pulse_proportions>`
- {ref}`dest <sec_spec_hdm_resolution_pulse_dest>`
- {ref}`time <sec_spec_hdm_resolution_pulse_time>`
- {ref}`Sort pulses <sec_spec_hdm_resolution_pulse_sort>`

(sec_spec_hdm_resolution_pulse_sources)=
##### sources

If ``sources`` is omitted,
- if the ``pulse.sources`` defaults field has a value,
  ``sources`` shall be given this value.
- Otherwise, an error MUST be raised.

(sec_spec_hdm_resolution_pulse_proportions)=
##### proportions

If ``proportions`` is omitted,
- if the ``pulse.proportions`` defaults field has a value,
  ``proportions`` shall be given this value.
- Otherwise, an error MUST be raised.

(sec_spec_hdm_resolution_pulse_dest)=
##### dest

If ``dest`` is omitted,
- if the ``pulse.dest`` defaults field has a value,
  ``dest`` shall be given this value.
- Otherwise, an error MUST be raised.

(sec_spec_hdm_resolution_pulse_time)=
##### time

If ``time`` is omitted,
- if the ``pulse.time`` defaults field has a value,
  ``time`` shall be given this value.
- Otherwise, an error MUST be raised.

(sec_spec_hdm_resolution_pulse_sort)=
##### Sort pulses

Pulses MUST be sorted in time-descending order (from oldest to youngest).
A [stable](https://en.wikipedia.org/wiki/Sorting_algorithm#Stability)
sorting algorithm MUST be used to avoid changing the model interpretation
when multiple pulses are specified with the same ``time`` value.

:::{note}
In a discrete-time setting, non-integer pulse times that are distinct
could be rounded to the same time value. If pulses are in time-ascending
order when times are rounded, then the pulses would be applied
in the opposite order compared to a continuous-time setting.
Sorting in time-descending order avoids this discrepancy.
:::

(sec_spec_hdm_validation)=
### Validation

:::{note}
It may be convenient to perform some or all validation during model resolution.
E.g. to avoid code duplication, or to provide better error messages to the user.
:::

Following resolution, the model must be validated against the MDM schema.
This includes checking:
- all required properties now have values,
- no additional properties are present (except where permitted by the schema),
- the types of properties match the schema,
- the values are within the ranges specified
  (noting that infinity is permitted only for deme `start_time`
  and for migration `start_time`).

In addition to validation against the schema, the following constraints
must be checked to ensure overall consistency of the model.
If any condition is not met, an error must be raised.

#### generation_time

If `time_units` is "generations", then `generation_time` must be 1.

#### demes

- There must be at least one deme.
- Each deme's `name` must be unique in the model.
- `name` must be a valid Python identifier.
- If `start_time` is infinity, `ancestors` must be an empty list.
- If `ancestors` is an empty list, `start_time` must have the value infinity.
- No deme may appear in its own `ancestors` list.
- Each element of the `ancestors` list must be unique.
- The `proportions` list must have the same length as the `ancestors` list.
- If the `proportions` list is not empty, then the values must sum to 1
  (within a reasonable tolerance, e.g. 1e-9).

##### epochs

- Each deme must have at least one epoch.
- The `end_time` values of successive epochs must be strictly descending
  (ordered from the past towards the present).
- The `end_time` values must be strictly smaller than the deme's `start_time`.
- If the deme has an infinite `start_time`, the first epoch's `size_function`
  must have the value "constant".
- If the `size_function` is "constant", the `start_size` and `end_size`
  must be equal.

#### migrations

This section assumes that symmetric migrations have been resolved into
pairs of asymmetric migrations and validated as per the
{ref}`migration resolution <sec_spec_hdm_resolution_migration>`
section. Resolution of symmetric migrations includes
validation of the ``migration.demes`` property, and this property
is not considered below as it is not part of the MDM.

- `source` must not be the same as `dest`.
- `start_time` and `end_time` must both be in the closed interval
   `[deme.start_time, deme.end_time]`, for both the `source` deme
   and the `dest` deme.
- `start_time` must be strictly greater than `end_time`.
- There must be at most one migration specified per source/destination pair
  for any given time interval.
- If more than one source population have continuous migration into the same
  destination population, the sum of those migration rates must also be less
  than or equal to 1
  (within a reasonable tolerance, e.g. 1e-9).

#### pulses

- `sources` must be list containing at least one element.
- Each element of `sources` must be unique.
- The `dest` deme must not appear in the `sources` list.
- For each source deme in `sources`,
  `time` must be in the open-closed interval `(deme.start_time, deme.end_time]`,
  defined by the existence interval of the source deme.
- `time` must be in the closed-open interval `[deme.start_time, deme.end_time)`,
  defined by the existence interval of the `dest` deme.
- Hence, `time` must not have the value infinity, nor the value 0.
- The `proportions` list must have the same length as the `sources` list.
- The sum of values in the `proportions` list must be less than or equal to 1
  (within a reasonable tolerance, e.g. 1e-9).

(sec_spec_hdm_schema)=

### Schema

The schema listed here is definitive in terms of types and the
structure of the JSON documents that are considered to be
valid instances of the Demes standard.

```{eval-rst}
.. literalinclude:: ../schema/hdm-v1.0.yaml
    :language: yaml
```


(sec_spec_reference_implementation)=

## Reference parser implementation

```{eval-rst}
.. literalinclude:: ../reference_implementation/demes_parser.py
    :language: python
```

(sec_appendix)=

## Appendix

(sec_appendix_backwards_to_forwards)=

### Converting backwards time to forwards time

Times in Demes models use a backwards-time convention, where the value `0` represents
now and time values increase towards the past.
However, many simulators use the opposite convention, where time `0` represents
some time in the past and time values increase towards the present.

To convert times in a Demes model into a forward-time representation:

* Set `y` equal to the minimum epoch end time in the resolved graph.
* Set `x` equal to the most ancient, finite, value out of epoch `start_time`,
  epoch `end_time`, migration `start_time`, or pulse `time`.
* The model duration is `d = x - y`;
* Using the convention of starting a forward-in-time model at time zero (
  representing the parental generation at the beginning of a model), the model
  runs forward in time from `(0, d]`.
* For explicit simulations involving a "burn in time", the previous interval is shifted by that length.
  The duration of the burn-in period is `(0, b]`
  and the events in the Demes graph occur from `(b, b + d]`.
* Given these definitions, `f = b + d - t`, where `t` is a backwards time in the Demes model and `f` is the forwards-time equivalent.
