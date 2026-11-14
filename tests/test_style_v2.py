"""The second style encoder's splits, work genres and pair rule (BOM-89 step 3)."""

import numpy as np

from metadata.config import load
from style_embed.v2 import Episodes, splits, work_genre


def test_heldout_stays_heldout() -> None:
    first = {f"a{i}": "heldout" if i % 10 == 0 else "train" for i in range(2000)}
    got = splits(first, 7, 0.05)
    assert all(got[a] == "heldout" for a, s in first.items() if s == "heldout")
    val = sum(v == "validation" for v in got.values())
    assert 40 < val < 150 and not any(got[a] == "validation" for a in first if first[a] != "train")


def test_work_genre_ignores_uncertain() -> None:
    g = {"v1": "uncertain", "v2": "fiction_narrative", "v3": "uncertain"}
    assert work_genre(["v1", "v2", "v3"], g) == "fiction_narrative"
    assert work_genre(["v1", "zz"], g) == "uncertain"


def test_hard_steps_are_one_genre_with_positives_from_another() -> None:
    cfg = load()
    cfg = {**cfg, "style_embed_v2": {**cfg["style_embed_v2"], "hard_step_share": 1.0}}
    p, t = cfg["style_embed"]["episode_passages"], cfg["style_embed"]["passage_tokens"]
    works, index, n = [], {"author": [], "work": []}, 0
    for a in range(12):
        for w, g in (
            ("s", "sermon_devotional"),
            ("h", "history_chronicle"),
            ("s2", "sermon_devotional"),
        ):
            works.append({"author": f"a{a}", "split": "train", "work": w, "genre": g})
            index["author"] += [f"a{a}"] * p
            index["work"] += [w] * p
            n += p
    eps = Episodes(cfg, np.zeros(n * t, dtype=np.uint16), index, works)
    for step in range(5):
        pairs = eps.pairs("train", 8, step)
        assert len({a for a, _, _ in pairs}) == 8
        first = {eps.pool["train"][a][w1][0] for a, w1, _ in pairs}
        assert len(first) == 1  # the batch's genre
        assert all(eps.pool["train"][a][w2][0] not in first for a, _, w2 in pairs)
    assert eps.draw("train", 8, 0).shape == (16, p, t)
