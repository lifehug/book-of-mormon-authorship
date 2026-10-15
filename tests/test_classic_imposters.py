import numpy as np
import pytest

from classic.imposters import general_imposters
from tests.classic_toy import author_distributions, matrix, sample_text


def _setup():
    dists = author_distributions(12, seed=7)
    rng = np.random.default_rng(3)
    texts = [sample_text(p, 2000, rng) for p in dists]  # one profile per author
    test_text = sample_text(dists[0], 2000, rng)  # unseen doc by author 0
    X, vocab = matrix(texts + [test_text])
    return X[-1], X[0], X[1], X[2:-1]


@pytest.mark.parametrize("distance", ["cosine", "delta", "cosine_delta"])
def test_gi_true_author_high_non_author_low(distance: str) -> None:
    test, true_author, non_author, pool = _setup()
    kw = dict(feature_fraction=0.5, n_imposters=8, trials=200, distance=distance, seed=11)
    assert general_imposters(test, true_author, pool, **kw) >= 0.9
    assert general_imposters(test, non_author, pool, **kw) <= 0.1


def test_gi_is_seeded_and_validates() -> None:
    test, cand, _, pool = _setup()
    a = general_imposters(test, cand, pool, trials=50, seed=5, feature_fraction=0.1)
    b = general_imposters(test, cand, pool, trials=50, seed=5, feature_fraction=0.1)
    assert a == b and 0.0 <= a <= 1.0
    with pytest.raises(ValueError):
        general_imposters(test, cand, pool, feature_fraction=0.0)
    with pytest.raises(ValueError):
        general_imposters(test, cand, pool, n_imposters=pool.shape[0] + 1)
    with pytest.raises(ValueError):
        general_imposters(test, cand, pool, distance="manhattan")
    with pytest.raises(ValueError):
        general_imposters(test[:-1], cand, pool)
