"""The Bayesian synthesis on synthetic method outputs (BOM-35)."""

import math

import pytest

from synth.model import NONE, band_rates, chunk_loglik, evidence, posterior, synthesise

CANDS = ["A", "B", "C"]
CFG = {"synthesis": {"prior_none": 0.5, "prior_grid": [0.2, 0.35, 0.5, 0.65, 0.8]}}
RATES = {"pos": {"match": 0.6, "inconclusive": 0.3, "non_match": 0.1},
         "neg": {"match": 0.05, "inconclusive": 0.35, "non_match": 0.6}}  # fmt: skip
FAM = {"classical": {"accuracy": 0.8, **RATES}, "embedding": {"accuracy": 0.7, **RATES}}


def test_band_rates_smoothed_and_normalised() -> None:
    th = {"match": 0.9, "non_match": 0.2}
    r = band_rates([0.95, 0.95, 0.5], [0.1, 0.1, 0.1, 0.5], th, 0.5)
    for side in ("pos", "neg"):
        assert math.isclose(sum(r[side].values()), 1.0)
        assert min(r[side].values()) > 0  # smoothing: no zero rate
    assert r["pos"]["match"] > r["neg"]["match"]


def test_posterior_sums_to_one_and_follows_evidence() -> None:
    ev = {"classical": evidence([("A", "match")] * 4, 0.8, RATES, CANDS)}
    p = posterior(ev, {"classical": 1.0}, CANDS, 0.5)
    assert math.isclose(sum(p.values()), 1.0)
    assert max(p, key=p.get) == "A"
    flat = posterior(ev, {"classical": 0.0}, CANDS, 0.5)  # weight 0: the prior alone
    assert math.isclose(flat[NONE], 0.5) and math.isclose(flat["A"], 0.5 / 3)


def test_non_match_favours_not_in_set() -> None:
    ev = {"classical": evidence([("B", "non_match")] * 3, 0.8, RATES, CANDS)}
    p = posterior(ev, {"classical": 1.0}, CANDS, 0.5)
    assert p[NONE] > 0.5


def test_prior_sensitivity_monotone() -> None:
    ev = {"classical": evidence([("A", "inconclusive")], 0.8, RATES, CANDS)}
    nones = [posterior(ev, {"classical": 1.0}, CANDS, q)[NONE] for q in (0.2, 0.5, 0.8)]
    assert nones == sorted(nones)


def test_mean_vs_independent_chunks() -> None:
    obs = [("A", "match")] * 5
    one = evidence(obs[:1], 0.8, RATES, CANDS)
    mean = evidence(obs, 0.8, RATES, CANDS)
    ind = evidence(obs, 0.8, RATES, CANDS, independent=True)
    assert mean == pytest.approx(one)  # identical chunks: the mean is one chunk's evidence
    assert ind["A"] == pytest.approx(5 * one["A"])


def test_chunk_loglik_pick_term() -> None:
    ll = chunk_loglik("A", "match", 0.8, RATES, CANDS)
    assert ll["A"] == pytest.approx(math.log(0.8) + math.log(0.6))
    assert ll["B"] == pytest.approx(math.log(0.1) + math.log(0.05))
    assert ll[NONE] == pytest.approx(math.log(1 / 3) + math.log(0.05))


def test_synthesise_drop_one_and_halves() -> None:
    obs = {"discovery": {"classical": [("A", "match")] * 3, "embedding": [("B", "match")] * 3},
           "confirmation": {"classical": [("A", "match")] * 3}}  # fmt: skip
    w = {"classical": 1.0, "embedding": 1.0}
    full = synthesise(obs, FAM, w, CANDS, CFG)
    no_cls = synthesise(obs, FAM, {**w, "classical": 0.0}, CANDS, CFG)
    assert set(full) == {"discovery", "confirmation", "both"}
    for r in (full, no_cls):
        for half in r.values():
            assert math.isclose(sum(half["posterior"].values()), 1.0)
            assert set(half["prior_grid"]) == {"0.2", "0.35", "0.5", "0.65", "0.8"}
    assert full["both"]["posterior"]["A"] > full["both"]["posterior"]["B"]
    # dropping the classical family leaves only the embedding, which points to B
    assert no_cls["discovery"]["posterior"]["B"] > no_cls["discovery"]["posterior"]["A"]
    assert full["discovery"]["by_family"]["embedding"]["B"] > 0.5


def test_side_by_side_reports_every_size_and_agreement() -> None:
    from synth.model import side_by_side

    def res(p: dict) -> dict:
        main = {h: {"posterior": p} for h in ("discovery", "confirmation", "both")}
        return {"hypotheses": {"primary": {"main": main}, "secondary": {"main": main}}}

    t = side_by_side({"pilot": res({"a": 0.6, "not in set": 0.4}),
                      "base": res({"a": 0.3, "not in set": 0.7})})  # fmt: skip
    row = t["primary:both"]
    assert set(row["posterior"]) == {"pilot", "base"}
    assert row["most_probable"] == {"pilot": "a", "base": "not in set"}
    assert row["sizes_agree"] is False
    same = side_by_side({"pilot": res({"a": 0.6, "b": 0.4}), "large": res({"a": 0.9, "b": 0.1})})
    assert same["secondary:discovery"]["sizes_agree"] is True
