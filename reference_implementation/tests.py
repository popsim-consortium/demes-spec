"""
Unit tests for the Demes reference parser implementation.

Run with ``python3 -m pytest ``
"""
import pathlib
import json
import math

import pytest
from ruamel.yaml import YAML

import parser


def minimal_graph(num_demes=1, population_size=1):
    graph = {
        "time_units": "generations",
        "demes": [
            {"name": f"deme{j}", "epochs": [{"start_size": population_size}]}
            for j in range(num_demes)
        ],
    }
    return graph


def island_model_graph(num_demes=1, population_size=1, migration_rate=1):
    graph = {
        "time_units": "generations",
        "demes": [
            {"name": f"deme{j}", "epochs": [{"start_size": population_size}]}
            for j in range(num_demes)
        ],
        "migrations": [
            {"rate": migration_rate, "demes": [f"deme{j}" for j in range(num_demes)]}
        ],
    }
    return graph


def single_deme_graph(num_epochs=1, population_size=1):
    graph = {
        "time_units": "generations",
        "demes": [
            {
                "name": "deme0",
                "epochs": [
                    {"start_size": population_size + j, "end_time": num_epochs - j - 1}
                    for j in range(num_epochs)
                ],
            }
        ],
    }
    return graph


def single_ancestor_graph(num_demes=1, population_size=1):
    graph = {
        "time_units": "generations",
        "defaults": {"epoch": {"start_size": population_size}},
        "demes": [{"name": "ancestor", "epochs": [{"end_time": 10}]}]
        + [{"name": f"child_{j}", "ancestors": ["ancestor"]} for j in range(num_demes)],
    }
    return graph


def two_ancestor_graph(num_demes=1, population_size=1):
    graph = {
        "time_units": "generations",
        "defaults": {"epoch": {"start_size": population_size}},
        "demes": [
            {"name": "ancestor0", "epochs": [{"end_time": 10}]},
            {"name": "ancestor1", "epochs": [{"end_time": 10}]},
        ]
        + [
            {
                "name": f"child_{j}",
                "ancestors": ["ancestor0", "ancestor1"],
                "proportions": [0.5, 0.5],
                "start_time": 10,
            }
            for j in range(num_demes)
        ],
    }
    return graph


class TestValidateGraph:
    def test_empty_document(self):
        with pytest.raises(KeyError):
            parser.parse({})

    def test_time_units(self):
        data = minimal_graph()
        data["time_units"] = 12
        with pytest.raises(TypeError):
            parser.parse(data)

    def test_generation_time_generations(self):
        data = minimal_graph()
        data["time_units"] = "generations"
        data["generation_time"] = 12
        parser.parse(data)
        data["generation_time"] = 1
        graph = parser.parse(data)
        assert graph.generation_time == 1

    def test_generation_time(self):
        data = minimal_graph()
        data["time_units"] = "years"
        with pytest.raises(ValueError):
            parser.parse(data)
        data["generation_time"] = "string"
        with pytest.raises(TypeError):
            parser.parse(data)

    def test_doi(self):
        data = minimal_graph()
        data["doi"] = {"x:", "y"}
        with pytest.raises(TypeError):
            parser.parse(data)
        data["doi"] = [2134]
        with pytest.raises(TypeError):
            parser.parse(data)

    def test_description(self):
        data = minimal_graph()
        data["description"] = 1234
        with pytest.raises(TypeError):
            parser.parse(data)


class TestExtraFields:
    def validate(self, data):
        with pytest.raises(ValueError, match="Extra fields"):
            parser.parse(data)

    def test_top_level(self):
        data = minimal_graph()
        data["extra_field"] = 1234
        self.validate(data)

    def test_deme(self):
        data = minimal_graph()
        data["demes"][0]["extra_field"] = 1234
        self.validate(data)

    def test_epoch(self):
        data = single_deme_graph()
        data["demes"][0]["epochs"][0]["extra_field"] = 1234
        self.validate(data)

    def test_migration(self):
        data = island_model_graph(3)
        data["migrations"][0]["extra_field"] = 1234
        self.validate(data)

    def test_pulse(self):
        data = minimal_graph(2)
        data["pulses"] = [
            {
                "source": "deme0",
                "dest": "deme1",
                "time": 1,
                "proportion": 0.5,
                "extra_field": 1234,
            }
        ]
        self.validate(data)

    def test_top_level_defaults(self):
        data = minimal_graph()
        data["defaults"] = {"extra_field": 1234}
        self.validate(data)

    def test_deme_defaults(self):
        data = minimal_graph()
        data["demes"][0]["defaults"] = {"extra_field": 1234}
        self.validate(data)


class TestExtraFieldsDefaults:
    def validate(self, data):
        with pytest.raises(ValueError, match="Only fields"):
            parser.parse(data)

    def test_deme(self):
        data = minimal_graph()
        data["defaults"] = {"deme": {"extra_field": 1234}}
        self.validate(data)

    def test_global_epoch(self):
        data = minimal_graph()
        data["defaults"] = {"epoch": {"extra_field": 1234}}
        self.validate(data)

    def test_migration(self):
        data = island_model_graph()
        data["defaults"] = {"migration": {"extra_field": 1234}}
        self.validate(data)
        # Should also be triggered when we have no migrations.
        data = minimal_graph()
        data["defaults"] = {"migration": {"extra_field": 1234}}
        self.validate(data)

    def test_pulse(self):
        data = minimal_graph()
        data["defaults"] = {"pulse": {"extra_field": 1234}}
        self.validate(data)


class TestValidateDeme:
    def test_id(self):
        data = minimal_graph()
        data["demes"][0]["name"] = 1234
        with pytest.raises(TypeError):
            parser.parse(data)
        data["demes"][0]["name"] = "not an identifier"
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_description(self):
        data = minimal_graph()
        data["demes"][0]["description"] = 1234
        with pytest.raises(TypeError):
            parser.parse(data)

    def test_duplicate_deme_ids(self):
        data = minimal_graph(num_demes=2)
        data["demes"][0]["name"] = data["demes"][1]["name"]
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_self_ancestor(self):
        data = minimal_graph(num_demes=2)
        data["demes"][0]["ancestors"] = ["deme1"]
        # Fails trying to find the deme with current ID.
        with pytest.raises(KeyError):
            parser.parse(data)

    def test_bad_proportions(self):
        data = single_ancestor_graph(1)
        for bad_proportion in [[], [1, 2]]:
            data["demes"][1]["proportions"] = bad_proportion
            with pytest.raises(ValueError, match="same length"):
                parser.parse(data)
        for bad_proportion in [[-1], [0.5], [2]]:
            data["demes"][1]["proportions"] = bad_proportion
            with pytest.raises(ValueError, match="Sum of proportions"):
                parser.parse(data)

    def test_missing_time_two_ancestors(self):
        data = two_ancestor_graph()
        graph = parser.parse(data)
        assert len(graph.demes) == 3
        del data["demes"][2]["start_time"]
        with pytest.raises(ValueError, match="explicitly set Deme.start_time"):
            parser.parse(data)

    def test_missing_proportion_two_ancestors(self):
        data = two_ancestor_graph()
        graph = parser.parse(data)
        assert len(graph.demes) == 3
        del data["demes"][2]["proportions"]
        with pytest.raises(ValueError, match="Must specify proportions"):
            parser.parse(data)

    def test_time_travel(self):
        data = {
            "time_units": "generations",
            "defaults": {"epoch": {"start_size": 1}},
            "demes": [
                {"name": "deme0"},
                {
                    "name": "deme1",
                    "start_time": 100,
                    "ancestors": ["deme0"],
                    "epochs": [{"end_time": 20}],
                },
                {
                    "name": "deme2",
                    "start_time": 150,
                    "ancestors": ["deme1"],
                    "epochs": [{"end_time": 120}],
                },
            ],
        }
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_root_with_finite_start_time(self):
        data = {
            "time_units": "generations",
            "demes": [
                {"name": "deme0", "start_time": 100, "epochs": [{"start_size": 1}]}
            ],
        }
        with pytest.raises(ValueError):
            parser.parse(data)


class TestValidateEpoch:
    def test_end_time(self):
        data = minimal_graph()
        epoch = data["demes"][0]["epochs"][0]
        epoch["end_time"] = "x"
        with pytest.raises(TypeError):
            parser.parse(data)
        epoch["end_time"] = -1000
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_no_end_time(self):
        data = single_deme_graph(num_epochs=3)
        graph = parser.parse(data)
        assert len(graph.demes["deme0"].epochs) == 3
        del data["demes"][0]["epochs"][1]["end_time"]
        with pytest.raises(ValueError, match="end_time must be specified"):
            parser.parse(data)

    def test_end_time_out_of_order(self):
        data = single_deme_graph(num_epochs=3)
        graph = parser.parse(data)
        assert len(graph.demes["deme0"].epochs) == 3
        data["demes"][0]["epochs"][1]["end_time"] = 0
        with pytest.raises(ValueError, match="end_times must be in decreasing"):
            parser.parse(data)

    def test_start_size(self):
        data = minimal_graph()
        epoch = data["demes"][0]["epochs"][0]
        epoch["start_size"] = "x"
        with pytest.raises(TypeError):
            parser.parse(data)
        epoch["start_size"] = -1000
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_end_size(self):
        data = minimal_graph()
        epoch = data["demes"][0]["epochs"][0]
        epoch["end_size"] = "x"
        with pytest.raises(TypeError):
            parser.parse(data)
        epoch["end_size"] = -1000
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_infinite_interval_non_constant(self):
        data = minimal_graph()
        epoch = data["demes"][0]["epochs"][0]
        epoch["end_size"] = 1000
        epoch["start_size"] = 1000.01
        with pytest.raises(ValueError):
            parser.parse(data)


class TestResolveEpochTimes:
    def test_minimal(self):
        graph = parser.parse(minimal_graph(population_size=10))
        deme = graph.demes["deme0"]
        assert deme.start_time == math.inf
        assert deme.end_time == 0
        assert len(deme.epochs) == 1
        epoch = deme.epochs[0]
        assert epoch.end_time == 0
        assert epoch.start_size == 10
        assert epoch.end_size == 10
        assert epoch.size_function == "exponential"
        assert epoch.selfing_rate == 0
        assert epoch.cloning_rate == 0

    def test_line_topology_one_epoch(self):
        data = {
            "time_units": "generations",
            "defaults": {"epoch": {"start_size": 1}},
            "demes": [
                {"name": "deme0", "epochs": [{"end_time": 20}]},
                {"name": "deme1", "ancestors": ["deme0"], "epochs": [{"end_time": 10}]},
                {"name": "deme2", "ancestors": ["deme1"]},
            ],
        }
        graph = parser.parse(data)
        assert graph.demes["deme0"].start_time == math.inf
        assert graph.demes["deme0"].end_time == 20
        assert graph.demes["deme1"].start_time == 20
        assert graph.demes["deme1"].end_time == 10
        assert graph.demes["deme2"].start_time == 10
        assert graph.demes["deme2"].end_time == 0


class TestPulse:
    def test_simple(self):
        data = minimal_graph(num_demes=2)
        data["pulses"] = [
            {"source": "deme0", "dest": "deme1", "proportion": 0.5, "time": 1}
        ]
        parsed = parser.parse(data).asdict()
        assert data["pulses"] == parsed["pulses"]

    def test_all_missing(self):
        data = minimal_graph(num_demes=2)
        data["pulses"] = [{}]
        with pytest.raises(KeyError):
            parser.parse(data)

    @pytest.mark.parametrize("proportion", [-1, 2])
    def test_bad_proportion(self, proportion):
        data = minimal_graph(num_demes=2)
        data["pulses"] = [
            {"source": "deme0", "dest": "deme1", "proportion": proportion, "time": 1}
        ]
        with pytest.raises(ValueError):
            parser.parse(data)

    def test_bad_deme(self):
        data = minimal_graph(num_demes=2)
        data["pulses"] = [
            {"source": "deme3", "dest": "deme1", "proportion": 0.5, "time": 1}
        ]
        with pytest.raises(KeyError):
            parser.parse(data)

    def test_same_deme(self):
        data = minimal_graph(num_demes=2)
        data["pulses"] = [
            {"source": "deme0", "dest": "deme0", "proportion": 0.5, "time": 1}
        ]
        with pytest.raises(ValueError, match="source deme equal to dest"):
            parser.parse(data)

    def test_bad_time(self):
        data = minimal_graph(num_demes=2)
        data["demes"][1]["start_time"] = 10
        data["demes"][1]["ancestors"] = ["deme0"]
        data["pulses"] = [
            {"source": "deme0", "dest": "deme1", "proportion": 0.5, "time": 20}
        ]
        with pytest.raises(ValueError, match="does not exist"):
            parser.parse(data)


class TestMigration:
    def test_simple_asymmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {
                "source": "deme0",
                "dest": "deme1",
                "rate": 0.5,
                "start_time": 2,
                "end_time": 1,
            }
        ]
        parsed = parser.parse(data).asdict()
        assert data["migrations"] == parsed["migrations"]

    def test_simple_asymmetric_default_times(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [{"source": "deme0", "dest": "deme1", "rate": 0}]
        parsed = parser.parse(data).asdict()
        assert parsed["migrations"] == [
            {
                "source": "deme0",
                "dest": "deme1",
                "rate": 0,
                "start_time": math.inf,
                "end_time": 0,
            }
        ]

    def test_simple_symmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {"demes": ["deme0", "deme1"], "rate": 0.5, "start_time": 2, "end_time": 1}
        ]
        parsed = parser.parse(data).asdict()
        assert data["migrations"] == parsed["migrations"]

    def test_symmetric_and_asymmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {
                "source": "deme0",
                "dest": "deme1",
                "demes": ["deme0", "deme1"],
                "rate": 0.5,
            }
        ]
        with pytest.raises(ValueError, match="both demes and source"):
            parser.parse(data)

    def test_neither_symmetric_or_asymmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {
                "rate": 0.5,
            }
        ]
        with pytest.raises(ValueError, match="either source and dest, or demes"):
            parser.parse(data)

    def test_same_deme_asymmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {
                "source": "deme0",
                "dest": "deme0",
                "rate": 0.5,
            }
        ]
        with pytest.raises(ValueError, match="migrate from a deme to itself"):
            parser.parse(data)

    def test_same_deme_symmetric(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {
                "demes": ["deme0", "deme0"],
                "rate": 0.5,
            }
        ]
        with pytest.raises(ValueError, match="migrate from a deme to itself"):
            parser.parse(data)

    def test_bad_start_time_value(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {"demes": ["deme0", "deme1"], "rate": 0.5, "start_time": -1, "end_time": 1}
        ]
        with pytest.raises(ValueError):
            parser.parse(data).asdict()

    def test_bad_end_time_value(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {"demes": ["deme0", "deme1"], "rate": 0.5, "start_time": 2, "end_time": -1}
        ]
        with pytest.raises(ValueError):
            parser.parse(data).asdict()

    def test_bad_end_time_interval(self):
        data = minimal_graph(num_demes=2)
        data["migrations"] = [
            {"demes": ["deme0", "deme1"], "rate": 0.5, "start_time": 1, "end_time": 100}
        ]
        with pytest.raises(ValueError, match="start_time must be > end_time"):
            parser.parse(data).asdict()

    def test_bad_time_asymmetric(self):
        data = minimal_graph(num_demes=2)
        data["demes"][1]["start_time"] = 10
        data["demes"][1]["ancestors"] = ["deme0"]
        data["migrations"] = [
            {
                "source": "deme0",
                "dest": "deme1",
                "rate": 0.5,
                "start_time": 20,
                "end_time": 11,
            }
        ]
        with pytest.raises(ValueError, match="time interval"):
            parser.parse(data)

    def test_bad_time_symmetric(self):
        data = minimal_graph(num_demes=2)
        data["demes"][1]["start_time"] = 10
        data["demes"][1]["ancestors"] = ["deme0"]
        data["migrations"] = [
            {"demes": ["deme0", "deme1"], "rate": 0.5, "start_time": 20, "end_time": 11}
        ]
        with pytest.raises(ValueError, match="time interval"):
            parser.parse(data)


class TestResolveEpochSizes:
    def test_single_epoch(self):
        data = minimal_graph()
        data["demes"][0]["epochs"][0] = {}
        with pytest.raises(ValueError):
            parser.parse(data)
        data["demes"][0]["epochs"][0] = {"start_size": 100}
        resolved = parser.parse(data).asdict()
        assert resolved["demes"][0]["epochs"][0]["start_size"] == 100
        assert resolved["demes"][0]["epochs"][0]["end_size"] == 100

        data["demes"][0]["epochs"][0] = {"end_size": 200}
        resolved = parser.parse(data).asdict()
        assert resolved["demes"][0]["epochs"][0]["start_size"] == 200
        assert resolved["demes"][0]["epochs"][0]["end_size"] == 200

    def test_propagate_start_size(self):
        data = minimal_graph()
        data["demes"][0]["epochs"] = [
            {"start_size": 1, "end_time": 100},
            {"end_size": 2, "end_time": 50},
        ]

        resolved = parser.parse(data).asdict()
        assert resolved["demes"][0]["epochs"][0]["start_size"] == 1
        assert resolved["demes"][0]["epochs"][0]["end_size"] == 1
        assert resolved["demes"][0]["epochs"][1]["start_size"] == 1
        assert resolved["demes"][0]["epochs"][1]["end_size"] == 2

    def test_propagate_start_and_end_size(self):
        data = minimal_graph()
        data["demes"][0]["epochs"] = [
            {"start_size": 1, "end_time": 100},
            {"end_time": 50},
            {},
        ]
        resolved = parser.parse(data).asdict()
        for j in range(3):
            assert resolved["demes"][0]["epochs"][j]["start_size"] == 1
            assert resolved["demes"][0]["epochs"][j]["end_size"] == 1


class TestDefaults:
    def test_asymmetric_migration_changing_rate(self):
        data = minimal_graph(num_demes=2)
        data["defaults"] = {"migration": {"source": "deme0", "dest": "deme1"}}
        data["migrations"] = [
            {"start_time": 2, "end_time": 1, "rate": 1},
            {"start_time": 1, "end_time": 0, "rate": 0.5},
        ]
        graph = parser.parse(data)
        assert len(graph.migrations) == 2
        for migration in graph.migrations:
            assert migration.source.name == "deme0"
            assert migration.dest.name == "deme1"
        assert graph.migrations[0].rate == 1
        assert graph.migrations[0].start_time == 2
        assert graph.migrations[0].end_time == 1
        assert graph.migrations[1].rate == 0.5
        assert graph.migrations[1].start_time == 1
        assert graph.migrations[1].end_time == 0

    def test_symmetric_migration_changing_rate(self):
        data = minimal_graph(num_demes=2)
        data["defaults"] = {"migration": {"demes": ["deme0", "deme1"]}}
        data["migrations"] = [
            {"start_time": 2, "end_time": 1, "rate": 1},
            {"start_time": 1, "end_time": 0, "rate": 0.5},
        ]
        graph = parser.parse(data)
        assert len(graph.migrations) == 2
        for migration in graph.migrations:
            assert migration.asdict()["demes"] == ["deme0", "deme1"]
        assert graph.migrations[0].rate == 1
        assert graph.migrations[0].start_time == 2
        assert graph.migrations[0].end_time == 1
        assert graph.migrations[1].rate == 0.5
        assert graph.migrations[1].start_time == 1
        assert graph.migrations[1].end_time == 0

    def test_migration_start_time_end_time_rate(self):
        data = minimal_graph(num_demes=3)
        data["defaults"] = {"migration": {"start_time": 2, "end_time": 1, "rate": 1}}
        data["migrations"] = [
            {"source": "deme0", "dest": "deme1"},
            {"source": "deme1", "dest": "deme2"},
        ]
        graph = parser.parse(data)
        assert len(graph.migrations) == 2
        for migration in graph.migrations:
            migration.start_time == 2
            migration.end_time == 1
            migration.rate == 1
        assert graph.migrations[0].source.name == "deme0"
        assert graph.migrations[0].dest.name == "deme1"
        assert graph.migrations[1].source.name == "deme1"
        assert graph.migrations[1].dest.name == "deme2"

    def test_pulse_time_proportion(self):
        data = minimal_graph(num_demes=3)
        data["defaults"] = {"pulse": {"time": 1, "proportion": 0.5}}
        data["pulses"] = [
            {"source": "deme0", "dest": "deme1"},
            {"source": "deme1", "dest": "deme2"},
        ]
        graph = parser.parse(data)
        assert len(graph.pulses) == 2
        for pulse in graph.pulses:
            pulse.time == 1
            pulse.proportion == 0.5
        assert graph.pulses[0].source.name == "deme0"
        assert graph.pulses[0].dest.name == "deme1"
        assert graph.pulses[1].source.name == "deme1"
        assert graph.pulses[1].dest.name == "deme2"

    def test_deme_description_start_time(self):
        data = minimal_graph(num_demes=3)
        data["defaults"] = {
            "deme": {"description": "default", "start_time": 1, "ancestors": ["deme0"]}
        }
        data["demes"][0]["start_time"] = math.inf
        data["demes"][0]["ancestors"] = []
        data["demes"][1]["description"] = "not default"
        data["demes"][1]["start_time"] = 2
        parsed = parser.parse(data).asdict()
        assert parsed["demes"][1]["description"] == "not default"
        assert parsed["demes"][1]["start_time"] == 2
        assert parsed["demes"][2]["description"] == "default"
        assert parsed["demes"][2]["start_time"] == 1

    def test_deme_ancestors_proportions(self):
        data = minimal_graph(num_demes=4)
        data["defaults"] = {
            "deme": {
                "ancestors": ["deme0", "deme1"],
                "proportions": [0.5, 0.5],
                "start_time": 1,
            }
        }
        for j in range(2):
            data["demes"][j]["start_time"] = math.inf
            data["demes"][j]["ancestors"] = []
            data["demes"][j]["proportions"] = []
        parsed = parser.parse(data).asdict()
        assert len(parsed["demes"]) == 4
        assert parsed["demes"][0]["ancestors"] == []
        assert parsed["demes"][1]["ancestors"] == []
        assert parsed["demes"][2]["ancestors"] == ["deme0", "deme1"]
        assert parsed["demes"][3]["ancestors"] == ["deme0", "deme1"]
        assert parsed["demes"][2]["proportions"] == [0.5, 0.5]
        assert parsed["demes"][3]["proportions"] == [0.5, 0.5]

    def test_no_epochs_specified(self):
        num_demes = 5
        data = {
            "time_units": "generations",
            "defaults": {"epoch": {"start_size": 1, "end_size": 2, "end_time": 10}},
            "demes": [{"name": "deme0", "epochs": [{"start_size": 1, "end_size": 1}]}]
            + [
                {"name": f"deme{j}", "start_time": 100, "ancestors": ["deme0"]}
                for j in range(1, num_demes)
            ],
        }
        graph = parser.parse(data)
        assert len(graph.demes) == num_demes
        for deme in list(graph.demes.values())[1:]:
            assert len(deme.epochs) == 1
            epoch = deme.epochs[0]
            assert epoch.start_size == 1
            assert epoch.end_size == 2
            assert epoch.end_time == 10

    def test_many_epochs_one_deme_global(self):
        num_epochs = 4
        data = {
            "time_units": "generations",
            "defaults": {
                "epoch": {
                    "start_size": 1,
                    "end_size": 2,
                    "cloning_rate": 0.5,
                    "selfing_rate": 0.1,
                }
            },
            "demes": [
                {
                    "name": "deme0",
                    "epochs": [{"end_time": 100, "start_size": 1, "end_size": 1}]
                    + [{"end_time": j} for j in range(num_epochs - 1, -1, -1)],
                }
            ],
        }
        graph = parser.parse(data)
        deme = graph.demes["deme0"]
        assert len(deme.epochs) == num_epochs + 1
        for epoch in deme.epochs[1:]:
            assert epoch.start_size == 1
            assert epoch.end_size == 2
            assert epoch.cloning_rate == 0.5
            assert epoch.selfing_rate == 0.1

    def test_many_epochs_one_deme_local(self):
        num_epochs = 4
        data = {
            "time_units": "generations",
            "demes": [
                {
                    "name": "deme0",
                    "defaults": {
                        "epoch": {
                            "start_size": 1,
                            "end_size": 2,
                            "cloning_rate": 0.5,
                            "selfing_rate": 0.1,
                        }
                    },
                    "epochs": [{"end_time": 100, "start_size": 1, "end_size": 1}]
                    + [{"end_time": j} for j in range(num_epochs - 1, -1, -1)],
                }
            ],
        }
        graph = parser.parse(data)
        deme = graph.demes["deme0"]
        assert len(deme.epochs) == num_epochs + 1
        for epoch in deme.epochs[1:]:
            assert epoch.start_size == 1
            assert epoch.end_size == 2
            assert epoch.cloning_rate == 0.5
            assert epoch.selfing_rate == 0.1

    def test_epoch_default_overrides(self):
        num_epochs = 4
        data = {
            "time_units": "generations",
            "defaults": {
                "deme": {"start_time": 100, "ancestors": ["ancestral"]},
                "epoch": {
                    "start_size": 1,
                    "end_size": 2,
                    "cloning_rate": 0.5,
                    "selfing_rate": 0.1,
                },
            },
            "demes": [
                {
                    "name": "ancestral",
                    "start_time": math.inf,
                    "ancestors": [],
                    "epochs": [{"start_size": 1, "end_size": 1}],
                },
                {
                    "name": "deme0",
                    "defaults": {
                        "epoch": {
                            "start_size": 2,
                            "end_size": 3,
                            "cloning_rate": 0.6,
                            "selfing_rate": 0.2,
                        }
                    },
                    "epochs": [{"end_time": j} for j in range(num_epochs - 1, -1, -1)],
                },
                {
                    "name": "deme1",
                    "epochs": [{"end_time": j} for j in range(num_epochs - 1, -1, -1)],
                },
                {
                    "name": "deme2",
                    "epochs": [{"end_time": j} for j in range(num_epochs - 1, -1, -1)],
                },
            ],
        }
        graph = parser.parse(data)
        deme = graph.demes["deme0"]
        assert len(deme.epochs) == num_epochs
        for epoch in deme.epochs:
            assert epoch.start_size == 2
            assert epoch.end_size == 3
            assert epoch.cloning_rate == 0.6
            assert epoch.selfing_rate == 0.2
        for deme_id in ["deme1", "deme2"]:
            deme = graph.demes[deme_id]
            assert len(deme.epochs) == num_epochs
            for epoch in deme.epochs:
                assert epoch.start_size == 1
                assert epoch.end_size == 2
                assert epoch.cloning_rate == 0.5
                assert epoch.selfing_rate == 0.1


class TestGraphUtilities:
    def test_str(self):
        graph = parser.parse(minimal_graph())
        assert len(str(graph)) > 0


@pytest.mark.parametrize(
    "yaml_path", map(str, pathlib.Path("../examples/").glob("*.yaml"))
)
def test_examples(yaml_path):
    yaml = YAML(typ="safe")
    with open(yaml_path) as source:
        data = yaml.load(source)
    graph = parser.parse(data)
    graph_data = graph.asdict()

    yaml_path = pathlib.Path(yaml_path)
    json_path = yaml_path.parent / yaml_path.with_suffix(".resolved.json")
    with open(json_path) as source:
        json_data = json.load(source)
    # Note: we'll probably need to do something less strict here.
    assert json_data == graph_data
