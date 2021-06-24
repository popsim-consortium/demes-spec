(sec_spec)=

# Specification


## Introduction

Demes is a specification for describing population genetic models
of demographic history. This specification precisely defines the
population genetics model and its assumptions, along with
the data model used for interchange and the required behaviour
of implementations.

:::{admonition}Who is this specification for?
This specification is intended to provide a detailed and definitive resource
for the following groups:

- Those implementing support for Demes as an input or output format in their programs
- Those implementing a Demes parser

As such, this specification contains a lot of detail that is not
interesting to most users.
If your wish to learn how to understand and create your own
Demes models, please see the {ref}`sec_tutorial` instead.
:::

## Note to Readers

To provide feedback on this specification, please use the
[issue tracker](https://github.com/popsim-consortium/demes-spec/issues).


(sec_spec_terminology)=

## Conventions and Terminology

The term "Demes" in this document is to be interpreted as a
reference to this specification. A {ref}`sec_spec_popgen_deme`
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


(sec_spec_popgen)=
## Population genetics model

In this section we define the underlying population genetics assumptions
made in Demes and the key concepts involved.
The goal is to provide a basic shared vocabulary that
is precise enough to make interchange of models defined in the standard
meaningful, but to avoid being overly proscriptive so that the
format is flexible enough to encompass a wide range of different methods.
Issues relating to the data model and interchange and dealt with
in later sections.

(sec_spec_popgen_deme)=

### Deme

A "deme" is collection of individuals whose dynamics can be described
by a fixed set of parameters. As explained in the {ref}`sec_spec_terminology`
section, we will usually the term "population" to refer to a deme
to avoid confusion.

:::{todo}
Define the model! What are the dynamics? Include definition of selfing and
cloning.  https://github.com/popsim-consortium/demes-spec/issues/43
:::

(sec_spec_popgen_time)=
### Time

Time is measured forwards, and in units of time-ago. Can be either
in years or generations. Can either discrete or continuous.

:::{todo}
Refine: https://github.com/popsim-consortium/demes-spec/issues/60
:::

(sec_spec_popgen_population_size)=

### Population size

:::{todo}
Refine: https://github.com/popsim-consortium/demes-spec/issues/72
:::

(sec_spec_popgen_population_epoch)=
### Epoch

An interval of time over which the parameters describing the dynamics of a
given {ref}`population<sec_spec_popgen_deme>` are fixed.

(sec_spec_popgen_population_migration)=
### Migration

:::{todo}
Define assumptions about migration.
:::

(sec_spec_mdm)=
## Machine Data Model

:::{warning}
The structure of the documentation here is still in flux - it's not clear
how to split things up in terms of explaining what something is, and
also what the formal restrictions on its value are, particularly
in terms of the HDM and MDM split.
:::

The Demes Machine Data Model (MDM) is a formal representation of the
{ref}`sec_spec_popgen` as a JSON document. The HDM is designed to be
used as input by programs such as population genetics simulators,
and explicitly includes all necessary details. The structure of JSON
documents conforming to the specification is formally defined
in the {ref}`sec_spec_mdm_schema`, and the detailed requirements for each of the
elements in this data model are defined in this section.

(sec_spec_defs_common)=

### Common concepts

This section provides details on properties that occur in multiple
contexts.

start_time
: The oldest time of a time interval (numerical upper bound).

end_time
: The youngest time of a time interval (numerical lower bound).

### MDM documents

The top-level MDM document describes a single instance of a Demes model.
Please see the {ref}`sec_spec_popgen` section for details about the
population genetics assumptions underlying these model descriptions.

Each MDM document contains the following list of properties. All
properties MUST be specified, and additional properties MUST NOT be
included in these documents. Please see the {ref}`sec_spec_mdm_schema`
for definitive details on the types and structure of these properties.

description
: A concise description of the demographic model.

doi
: The DOI(s) of the publication(s) in which the model was inferred or
  originally described.

time_units
: The units of time used to specify times and time intervals. These
  SHOULD be one of "generations" or "years".

generation_time
: The number by which times must be divided, to convert them to have
  units of generations. Unless ``time_units`` are ``generations``,
  the ``generation_time`` MUST be specified.

demes
: The list of demes in the model. At least one deme MUST be specified.
  Please see the section {ref}`below <sec_spec_mdm_deme>` for the
  required properties of these objects.

pulses
: The list of pulses in the model.
  Please see the section {ref}`below <sec_spec_mdm_pulse>` for the
  required properties of these objects.

migrations
: The list of migrations in the model.
  Please see the section {ref}`below <sec_spec_mdm_migration>` for the
  required properties of these objects.

(sec_spec_mdm_deme)=

### Deme

The deme may be a descendant of one or more demes in the graph, and may
be an ancestor to others. The deme exists over the half-open time interval
``(start_time, end_time]``, and it may continue to exist after
contributing ancestry to a descendant deme. The deme's ``end_time`` is
defined as the ``end_time`` of the deme's last epoch.

name
: A string identifier for a deme, which MUST be unique among all demes in a document.
  Must be a valid
  [python identifier](https://docs.python.org/3/reference/lexical_analysis.html#identifiers)

description
: A concise description of the deme.

ancestors
: The ancestors of the deme at the start of the deme's first epoch.
  May be omitted if the deme has no ancestors in the graph.
  If two or more ancestors are specified, the ``proportions``
  must also be specified, and the ``start_time`` must be defined
  (either specified directly, or indirectly in the deme's first epoch).
  Each ancestor must be in the graph, and each ancestor must be
  specified only once. A deme must not be one of its own ancestors.

proportions
: The proportions of ancestry derived from each of the ``ancestors``
  at the start of the deme's first epoch.
  The ``proportions`` may be omitted if there are no ancestors, or if
  there is only one ancestor.
  The ``proportions`` must be ordered to correspond with the
  order of ``ancestors``. The proportions must sum to 1 (within a
  reasonable tolerance, e.g. 1e-9).

start_time
: The most ancient time at which the deme exists, in ``time_units``
  before the present. Demes with no ancestors are root demes and must
  have an infinite ``start_time``. Otherwise, the ``start_time`` must
  correspond with the interval of existence
  for each of the deme's ``ancestors``. I.e. the ``start_time`` must
  be within the half-open interval ``(deme.start_time, deme.end_time]``
  for each deme in ``ancestors``.


epochs
: The list of epochs for this deme. There MUST be at least one epoch.
  Please see the section {ref}`below <sec_spec_mdm_epoch>` for details.

(sec_spec_mdm_epoch)=

### Epoch

A deme-specific period of time spanning the half-open interval
``(start_time, end_time]``, in which a fixed set of population parameters
apply. The epoch's ``start_time`` is defined as the ``end_time`` of the
previous epoch, or the deme's ``start_time`` if it is the first epoch.

end_time
: The most recent time of the epoch, in ``time_units`` before the present.

start_size
: The population size at the epoch's ``start_time``.

end_size
: The population size at the epoch's ``end_time``.

size_function
: A function describing the population size change between
  ``start_time`` and ``end_time``. FIXME, MORE DETAIL.

cloning_rate
: DEFINE ME

selfing_rate
: DEFINE ME


(sec_spec_mdm_pulse)=

### Pulse

An instantaneous pulse of migration at ``time``, from the ``source`` deme
into the ``dest`` deme.

source
: The deme ID of the migration source.

dest
: The deme ID of the migration destination.

time
: The time of migration, in ``time_units`` before the present.
  The ``source`` and ``dest`` demes must both exist at the given
  ``time``.  I.e. ``time`` must be contained in the
  ``(deme.start_time, deme.end_time]`` interval of the ``source``
  deme and the ``dest`` deme.

proportion
: The proportion of the ``source`` deme's ancestry in the ``dest`` deme
  immediately after the ``time`` of migration.


(sec_spec_mdm_migration)=

### Migration

Continuous migration over the half-open time interval ``(start_time, end_time]``.
If ``demes`` is specified, then migration shall be symmetric between all
pairs of demes with deme IDs in the array. If ``source`` and ``dest`` are
specified instead, migration shall be asymmetric from the deme with ID
``source`` to the deme with ID ``dest``. Either ``demes``, or alternately
both ``source`` and ``dest``, must be specified. If ``demes`` is specified,
neither ``source`` nor ``dest`` may be specified.

demes
: The deme IDs of the symmetrically migrating demes.

source
: The deme ID of the asymmetric migration source.

dest
: The deme ID of the asymmetric migration destination.

start_time
: The time at which migration begins, in ``time_units`` before the present.
  The ``start_time`` must be contained in the
  ``[deme.start_time, deme.end_time)`` interval of the ``source`` deme
  and the ``dest`` deme.
  If not specified, the migration ``start_time`` shall be the minimum
  ``deme.start_time`` of the ``source`` deme and the ``dest`` deme.

end_time
: The time at which migration stops, in ``time_units`` before the present.
  The ``end_time`` must be contained in the
  ``(deme.start_time, deme.end_time]`` interval of the ``source`` deme
  and the ``dest`` deme.
  If not specified, the migration ``end_time`` shall be the maximum
  ``deme.end_time`` of the ``source`` deme and the ``dest`` deme.

rate
: The rate of migration per generation.


(sec_spec_mdm_schema)=

### Schema

The schema listed here is definitive in terms of types and the
structure of the JSON documents that are considered to be
valid instances of the MDM

```{eval-rst}
.. literalinclude:: ../demes-fully-qualified-specification.yaml
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

(sec_spec_hdm_defaults)=
### Defaults

Repeated values such as shared population sizes represent a significant opportunity
for error in human-generated models. The HDM provides the default value
propagation mechanism to avoid this repetition.

:::{todo}
Describe the process of hierarchical default value replacement.
:::


### Resolution

:::{todo}
Tidy this up - just putting text in here for the moment that's
pulled from other parts of the document.
:::

start_time
: The most ancient time at which the deme exists, in ``time_units``
  before the present. Demes with no ancestors are root demes and must
  have an infinite ``start_time``. Otherwise, the ``start_time`` must
  correspond with the interval of existence
  for each of the deme's ``ancestors``. I.e. the ``start_time`` must
  be within the half-open interval ``(deme.start_time, deme.end_time]``
  for each deme in ``ancestors``.

  If not specified, the deme's ``start_time`` shall be obtained
  according to the following rules (the first matching rule shall
  be used).

   - If the deme has one ancestor, and the ancestor has an
     ``end_time > 0``, the ancestor's ``end_time`` value shall be
     used.
   - If the deme has no ancestors, the ``start_time`` shall be
     infinitely far into the past. I.e. the ``start_time`` shall
     have the value ``infinity``.

  If the ``start_time`` has not been defined after following the
  rules above, an error shall be raised. E.g. an error shall be
  raised for the following conditions.

   - If the deme has multiple ancestors,
     and the deme's ``start_time`` is not specified.
   - If the deme has one ancestor with an ``end_time == 0``,
     and the deme's ``start_time`` is not specified.
   - If the deme has zero ancestors and a finite ``start_time``.


(sec_spec_hdm_schema)=

### Schema

The schema listed here is definitive in terms of types and the
structure of the JSON documents that are considered to be
valid instances of the Demes standard.

```{eval-rst}
.. literalinclude:: ../demes-specification.yaml
    :language: yaml
```
