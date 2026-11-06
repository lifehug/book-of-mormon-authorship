"""The prior-work table's statistics (BOM-68)."""

import numpy as np

from eval.prior_work import _flat, bootstrap, mcnemar


def test_bootstrap_interval_brackets_accuracy() -> None:
    c = np.array([True] * 90 + [False] * 10)
    lo, hi = bootstrap(c, 2000, 1)
    assert lo < 0.9 < hi and 0.8 < lo and hi < 0.97
    assert bootstrap(np.ones(50, dtype=bool), 500, 2) == [1.0, 1.0]
    assert bootstrap(c, 500, 3) == bootstrap(c, 500, 3)  # seeded


def test_mcnemar_counts_discordant_pairs() -> None:
    a = np.array([True, True, True, False, True, True])
    b = np.array([True, False, False, False, False, True])
    r = mcnemar(a, b)
    assert (r["only_first"], r["only_second"]) == (3, 0)
    assert np.isclose(r["p"], 0.25)  # exact binomial, 3 of 3 discordant
    assert mcnemar(a, a) == {"only_first": 0, "only_second": 0, "p": 1.0}


def test_flat_keys_pair_tests_in_order() -> None:
    k1, c1 = _flat({"b": [("x", True)], "a": [("y", False), ("z", True)]})
    k2, _ = _flat({"a": [("y", True), ("z", True)], "b": [("x", False)]})
    assert k1 == k2 == ["a:0:y", "a:1:z", "b:0:x"]
    assert c1.tolist() == [False, True, True]


def test_by_size_side_by_side() -> None:
    from eval.prior_work import by_size, size_of

    assert size_of("alm_large_v1") == ("large", "v1")
    assert size_of("alm_base") == ("base", "primary")
    assert size_of("alm_candidates_base") is None and size_of("style_embed") is None
    r = {"closed_set": 0.9, "closed_set_95": None, "open_set_fpr": 0.2, "passes": False,
         "test_set": "tails"}  # fmt: skip
    t = by_size({"alm_large": r, "alm_pilot": r, "alm_base_v2": r, "general_imposters": r})
    assert list(t) == ["primary", "v2"] and list(t["primary"]) == ["pilot", "large"]


def test_records_reads_classic_tails(tmp_path, monkeypatch) -> None:
    import json

    import eval.prior_work as pw

    trial = {"author": "A", "burrows_delta": "A", "cosine_delta": "B", "general_imposters": "A"}
    (tmp_path / "benchmark.json").write_text(json.dumps({"records": {"t": [trial]}}))
    tail = {**trial, "where": "blocks 1-5 of 9", "ensc": "A"}
    (tmp_path / "prior_work_classic_tails.json").write_text(json.dumps({"records": {"t": [tail]}}))
    (tmp_path / "alm_base.json").write_text(json.dumps({"records": {"t": [
        {"author": "A", "predicted": "B", "where": "blocks 1-5 of 9"}]}}))  # fmt: skip
    monkeypatch.setattr(pw, "DIR", tmp_path)
    recs = pw.records()
    assert recs["tails_ensc"] == ("tails", {"t": [("A", True)]})
    assert recs["tails_cosine_delta"][1]["t"] == [("A", False)]
    assert recs["alm_base"][0] == "tails"
    assert pw._flat(recs["tails_burrows_delta"][1])[0] == pw._flat(recs["alm_base"][1])[0]
