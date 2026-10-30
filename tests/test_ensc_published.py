import numpy as np

from classic.ensc_published import LATENT, ENSCPublished


def _data(rng: np.random.Generator) -> tuple[np.ndarray, list[str]]:
    a = rng.normal(0.0, 1.0, size=(20, 8))
    b = rng.normal(3.0, 1.0, size=(20, 8))
    return np.vstack([a, b]), ["a"] * 20 + ["b"] * 20


def test_known_class_and_latent() -> None:
    rng = np.random.default_rng(0)
    X, y = _data(rng)
    m = ENSCPublished(shrinkage=0.0, lam=3.0).fit(X, y)
    assert m.predict(np.zeros(8)) == "a"
    assert m.predict(np.full(8, 3.0)) == "b"
    assert m.predict(np.full(8, 40.0)) == LATENT  # far from both: the capped latent term wins


def test_posteriors_sum_to_one_with_latent() -> None:
    rng = np.random.default_rng(1)
    X, y = _data(rng)
    post = ENSCPublished(shrinkage=1.0, lam=2.0).fit(X, y).posteriors(np.ones(8))
    assert set(post) == {"a", "b", LATENT}
    assert abs(sum(post.values()) - 1.0) < 1e-9
