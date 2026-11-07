"""The blind run's false-match ladder (BOM-32; owner, 2026-11-07: objective data, not one rule)."""

from blind.thresholds import ladder, rung
from blind.unblind import ladder_report

RATES = [0.01, 0.05, 0.10, 0.20, 0.30, 0.50]


def test_ladder_is_monotone_and_honest_about_ties() -> None:
    neg = [i / 100 for i in range(100)]
    pos = [0.5 + i / 200 for i in range(100)]
    steps = ladder(pos, neg, RATES)
    th = [s["threshold"] for s in steps]
    fm = [s["false_match"] for s in steps]
    assert th == sorted(th, reverse=True) and fm == sorted(fm)
    assert all(abs(s["false_match"] - s["rate"]) <= 0.02 for s in steps)
    # ties at the top (as General Imposters' 1.0): the low rungs share one threshold, and the
    # real false-match rate is reported, not the nominal one
    tied = ladder(pos, [1.0] * 20 + [0.5] * 80, RATES)
    assert tied[0]["threshold"] == tied[1]["threshold"] == 1.0
    assert tied[0]["false_match"] == 0.2


def test_rung_is_the_lowest_matching_rate() -> None:
    steps = ladder([0.9] * 10, [i / 100 for i in range(100)], RATES)
    assert rung(1.5, steps)["rate"] == 0.01
    assert rung(0.75, steps)["rate"] == 0.30
    assert rung(-1.0, steps) is None


def test_ladder_report_chunks_halves_and_decoys() -> None:
    steps = ladder([0.9] * 10, [i / 100 for i in range(100)], RATES)
    units = {"u_a": "Alpha", "u_a2": "Alpha", "u_b": "Beta"}
    key = {"s1": {"kind": "bom", "chunk_id": "c1"}, "s2": {"kind": "bom", "chunk_id": "c2"},
           "d1": {"kind": "decoy", "author": "Alpha"},
           "d2": {"kind": "decoy", "author": "control:x"}}  # fmt: skip
    per = {"s1": {"g": {"u_a": 0.2, "u_a2": 0.995, "u_b": 0.75}},  # Alpha's best unit counts
           "s2": {"g": {"u_a": 0.1, "u_b": 0.1}},
           "d1": {"g": {"u_a": 0.995, "u_b": 0.75}},
           "d2": {"g": {"u_a": 0.2, "u_b": 0.85}}}  # fmt: skip
    split = {"c1": "discovery", "c2": "confirmation"}
    r = ladder_report(per, lambda rec: rec["g"], steps, key, units, split)
    assert r["chunks"]["c1"]["Alpha"]["rate"] == 0.01
    assert r["chunks"]["c1"]["Beta"]["rate"] == 0.30 and r["chunks"]["c2"]["Beta"] is None
    assert r["by_half"]["discovery"]["Alpha"]["0.01"] == 1
    assert r["by_half"]["confirmation"]["Alpha"]["none"] == 1
    cd = r["decoys"]["candidate"]
    assert cd["decoys"] == 1 and cd["own_match"]["0.01"] == 1 and cd["rival_at_or_below"] == 0
    ctl = r["decoys"]["control"]
    assert ctl["decoys"] == 1 and ctl["false_match"]["0.1"] == 0 and ctl["false_match"]["0.2"] == 1
