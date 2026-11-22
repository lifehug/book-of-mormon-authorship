"""BOM-116: the geography extractor, the consistency check and the optimiser on toy cases."""

import numpy as np

from lab import geography as g

W = {
    "min_mentions": 1,
    "max_gap_chars": 60,
    "sentence_max_chars": 1500,
    "unit_km": {"furlong": 0.201, "mile": 1.609, "league": 4.83},
    "cone_deg": 67.5,
    "higher_margin_m": 0,
    "km_per_day": [8, 40],
    "distance_factor": 1.6,
    "near_km": 50,
    "restarts": 3,
    "max_sweeps": 10,
}


def kinds(units):
    t = g.extract(units, W)
    return {(c["kind"], c["a"], c["b"], c["value"]) for c in t["constraints"]}


def test_direction_and_border():
    got = kinds(
        [
            ("r1", "They came to the land of Ara. The land of Ara is on the north of Bel."),
            ("r2", "And they went to Bel. And the city of Cor, on the east by the land of Bel."),
        ]
    )
    assert ("direction", "Ara", "Bel", "north") in got
    assert ("direction", "Bel", "Cor", "east") in got


def test_up_down_needs_both_places():
    got = kinds(
        [
            ("r1", "They went up from the land of Ara to the land of Bel."),
            ("r2", "And they went down to the land of Cor."),
        ]
    )
    assert ("higher", "Bel", "Ara", None) in got
    assert not any(k[0] == "higher" and "Cor" in k for k in got)


def test_days_distance_sea_near_neck():
    got = kinds(
        [
            ("r1", "It is three days' journey from the land of Ara to the land of Bel."),
            ("r1b", "It was a day and a half's journey from the city of Cor to Dan."),
            ("r2", "The city of Cor is six miles from the city of Dan."),
            ("r3", "The land of Ara, which was by the sea west."),
            ("r4", "The land of Bel was near the land of Dan."),
            ("r5", "The land of Cor reached from the sea east to the sea west."),
            ("r6", "They came to the narrow neck of land and to the land of Dan."),
        ]
    )
    assert ("days", "Ara", "Bel", 3.0) in got
    assert ("days", "Cor", "Dan", 1.5) in got
    assert ("distance", "Cor", "Dan", round(6 * 1.609, 1)) in got
    assert ("sea", "Ara", None, "west") in got
    assert ("near", "Bel", "Dan", None) in got
    assert ("sea", "Cor", None, "east") in got and ("sea", "Cor", None, "west") in got
    assert ("isthmus", "Narrowneck", None, None) in got


def test_people_are_not_places():
    text = "He went to Abel. Abel said no. Abel said yes. In the land of Ur."
    names = g.lexicon([("r", text)], W)
    assert "Ur" in names and "Abel" not in names


def test_number_words():
    assert g.number("three") == 3 and g.number("six hundred") == 600 and g.number("12") == 12
    assert g.number("many") is None


def test_cycles_found():
    cons = [
        {"kind": "direction", "a": "A", "b": "B", "value": "north", "refs": ["1"]},
        {"kind": "direction", "a": "B", "b": "C", "value": "north", "refs": ["2"]},
        {"kind": "direction", "a": "C", "b": "A", "value": "north", "refs": ["3"]},
        {"kind": "direction", "a": "D", "b": "A", "value": "east", "refs": ["4"]},
    ]
    c = g.cycles(cons)
    assert c["north_south"]["in_a_cycle"] == 3
    assert c["east_west"]["in_a_cycle"] == 0
    assert c["groups_of_linked_places"] == 1


def toy_window():
    lat = np.array([0.0, 1.0, 0.0, -1.0, 0.0])
    lon = np.array([0.0, 0.0, 1.0, 0.0, -1.0])
    win = {
        "lat": lat,
        "lon": lon,
        "dem": np.array([10.0, 500.0, 20.0, 5.0, 30.0]),
        "near": np.array([False, False, True, False, False]),
        "side": {d: np.zeros(5, dtype=bool) for d in g.DIRS},
        "neck": np.zeros(5, dtype=bool),
    }
    return win


def test_best_fit_satisfies_a_consistent_set():
    places, cons = g.compile_constraints(
        [
            {"kind": "direction", "a": "A", "b": "B", "value": "north", "refs": []},
            {"kind": "higher", "a": "A", "b": "B", "value": None, "refs": []},
            {"kind": "sea", "a": "C", "b": None, "value": None, "refs": []},
        ]
    )
    r = g.best_fit(places, cons, toy_window(), W, np.random.default_rng(0))
    assert r["share"] == 1.0


def test_best_fit_cannot_beat_a_contradiction():
    places, cons = g.compile_constraints(
        [
            {"kind": "direction", "a": "A", "b": "B", "value": "north", "refs": []},
            {"kind": "direction", "a": "B", "b": "A", "value": "north", "refs": []},
        ]
    )
    r = g.best_fit(places, cons, toy_window(), W, np.random.default_rng(0))
    assert r["share"] == 0.5


def test_percentile_counts_ties_half():
    assert g.percentile(1.0, [0.5, 1.0, 1.0, 0.2]) == 75.0
    assert g.percentile(None, [1.0]) is None
