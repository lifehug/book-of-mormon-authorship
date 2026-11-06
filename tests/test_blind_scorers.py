"""BOM-32's per-id scorers on synthetic text (no Book of Mormon, no models)."""

import random

import numpy as np

from alm.blind_score import decide, scores
from blind.thresholds import alm_scores, calibrate, call
from classic.blind_score import drop_spans, source_of
from metadata.config import load as load_config


def _author(rng: random.Random, weights: list[float], vocab: list[str], n: int) -> list[str]:
    return rng.choices(vocab, weights=weights, k=n)


def _synthetic():
    rng = random.Random(7)
    vocab = [f"w{i}" for i in range(400)]
    base = [1.0 / (i + 1) for i in range(400)]
    wa = [b * (3.0 if i % 7 == 0 else 1.0) for i, b in enumerate(base)]
    wb = [b * (3.0 if i % 5 == 0 else 1.0) for i, b in enumerate(base)]
    refs = {"cand-a": {"tokens": _author(rng, wa, vocab, 12000)},
            "cand-b": {"tokens": _author(rng, wb, vocab, 12000)}}  # fmt: skip
    pool = [_author(rng, base, vocab, 5000) for _ in range(20)]
    rows = [{"id": "x1", "text": " ".join(_author(rng, wa, vocab, 5000))},
            {"id": "x2", "text": " ".join(_author(rng, wb, vocab, 5000))}]  # fmt: skip
    return refs, pool, rows


def test_drop_spans_and_source() -> None:
    w = list("abcdefgh")
    assert drop_spans(w, [(1, 3), (5, 6)]) == list("adegh")
    assert drop_spans(w, []) == w
    assert source_of("cand:hunt_late_war") == "candidates/clean/hunt_late_war.txt"


def test_thresholds_and_calls() -> None:
    th = calibrate([0.9, 0.8, 0.95, 0.7] * 5, [0.1, 0.3, 0.2, 0.6] * 5, 0.05)
    assert th["match"] < 0.61 and th["non_match"] > 0.69
    assert call(0.99, th) == "match" and call(0.0, th) == "non_match"
    assert call(0.65, {"match": 0.7, "non_match": 0.6}) == "inconclusive"
    kinds = {"cand-a": "candidate", "cand-b": "candidate", "ctrl-x": "control"}
    recs = [{"unit": "cand-a", "margins": {"cand-a": 0.3, "cand-b": -0.1}},
            {"unit": "ctrl-x", "margins": {"cand-a": -0.2, "cand-b": 0.05}}]  # fmt: skip
    assert alm_scores(recs, kinds) == ([0.3], [-0.1, 0.05])


def test_alm_decide() -> None:
    kinds = {"cand-a": "candidate", "cand-b": "candidate", "ctrl-x": "control"}
    s = scores({"cand-a": [[1.0, 1.2]], "cand-b": [[1.5, 1.5]], "ctrl-x": [[1.4, 1.4]]},
               [[2.0, 2.0]])[0]  # fmt: skip
    assert np.isclose(s["cand-a"], -0.9)
    d = decide(s, kinds, {"match": 0.2, "non_match": -0.2})
    assert d["first_candidate"] == "cand-a" and np.isclose(d["margins"]["cand-a"], 0.3)
    assert d["call"] == {"cand-a": "match", "cand-b": "inconclusive"}


def test_classic_scorer_finds_the_author() -> None:
    from classic.blind_score import score

    refs, pool, rows = _synthetic()
    th = {"general_imposters": {"match": 0.9, "non_match": 0.2},
          "ensc": {"shrinkage": 0.5, "alpha": 0.5}}  # fmt: skip
    out = score(rows, load_config(), refs, pool, th)
    assert out["x1"]["cosine_first"] == "cand-a" and out["x2"]["cosine_first"] == "cand-b"
    assert out["x1"]["gi_first"] == "cand-a" and out["x2"]["gi_first"] == "cand-b"
    assert set(out["x1"]["gi_call"]) == {"cand-a", "cand-b"}


def test_style_scorer_with_a_stand_in_encoder() -> None:
    from style_embed.blind_score import score

    refs, pool, rows = _synthetic()

    def embed(words: list[str]) -> np.ndarray:
        v = np.zeros(400)
        for w in words:
            v[int(w[1:])] += 1
        v = np.log1p(v)
        return v / np.linalg.norm(v)

    out = score(rows, load_config(), refs, pool, {"style": {"match": 0.9, "non_match": 0.2}},
                embed=embed)  # fmt: skip
    assert out["x1"]["first"] == "cand-a" and out["x2"]["first"] == "cand-b"
    assert set(out["x2"]["call"]) == {"cand-a", "cand-b"}
