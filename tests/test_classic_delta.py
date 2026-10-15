import numpy as np
import pytest

from classic.delta import (
    burrows_delta,
    cosine_delta,
    eder_delta,
    fit_zscore,
    get_distance,
    nearest_authors,
    zscore,
)
from tests.classic_toy import corpus, matrix


def test_distance_formulas() -> None:
    a = np.array([1.0, 0.0, -1.0])
    b = np.array([0.0, 0.0, 1.0])
    assert burrows_delta(a, b) == pytest.approx(1.0)
    assert cosine_delta(a, a) == pytest.approx(0.0)
    assert cosine_delta(a, -a) == pytest.approx(2.0)
    assert cosine_delta(np.zeros(3), a) == 1.0
    # weights 3/3, 2/3, 1/3; diffs 1, 0, 2 -> (1 + 0 + 2/3) / 3
    assert eder_delta(a, b) == pytest.approx((1 + 2 / 3) / 3)
    with pytest.raises(ValueError):
        get_distance("manhattan")


def test_zscore_handles_constant_features() -> None:
    ref = np.array([[1.0, 5.0], [3.0, 5.0]])
    mean, std = fit_zscore(ref)
    np.testing.assert_allclose(mean, [2.0, 5.0])
    assert std[1] == 1.0
    np.testing.assert_allclose(zscore(ref, mean, std)[:, 1], [0.0, 0.0])


@pytest.mark.parametrize("method", ["burrows", "cosine", "eder"])
def test_delta_recovers_author(method: str) -> None:
    _, texts, labels, _ = corpus(n_authors=5, docs_per_author=4, n_tokens=1500)
    X, vocab = matrix(texts)
    labels = np.array(labels)
    correct = 0
    for i in range(len(texts)):
        train = np.arange(len(texts)) != i
        profiles = {a: X[train & (labels == a)].mean(axis=0) for a in sorted(set(labels.tolist()))}
        ranked = nearest_authors(X[i], profiles, method=method, reference=X[train])
        correct += ranked[0][0] == labels[i]
        assert len(ranked) == 5 and ranked[0][1] <= ranked[-1][1]
    assert correct == len(texts)


def test_nearest_authors_needs_reference() -> None:
    with pytest.raises(ValueError):
        nearest_authors(np.ones(3), {"a": np.ones(3)})
    with pytest.raises(ValueError):
        nearest_authors(np.ones(3), {})
