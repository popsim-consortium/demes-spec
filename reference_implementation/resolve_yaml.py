# Convert a yaml Demes model to a fully qualified json model and write
# to stdout.
import sys
import json
from ruamel.yaml import YAML

import demes_parser as parser


if __name__ == "__main__":

    yaml = YAML(typ="safe")
    with open(sys.argv[1], encoding="utf-8") as source:
        data = yaml.load(source)
    graph = parser.parse(data)
    print(json.dumps(graph.as_json_dict(), indent=2))
