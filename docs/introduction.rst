============
Introduction
============

What is the Demes Specification?
--------------------------------

The Demes Specification is a concrete proposal to standardise:

 - :ref:`how computational biologists write down demographic models <sec_tutorial>`, and
 - :ref:`how those models should be interpreted by software <sec_spec>`.


Why is it necessary?
--------------------

It can be tedious and error prone to write down a demographic model for
use with population genetics software, such as simulators. Moreover,
genetics software use many different and often incompatible input formats
for describing demographic models. So a user may be forced to rewrite
the model in order to use it with another tool.

Publications often report demographic models as a table of parameters,
which needs to be transcribed by the reader. Even when publications provide
commands, or code, that correspond to their concrete demographic model,
this is unfortunately tied to specific software.

We believe these problems are fixable.
