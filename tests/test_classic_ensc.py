import numpy as np
import pytest

from classic.ensc import ENSC, NONE
from tests.classic_toy import author_distributions, corpus, matrix, sample_text


def _fit(shrinkage=0.5, alpha=1e-4):
    dists, texts, labels, rng = corpus(n_authors=4, docs_per_author=6, n_tokens=1500)
    X, vocab = matrix(texts)
    model = ENSC(shrinkage=shrinkage, alpha=alpha).fit(X, labels)
    return model, dists, vocab, rng


def test_ensc_classifies_known_authors() -> None:
    model, dists, vocab, rng = _fit()
    for a, p in enumerate(dists):
        x, _ = matrix([sample_text(p, 1500, rng)], vocab)
        res = model.classify(x[0])
        assert res.label == f"A{a}"
        assert res.posteriors[f"A{a}"] > 0.99
        assert res.likelihoods[f"A{a}"] >= model.alpha
        assert sum(res.posteriors.values()) == pytest.approx(1.0)


def test_ensc_returns_none_far_from_all_classes() -> None:
    model, _, vocab, rng = _fit()
    outsider = author_distributions(9, seed=99)[8]  # an author not in training
    x, _ = matrix([sample_text(outsider, 1500, rng)], vocab)
    res = model.classify(x[0])
    assert res.label == NONE
    assert max(res.likelihoods.values()) < model.alpha
    # the closed-set posterior still names someone; only the open-set rule rejects
    assert max(res.posteriors.values()) > 0


def test_shrinkage_zeroes_features() -> None:
    dists, texts, labels, _ = corpus(n_authors=3, docs_per_author=4)
    X, _ = matrix(texts)
    none = ENSC(shrinkage=0.0).fit(X, labels)
    big = ENSC(shrinkage=1e6).fit(X, labels)
    assert len(none.active_features_) == X.shape[1]
    assert len(big.active_features_) == 0
    np.testing.assert_allclose(big.shrunken_centroids_, np.tile(X.mean(axis=0), (3, 1)))


def test_ensc_validation() -> None:
    X = np.eye(3)
    with pytest.raises(ValueError):
        ENSC().fit(X, ["a", "a", "a"])
    with pytest.raises(ValueError):
        ENSC().fit(X[:2], ["a", "b"])
    with pytest.raises(ValueError):
        ENSC(shrinkage=-1)
    with pytest.raises(ValueError):
        ENSC(priors="flat")
    m = ENSC(priors="uniform").fit(np.array([[0.0], [0.1], [1.0], [1.1]]), list("aabb"))
    np.testing.assert_allclose(m.prior_, [0.5, 0.5])
