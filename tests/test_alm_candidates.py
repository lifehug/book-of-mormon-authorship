"""The candidate and control authorial models' pure logic (BOM-28; Amendment 30)."""

import random

from alm.candidates import control_sample, holdout_blocks, margins, slug, window_starts


def test_holdout_follows_amendment_22() -> None:
    assert holdout_blocks(9, 5, 5, 0.25) is None  # too short to test: trains on everything
    assert holdout_blocks(10, 5, 5, 0.25) == 5  # at least one test window
    assert holdout_blocks(41, 5, 5, 0.25) == 11  # ceil(41/4)
    assert holdout_blocks(277, 5, 5, 0.25) == 70


def test_test_windows_inside_the_tail() -> None:
    starts = window_starts(41, 11, 5, 20, random.Random(0))
    assert starts == list(range(30, 37))  # all 7 distinct windows fit in blocks 30-40
    many = window_starts(277, 70, 5, 20, random.Random(0))
    assert len(many) == 20 and min(many) >= 207 and max(many) <= 272
    assert many == sorted(set(many)) == window_starts(277, 70, 5, 20, random.Random(0))


def test_control_sample_middles_and_target() -> None:
    vols = [(f"v{i}", [f"w{i}_{j}" for j in range(30_000)]) for i in range(4)]
    got = control_sample(vols, 50_000, 5_000, random.Random(1))
    assert sum(len(ws) for _, ws in got) == 50_000
    assert [len(ws) for _, ws in got] == [12_500, 12_500, 12_500, 12_500]
    # the middle of each volume
    v, ws = got[0]
    assert ws[0] == f"{v}_{15_000 - 6_250}".replace("v", "w")
    small = control_sample(vols, 300_000, 5_000, random.Random(1))
    assert sum(len(ws) for _, ws in small) == 120_000  # every volume whole: the list runs out
    assert control_sample([], 10, 5, random.Random(0)) == []


def test_margin_is_best_control_minus_candidate() -> None:
    kinds = {"a": "candidate", "b": "candidate", "c1": "control", "c2": "control"}
    m = margins({"a": -0.30, "b": -0.05, "c1": -0.10, "c2": -0.20}, kinds)
    assert m == {"a": -0.20 + 0.30, "b": -0.20 + 0.05}
    assert m["a"] > 0 > m["b"]


def test_slug() -> None:
    assert slug("cand", "W. W. Phelps", "printed_by_author", "post1830") == (
        "cand__w-w-phelps__printed_by_author__post1830"
    )
