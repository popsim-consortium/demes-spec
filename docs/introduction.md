(sec_intro)=
# Introduction

## What is the Demes specification?

The Demes specification is a concrete proposal to standardise:

 - {ref}`how computational biologists write down demographic models <sec_tutorial>`, and
 - {ref}`how those models should be interpreted by software <sec_spec>`.


## Why is it necessary?

It can be tedious and [error prone](https://doi.org/10.1016/j.ajhg.2020.08.017)
to write down a demographic model for
use with population genetics software, such as simulators. Moreover,
genetics software use many different and often incompatible input formats
for describing demographic models. So a user may be forced to rewrite
the model in order to use it with another tool.

Publications often report demographic models as a table of parameters,
which needs to be transcribed by the reader. Even when publications provide
commands, or code, that correspond to their concrete demographic model,
this is unfortunately tied to specific software.

We believe these problems are fixable.


## Software support

The following software provides support for Demes.
If you'd like to add your software to this list, please open a
[Pull Request](https://github.com/popsim-consortium/demes-spec/edit/main/docs/introduction.md).

### Software directly related to Demes

 - [demes-c](https://github.com/grahamgower/demes-c) -
   A C library for loading Demes models using libyaml.
 - [demes-python](https://github.com/popsim-consortium/demes-python/) -
   A Python library for loading, saving, and working with Demes models.
   Includes an `ms` converter.
 - [demesdraw](https://github.com/grahamgower/demesdraw) -
   A Python library for drawing Demes models (as seen in the
   {ref}`tutorial <sec_tutorial>`).

### Software accepting the Demes format as input/output

 - [fwdpy11](https://github.com/molpopgen/fwdpy11) -
   A Python package for forward-time population genetic simulation.
 - [GADMA](https://github.com/ctlab/GADMA) -
   Genetic Algorithm for Demographic Model Analysis.
   GADMA implements methods for automatic inference of the joint demographic
   history of multiple populations from genetic data.
 - [moments](https://bitbucket.org/simongravel/moments/) -
   Moment-based solution of the diffusion equation in genetics,
   for inference of demographic history and selection.
 - [msprime](https://github.com/tskit-dev/msprime/) -
   A population genetics simulator of ancestry and DNA sequence evolution
   based on tskit.
 - [demes-slim](https://github.com/grahamgower/demes-slim) -
   A SLiM/Eidos library for loading a Demes model into SLiM.
