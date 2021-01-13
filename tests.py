"""
Test that all the examples are valid instances of the schema.

Run with ``python3 -m pytest ``
"""
import pathlib
import json

import pytest
import jsonschema
from ruamel.yaml import YAML


@pytest.mark.parametrize(
    "yaml_path", map(str, pathlib.Path("examples/").glob("*.yaml"))
)
def test_examples(yaml_path):
    yaml = YAML(typ="safe")
    with open("demes-specification.yaml") as source:
        schema = yaml.load(source)
    with open(yaml_path) as source:
        data = yaml.load(source)
    jsonschema.validate(instance=data, schema=schema)
