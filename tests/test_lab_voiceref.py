"""BOM-100: the voice-reference scoring's own pieces behave as stated (no model, no text)."""

import numpy as np
import pytest

from lab.voiceref import (
    analyse,
    chunk_z,
    judge,
    placebo,
    shares,
    take,
    verdict,
    weighted_quantile,
)

CFG = {
    "seed": 1,
    "lab": {
        "voice_reference": {
            "seed": "t",
            "resamples": 200,
            "interval": 0.95,
            "tar": 0.95,
            "same_voice_tolerance": 0.05,
        }
    },
}


def test_shares_are_equal_and_from_the_middle():
    src = [list(range(10)), list(range(100, 120))]
    assert shares(src, 5) == [(3, 3), (9, 2)]
    assert take(src, 5) == [3, 4, 5, 109, 110]
    with pytest.raises(ValueError):
        shares([[1, 2]], 3)


def test_chunk_z_and_weighted_quantile():
    z = chunk_z(np.array([[1.0, 2.0, 3.0], [5.0, 5.0, 5.0]]))
    assert np.allclose(z[0].mean(), 0) and np.allclose(z[1], 0)
    # two groups weighted equally: the small group counts as much as the big one
    q = weighted_quantile([np.zeros(99), np.ones(1)], 0.6)
    assert q == 1.0


def _toy(n=8, person=0.6, seed=0):
    """Three writers. Every chunk's loss has a large chunk-difficulty term shared by all models,
    a voice term (ordinary models fit ordinary chunks better) and a person term on the right
    writer's models; the voice reference fits scripture chunks well."""
    rng = np.random.default_rng(seed)
    writers = ["a", "b", "c"]
    meta, rows = [], []
    for w in writers:
        for v in ("prophetic", "ordinary"):
            for i in range(n):
                meta.append((w, v, i))
                diff = rng.normal(0, 2)
                row = []
                for m in writers:
                    for mv in ("prophetic", "ordinary"):
                        x = 5 + diff + rng.normal(0, 0.1)
                        x -= 0.5 if mv == v else 0
                        x -= person if m == w else 0
                        row.append(x)
                rows.append(row)
    L = np.array(rows)
    base = L.mean(axis=1) + 0.3
    ref = L.mean(axis=1) - np.array([0.4 if m[1] == "prophetic" else 0 for m in meta])
    return L, base, ref, meta, writers


def test_a_per_chunk_reference_never_changes_the_unscaled_attribution():
    L, base, ref, meta, writers = _toy()
    r = analyse(L, base, ref, ref + 0.1, meta, writers, CFG)
    assert all(r["unscaled_identical"].values())
    names = [n for n in r["scorings"] if n.endswith("_unscaled")]
    cv = {r["scorings"][n]["cross_voice"]["macro"] for n in names}
    assert len(cv) == 1


def test_person_signal_is_found_and_reported_with_intervals():
    L, base, ref, meta, writers = _toy()
    r = analyse(L, base, ref, None, meta, writers, CFG)
    s = r["scorings"]["voice_out_scaled"]
    assert s["cross_voice"]["macro"] == 1.0
    lo, hi = s["cross_voice"]["macro_ci"]
    assert lo <= 1.0 <= hi
    assert "minus_base_scaled_ci" in s["cross_voice"]
    assert r["chance"] == round(1 / 3, 3)
    assert "voice_loo_scaled" not in r["scorings"]


def test_placebo_counts_confident_assignments_when_the_writer_is_absent():
    L, base, ref, meta, writers = _toy(person=3.0)
    names = [f"{w}|{v}" for w in writers for v in ("prophetic", "ordinary")]
    col_ix = {n: i for i, n in enumerate(names)}
    S = L - base[:, None]
    p = placebo(S, meta, writers, col_ix, 0.95)
    # the true writer is far ahead; without them nothing should reach the true writers' scores
    assert p["macro"] == 0.0
    pz = placebo(S, meta, writers, col_ix, 0.95, chunk_z)
    assert set(pz["confident_share"]) == set(writers)


def test_verdict_needs_both_doses():
    ok = {"W1_above_chance": True, "W2_above_base": True, "W3_same_voice_kept": True}
    half = {"W1_above_chance": True, "W2_above_base": False, "W3_same_voice_kept": True}
    assert verdict({"s": ok, "l": ok}) == "works"
    assert verdict({"s": ok, "l": half}) == "does not work reliably"
    assert verdict({"s": half, "l": half}) == "does not work"
    assert verdict({"s": ok}).startswith("cannot tell")


def test_judge_reads_the_three_criteria():
    r = {
        "chance": 0.2,
        "scorings": {
            "voice_out_scaled": {
                "cross_voice": {"macro_ci": [0.3, 0.5], "minus_base_scaled_ci": [0.01, 0.2]},
                "same_voice_ordinary": {"macro": 0.86},
            },
            "base_scaled": {"same_voice_ordinary": {"macro": 0.9}},
        },
    }
    assert all(judge(r, CFG).values())
    r["scorings"]["voice_out_scaled"]["same_voice_ordinary"]["macro"] = 0.8
    assert not judge(r, CFG)["W3_same_voice_kept"]
