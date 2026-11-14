"""Per-episode scoring of the sweep (BOM-89 step 2)."""

import numpy as np

from sweep.episodes import padded, rank, topk_scores


def test_topk_finds_an_author_by_their_closest_episodes() -> None:
    rng = np.random.default_rng(0)
    unit = lambda x: x / np.linalg.norm(x, axis=-1, keepdims=True)  # noqa: E731
    q = unit(rng.normal(size=(1, 16)))
    far = [unit(rng.normal(size=(5, 16))) for _ in range(6)]
    # the true author: mostly unlike the query, two episodes like it
    true = np.concatenate(
        [unit(rng.normal(size=(6, 16))), unit(q + 0.05 * rng.normal(size=(2, 16)))]
    )
    G, M = padded([*far, true])
    assert G.shape == (7, 8, 16) and M.sum() == 6 * 5 + 8
    s = topk_scores(q, G, M, [1, 2])
    every = np.ones(7, dtype=bool)
    assert rank(s[1], 6, every) == 1 and rank(s[2], 6, every) == 1
    short = topk_scores(q, *padded([q, far[0]]), [3])[3]  # one episode: scored on that one
    assert np.isclose(short[0], 1.0, atol=1e-5)


def test_rank_ignores_dropped_authors_but_keeps_the_true_one() -> None:
    s = np.array([0.9, 0.8, 0.5, 0.7])
    assert rank(s, 2, np.ones(4, dtype=bool)) == 4
    assert rank(s, 2, np.array([False, True, False, False])) == 2
