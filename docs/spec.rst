.. _sec_spec:

===================
Demes Specification
===================

The structure of ``demes``' data model is formally defined using
`JSON schema <https://json-schema.org/>`_ and rendered below as a table.
A machine readable version of the schema (from which this table was generated)
can be found in the ``demes-specification.yaml`` file of the 
`demes-spec repository <https://github.com/popsim-consortium/demes-spec>`_.

.. note::

 The formal requirements of ``demes``' data model impose inter-property
 constraints that cannot be described using JSON schema alone.
 These additional conditions are described throughout this document
 using the language *must* or *must not*.

For each object defined below, the strictly required properties are indicated
in **bold**, and these properties must be specified by the user.
The remaining properties, which may be omitted by the user, must nevertheless
have defined values. Where default values are obtained from other properties,
this is described in the ``description`` field, using the language *shall*
or *shall not*.

Software implementing this specification is expected to raise errors
when processing input for which the formal requirements are not met.

.. jsonschema:: ../demes-specification.yaml
   :lift_description:
   :lift_definitions:
   :auto_target:
   :auto_reference:


