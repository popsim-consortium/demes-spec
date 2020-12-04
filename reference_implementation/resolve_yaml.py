# Convert a yaml Demes model to a fully qualified json model and write
# to stdout.
import sys
import json
from ruamel.yaml import YAML

import parser


if __name__ == "__main__":

    yaml = YAML(typ="safe")
    with open(sys.argv[1]) as source:
        data = yaml.load(source)
    graph = parser.parse(data)
    print(json.dumps(graph.asdict(), indent=2))
