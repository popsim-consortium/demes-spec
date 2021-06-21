(sec_spec)=

# Specification


## Introduction

Demes is a specification for describing population genetic models
of demographic history. This specification precisely defines the
data model and the required behaviour of implementations.


## Note to Readers

To provide feedback on this specification, please use the
[issue tracker](https://github.com/popsim-consortium/demes-spec/issues).


## Conventions and Terminology

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

(sec_spec_defaults)=

## Defaults

We specify defaults to do stuff.

## Definitions

(sec_spec_defs_common)=

### Common concepts

start_time
: The oldest time of a time interval (numerical upper bound).

end_time
: The youngest time of a time interval (numerical lower bound).


(sec_spec_defs_demes_graph)=

### Demes graph

A ``demes`` model is a graph in which each deme is a vertex, and graph edges
indicate ancestor/descendant relationships. Additional relationships between
demes are described using `pulses` for instantaneous migrations, and
`migrations` for continuous migration over a time interval.

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
: The list of {ref}`sec_spec_defs_deme`s. At least one deme MUST
  be specified.

pulses
: The list of instantaneous {ref}`pulses of migration <sec_spec_defs_pulse>`
  between demes.

migrations
: The list of {ref}`migrations <sec_spec_defs_migration>`  occurring
  continuously over a time interval.

defaults
: The default values for omitted properties in Demes. See the
  {ref}`sec_spec_defaults` for details.


(sec_spec_defs_deme)=

### Deme

A collection of individuals that are exchangeable at any fixed time.
The deme may be a descendant of one or more demes in the graph, and may
be an ancestor to others. The deme exists over the half-open time interval
``(start_time, end_time]``, and it may continue to exist after
contributing ancestry to a descendant deme. The deme's ``end_time`` is
defined as the ``end_time`` of the deme's last epoch.


name
: A string identifier for a deme, which MUST be unique
  among all demes in a model.
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

epochs
: The list of {ref}`epochs <sec_spec_defs_epoch>` for this deme.

defaults
: The default values for omitted properties in epochs.


(sec_spec_defs_epoch)=

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


(sec_spec_defs_pulse)=

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


(sec_spec_defs_migration)=

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

## Schema

The schema listed here is definitive in terms of types and the
structure of the JSON documents that are considered to be
valid instances of the Demes standard.

```{eval-rst}
.. literalinclude:: ../demes-specification.yaml
    :language: yaml
```
