"""
Test that all the examples are valid instances of the schema.

Run with ``python3 -m pytest ``
"""
import pathlib
import functools

import pytest
import jsonschema
from ruamel.yaml import YAML
import hypothesis
import hypothesis_jsonschema


@functools.lru_cache(maxsize=None)
def load_yaml(filename):
    with open(filename) as f:
        with YAML(typ="safe") as yaml:
            data = yaml.load(f)
    return data


def validate(yaml_path):
    schema = load_yaml("demes-specification.yaml")
    data = load_yaml(yaml_path)
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.parametrize(
    "yaml_path", map(str, pathlib.Path("examples/").glob("**/*.yaml"))
)
def test_examples(yaml_path):
    validate(yaml_path)


@pytest.mark.parametrize(
    "yaml_path", map(str, pathlib.Path("test-cases/valid").glob("**/*.yaml"))
)
def test_test_cases_valid(yaml_path):
    validate(yaml_path)


# Check that the MDM schema is a subschema of the HDM schema by generating
# random data matching the MDM schema and validating against the HDM schema.
@hypothesis.given(
    mdm_data=hypothesis_jsonschema.from_schema(
        load_yaml("demes-fully-qualified-specification.yaml")
    )
)
def test_subschema(mdm_data):
    hdm_schema = load_yaml("demes-specification.yaml")
    jsonschema.validate(instance=mdm_data, schema=hdm_schema)
