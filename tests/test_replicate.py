"""BOM-22: the replication helpers, on synthetic authors (no Book of Mormon text)."""

import random

from eval import replicate as R


def _author(vocab_bias: str, n_docs: int, rng: random.Random) -> list[tuple[str, list[str]]]:
    """Both synthetic authors use every word; they differ only in how often."""
    base = "the and of to a in that it for be upon whereby".split()
    return [(f"{vocab_bias}{i}", [rng.choice(base + [vocab_bias] * 3) for _ in range(800)])
            for i in range(n_docs)]  # fmt: skip


def test_chunks_cover_everything():
    toks = list(range(10_005))
    parts = R._chunks(toks, 2000)
    assert sum(len(p) for p in parts) == len(toks) and len(parts) == 5


def test_jockers_methods_rank_the_true_author_first():
    rng = random.Random(1)
    known = {"x": _author("upon", 12, rng), "y": _author("whereby", 12, rng)}
    tests = [t for _, t in _author("upon", 3, rng)] + [t for _, t in _author("whereby", 3, rng)]
    feats = R.jockers_features(known, tests)
    assert "upon" in feats and "whereby" in feats
    out = R.jockers_methods(known, tests, feats, [0.0, 1.0], seed=0)
    firsts = [r["nsc"][0] for r in out["chapters"]]
    assert firsts == ["x", "x", "x", "y", "y", "y"]
    assert [r["delta"][0] for r in out["chapters"]] == firsts


def test_manova_separates_different_groups_not_identical_ones():
    import numpy as np

    rng = np.random.default_rng(0)
    same = {g: rng.normal(0, 1, size=(30, 3)) for g in "abc"}
    diff = {"a": rng.normal(0, 1, size=(30, 3)), "b": rng.normal(2, 1, size=(30, 3))}
    assert R.manova(same)["p_value"] > 0.01
    assert R.manova(diff)["p_value"] < 1e-6


def test_richness_measures():
    toks = "a a b c c c d".split()  # V=4, V1=2 (b, d), V2=1 (a)
    r = R.richness(toks)
    assert abs(r["v2_over_v"] - 0.25) < 1e-12
    # Yule's K: 1e4 * (sum i^2 V_i - N) / N^2 = 1e4 * (1*2 + 4*1 + 9*1 - 7) / 49
    assert abs(r["yule_k"] - 1e4 * 8 / 49) < 1e-9
