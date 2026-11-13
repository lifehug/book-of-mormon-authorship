"""The vectorised ENSC in sweep.older equals classic.ensc.ENSC (Amendment 57, step 0)."""

import numpy as np

from classic.ensc import ENSC
from sweep.older import ensc_discriminants, ensc_fit


def test_vectorised_ensc_matches_classic() -> None:
    rng = np.random.default_rng(0)
    K, per, p = 6, 5, 12
    X = rng.random((K * per, p)) + np.repeat(rng.random((K, p)), per, axis=0)
    y = np.repeat(np.arange(K), per)
    ref = ENSC(shrinkage=0.5, alpha=0.05, priors="proportional").fit(X, y.tolist())
    f = ensc_fit(X, y, K, 0.5, "proportional")
    Q = rng.random((3, p))
    got = ensc_discriminants(f, Q)
    want = np.stack([ref.discriminants(q) for q in Q])
    assert np.allclose(got, want)
