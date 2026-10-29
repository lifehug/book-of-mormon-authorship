"""BOM-40: the multiverse runner's enumeration, overrides and specification curve."""

import json

import pytest

from pipeline import cli


def test_configurations_override_and_sample():
    base = {"seed": 1, "classic": {"a": 1, "b": {"c": 2}}}
    spec = {"ranges": {"classic.a": [1, 2], "classic.b.c": [2, 3, 4]}}
    every = cli.configurations(spec, base, max_configs=100)
    assert len(every) == 6
    assert {(c["config"]["classic"]["a"], c["config"]["classic"]["b"]["c"]) for c in every} == {
        (a, c) for a in (1, 2) for c in (2, 3, 4)
    }
    assert base["classic"]["a"] == 1  # the base is not mutated
    some = cli.configurations(spec, base, max_configs=4)
    assert len(some) == 4 and some == cli.configurations(spec, base, max_configs=4)  # seeded
    with pytest.raises(KeyError):
        cli._set({"x": {}}, "x.y", 1)


def test_specification_curve_counts_agreement(tmp_path):
    def write(d, findings):
        d.mkdir()
        t1, t2 = findings
        (d / "s.json").write_text(json.dumps({"per_test": {"t1": {"m": t1}, "t2": {"m": t2}}}))

    write(tmp_path / "reg", (True, True))
    write(tmp_path / "r1", (True, False))
    write(tmp_path / "r2", (True, True))
    runs = [{"choices": {"k": 1}, "out": str(tmp_path / "r1")},
            {"choices": {"k": 2}, "out": str(tmp_path / "r2")}]  # fmt: skip
    curve = cli.specification_curve(tmp_path / "reg", runs, ["s"])
    assert curve["agreement"] == {"t1:m": 1.0, "t2:m": 0.5}
    assert curve["lowest_agreement"] == 0.5
    assert cli.curve_svg(curve).startswith("<svg")
