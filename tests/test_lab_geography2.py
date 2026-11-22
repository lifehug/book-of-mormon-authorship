"""BOM-116 second design: reading, tables, the window counter, consistency (lab.geography2)."""

import copy
import json

import numpy as np
import pytest

from lab import geography2 as g
from lab import geography2_earth as ge
from metadata import config


@pytest.fixture(scope="module")
def cfg():
    c = copy.deepcopy(config.load())
    c["lab"]["geography2"]["earth"]["raster_deg"] = 1.0
    return c


def s_of(cfg):
    return g.settings(cfg)


# ------------------------------------------------------------------ earth


def test_rasterize_square_and_hole():
    outer = np.array([[10, 10], [20, 10], [20, 20], [10, 20], [10, 10]], dtype=float)
    hole = np.array([[14, 14], [16, 14], [16, 16], [14, 16], [14, 14]], dtype=float)
    m = ge.rasterize([[outer, hole]], 1.0)
    r = lambda lat: int(90 - lat)  # noqa: E731
    c = lambda lon: int(lon + 180)  # noqa: E731
    assert m[r(12.5), c(12.5)] and not m[r(15.5), c(15.5)] and not m[r(25.5), c(25.5)]
    assert m.sum() == 100 - 4


def test_directional_distance_simple():
    water = np.ones((180, 360), dtype=bool)
    water[80:100, 170:190] = False  # a 20 x 20 degree island around (0, 0)
    d = ge.directional_distance(water, 1.0, 5000)
    i, j = 90, 180  # lat -0.5, lon 0.5
    east = d[ge.DIRS.index("E"), i, j]
    west = d[ge.DIRS.index("W"), i, j]
    assert east < west  # the pixel sits east of the island's middle
    assert 9 * 111 * 0.99 < east < 11 * 111
    assert d[:, 0, 0].max() == 0  # water


def toy_earth(cfg):
    """A 1-degree world: an ocean with a land block, a lake, a mountain and a river."""
    water = np.ones((180, 360), dtype=bool)
    water[60:120, 150:230] = False  # land: lat -30..30, lon -30..50
    water[85:95, 188:191] = True  # a lake near lat 0, lon 9
    elev = np.zeros((180, 360), dtype=np.float32)
    elev[60:120, 150:230] = 100
    elev[60:80, 200:230] = 2000  # high in the north-east
    dist = ge.directional_distance(water, 1.0, 3000).astype(np.float16)
    river = {
        "name": "Toy",
        "head": [35.0, 25.0],
        "mouth": [35.0, -25.0],
        "lon": [35.0] * 6,
        "lat": [25.0, 15.0, 5.0, -5.0, -15.0, -25.0],
    }
    return ge.Earth.from_arrays(cfg, water, elev, dist, [river])


def test_window_and_solver(cfg):
    s = s_of(cfg)
    earth = toy_earth(cfg)
    a = s["part_a"] | {"grid": 9}
    win = ge.window(earth, 0.0, 10.0, 6000, a)
    assert win["land"].any() and win["water"].any() and win["rivers"]
    feats = [
        {"kind": "water", "a": "lake"},
        {"kind": "direction", "a": "hill", "b": "plain", "dir": "N", "cone": 45},
        {"kind": "higher", "a": "hill", "b": "plain"},
        {"kind": "river", "river": "toy", "a": "plain", "role": "bank"},
        {"kind": "flows", "river": "toy", "toward": "S", "cone": 67.5},
    ]
    assert g.window_verdict(feats, win, [0], a)[0] == "pass"
    turned = g.rotate(feats, 4)  # north becomes south: the hill now must lie south and be higher
    assert g.window_verdict(turned, win, [0], a)[0] == "fail"
    assert g.window_verdict(turned, win, list(range(8)), a)[0] == "pass"
    comp = ge.compile_features(feats, win, 0, a)
    assert ge.solve(*comp, node_limit=0) in ("pass", "undecided")


def test_solver_states():
    m = np.array([[False, True], [True, False]])
    dom = [np.array([True, True]), np.array([True, True])]
    assert ge.solve([("p", "a"), ("p", "b")], dom, [(0, 1, m)], 100) == "pass"
    never = np.zeros((2, 2), dtype=bool)
    assert ge.solve([("p", "a"), ("p", "b")], dom, [(0, 1, never)], 100) == "fail"


# ------------------------------------------------------------------ reading and tables


def test_parse_first_and_second():
    reply = (
        'Here: [{"kind":"direction","a":"Zarahemla","b":"Nephi","dir":"north","ref":"r1"},'
        '{"kind":"bogus","a":"x"},{"kind":"days","a":"A","b":"B","days":"3","ref":"r1"}]'
    )
    items = g.parse_reply(reply)
    assert [i["kind"] for i in items] == ["direction", "days"]
    assert items[0]["dir"] == "N" and items[1]["traveller"] == "unknown"
    assert g.parse_reply("no array here") is None
    sec = "direction | Zarahemla | Nephi | N | r1\nriver | Sidon | Manti | source | r2\nnoise"
    items = g.parse_reply_second(sec)
    assert items[1] == {
        "kind": "river",
        "ref": "r2",
        "river": "Sidon",
        "a": "Manti",
        "role": "source",
    }
    assert g.parse_reply_second("NONE") == []
    assert g.parse_reply_second("I cannot help") is None


def test_norm():
    assert g.norm("the land of Zarahemla") == "zarahemla"
    assert g.norm("City of Zarahemla") == "zarahemla"
    assert g.norm("the sea east") == "east sea"
    assert g.norm("the land northward") == "land northward"
    assert g.norm("narrow neck of land") == "narrow neck"


def test_window_relations_guards():
    w = {
        "refs": ["Alma 22 para 1", "Alma 22 para 2"],
        "text": "[Alma 22 para 1] the land of Zarahemla",
    }
    items = [
        {"kind": "water", "a": "Zarahemla", "ref": "Alma 22 para 1"},
        {"kind": "water", "a": "Zarahemla", "ref": "Mosiah 9"},
        {"kind": "water", "a": "Cumorah", "ref": "Alma 22 para 1"},
    ]
    kept, drop = g.window_relations(items, w)
    assert len(kept) == 1 and kept[0]["a"] == "zarahemla"
    assert drop == {"reference not in the window": 1, "name not in the passage": 1}


def test_build_table_and_conflicts():
    rels = [
        {"kind": "direction", "a": "x", "b": "y", "dir": "N", "ref": "1"},
        {"kind": "direction", "a": "x", "b": "y", "dir": "N", "ref": "2"},
        {"kind": "direction", "a": "y", "b": "x", "dir": "NE", "ref": "3"},
        {"kind": "sea", "a": "sea", "side": None, "ref": "4"},
    ]
    t = g.build_table(rels, {"sea"})
    assert len(t) == 2
    kept, dropped = g.resolve_conflicts(t)
    assert dropped == 1 and kept[0]["refs"] == ["1", "2"]


def test_features_and_rotation(cfg):
    s = s_of(cfg)
    t = [
        {"kind": "direction", "a": "x", "b": "y", "dir": "N", "refs": ["1"]},
        {"kind": "sea", "a": "x", "side": "W", "refs": ["1"]},
        {"kind": "near", "a": "x", "b": "y", "refs": ["1"]},
        {"kind": "days", "a": "x", "b": "y", "days": 2.0, "traveller": "army", "refs": ["1"]},
        {
            "kind": "neck",
            "a": "n",
            "water_sides": "E-W",
            "crossing_days": 1.5,
            "traveller": "walker",
            "refs": ["1"],
        },
    ]
    strong = g.features(t, s)
    kinds = sorted(f["kind"] for f in strong)
    assert kinds == ["days", "direction", "neck", "sea"]
    assert next(f for f in strong if f["kind"] == "neck")["width_km"] == 1.5 * 40
    weak = g.features(t, s, "weak")
    assert {f["kind"] for f in weak} == {"direction", "sea", "near"}
    assert all(f.get("side") is None for f in weak if f["kind"] == "sea")
    turned = g.rotate(strong, 2)
    assert next(f for f in turned if f["kind"] == "direction")["dir"] == "E"
    assert next(f for f in turned if f["kind"] == "neck")["water_sides"] == "N-S"


def test_clark_key_features(cfg):
    feats = g.clark_features(s_of(cfg))
    points = {f["point"] for f in feats}
    assert len(points) == 10
    neck = next(f for f in feats if f["kind"] == "neck")
    assert neck["width_km"] == 4 * s_of(cfg)["clark_unit_km"][1]


def test_windows_of_respects_quoted_boundary():
    units = [
        ("a", "w " * 300, False),
        ("b", "w " * 50, False),
        ("c", "w " * 50, True),
        ("d", "w " * 900, True),
    ]
    wins = g.windows_of(units, 400)
    assert [w["refs"] for w in wins] == [["a", "b"], ["c"], ["d #1"], ["d #2"], ["d #3"]]
    assert all(w["words"] <= 400 for w in wins)


def test_kappa_perfect_and_none():
    a = [{"kind": "direction", "a": "x", "b": "y", "dir": "N", "window": "w"}]
    b = [
        {"kind": "direction", "a": "y", "b": "x", "dir": "S", "window": "w"},
        {"kind": "near", "a": "x", "b": "z", "window": "w"},
    ]
    k = g.kappa(a, b)
    assert k["items"] == 2 and k["observed_agreement"] == 0.5


def test_consistency_counts_a_cycle(cfg):
    s = s_of(cfg)
    t = [
        {"kind": "direction", "a": "b", "b": "a", "dir": "N"},
        {"kind": "direction", "a": "c", "b": "b", "dir": "N"},
        {"kind": "direction", "a": "a", "b": "c", "dir": "N"},
    ]
    c = g.consistency(t, s)
    assert c["opportunities"] == 3 and c["contradictions"] == 3
    ok = t[:2] + [{"kind": "direction", "a": "c", "b": "a", "dir": "N"}]
    c2 = g.consistency(ok, s)
    assert c2["contradictions"] == 0 and c2["opportunities"] == 1 and c2["rigidity"] == 1.0


def test_auc_and_place():
    assert g.auc([0.0, 0.1], [0.2, 0.3]) == 1.0
    assert g.auc([0.2], [0.2]) == 0.5
    assert g.place_book(0.05, [0.0, 0.1], [0.3, 0.4]) == "more like real"
    assert g.place_book(0.35, [0.0, 0.1], [0.3, 0.4]) == "more like invented"


def test_part_a_verdicts(cfg):
    a = s_of(cfg)["part_a"]
    assert g.part_a_verdict(0.01, 0.01, True, a).startswith("constraining, and")
    assert g.part_a_verdict(0.5, 0.5, True, a) == "does not pick out a region"
    assert g.part_a_verdict(0.0, 0.0, False, a) == "fits nowhere under this reading"
    assert g.part_a_verdict(0.04, 0.3, True, a).startswith("cannot tell")


def test_dev_table_refs_exist_in_kjv():
    refs = {json.loads(x)["ref"] for x in open("data/kjv/kjv.jsonl")}
    for r in g.dev_tables()["bible_hand"]:
        for ref in r["refs"]:
            assert ref in refs, ref
