"""The shared pool's equal-dose slices (BOM-94)."""

from eval.library_pool import slices


def test_slices_spread_evenly_and_never_overrun() -> None:
    assert slices(26000, 3039, 3) == [0, 11480, 22961]
    assert slices(3039, 3039, 3) == [0] and slices(3000, 3039, 3) == []
    assert slices(10000, 3039, 1) == [3480]
    assert all(s + 3039 <= 4000 for s in slices(4000, 3039, 3))


def test_in_top_is_exact_for_the_whole_pool_and_for_pairs() -> None:
    import numpy as np

    from eval.library_pool import in_top, scaled

    better = np.array([0, 1, 5])
    assert in_top(better, 99, 100, 1).tolist() == [1.0, 0.0, 0.0]  # the whole pool
    assert np.allclose(in_top(better, 99, 2, 1), [1, 98 / 99, 94 / 99])  # one random rival
    assert (
        in_top(np.array([5]), 99, 100, 10)[0] == 1.0 and in_top(np.array([5]), 99, 2000, 5)[0] == 0
    )
    X = np.random.default_rng(0).normal(size=(400, 3)) + np.array([0.0, 5.0, -5.0])
    Z = scaled(X, np.array([0, 1] * 200, dtype=bool))
    assert np.abs(Z.mean(axis=0)).max() < 0.2 and np.abs(Z.std(axis=0) - 1).max() < 0.2
