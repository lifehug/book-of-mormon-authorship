"""General Imposters verification (BOM-20; pre-registration sections 5.1 and 6.1).

Koppel & Winter (2014), "Determining if two documents are written by the same author",
JASIST 65(1); as adapted by Kestemont, Stover, Koppel, Karsdorp & Daelemans (2016),
"Authenticating the writings of Julius Caesar", Expert Systems with Applications 63.

For a test document and a candidate author, each trial:

1. samples ``feature_fraction`` of the feature columns at random (without replacement);
2. samples ``n_imposters`` imposter profiles at random (without replacement) from the pool;
3. computes the distance from the test document to the candidate and to each sampled
   imposter on the sampled features only;
4. scores a win if the candidate is strictly nearer than every sampled imposter.

The returned score is wins / trials, in [0, 1]. Pre-registration 6.1 uses this proportion
as the verification score passed to ``classic.decide``.

Distances:

- ``"cosine"``: cosine distance on the raw relative-frequency vectors (Koppel & Winter's
  choice);
- ``"delta"``: Burrows' Delta on z-scores, with mean and std fit once on the candidate plus
  the full imposter pool (never the test document) before any sampling;
- ``"cosine_delta"``: cosine distance on those same z-scores.
"""

from __future__ import annotations

import numpy as np

from classic.delta import burrows_delta, cosine_delta, fit_zscore, zscore

DISTANCE_CHOICES = ("cosine", "delta", "cosine_delta")


def general_imposters(
    test: np.ndarray,
    candidate: np.ndarray,
    imposters: np.ndarray,
    *,
    feature_fraction: float = 0.5,
    n_imposters: int | None = None,
    trials: int = 100,
    distance: str = "cosine",
    seed: int | None = 0,
) -> float:
    """Proportion of trials in which ``candidate`` beats every sampled imposter.

    ``test`` and ``candidate`` are 1-D feature vectors; ``imposters`` is an
    (n_pool x features) matrix. ``n_imposters`` defaults to half the pool (at least 1).
    """
    test = np.asarray(test, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    pool = np.atleast_2d(np.asarray(imposters, dtype=float))
    n_feat = test.shape[0]
    if candidate.shape != test.shape or pool.shape[1] != n_feat:
        raise ValueError("test, candidate, and imposters must share the feature dimension")
    if not 0.0 < feature_fraction <= 1.0:
        raise ValueError("feature_fraction must be in (0, 1]")
    if trials < 1:
        raise ValueError("trials must be >= 1")
    if distance not in DISTANCE_CHOICES:
        raise ValueError(f"distance must be one of {DISTANCE_CHOICES}")
    n_pool = pool.shape[0]
    if n_pool < 1:
        raise ValueError("need at least one imposter")
    k = max(1, n_pool // 2) if n_imposters is None else n_imposters
    if not 1 <= k <= n_pool:
        raise ValueError(f"n_imposters must be in [1, {n_pool}]")
    m = max(1, int(round(feature_fraction * n_feat)))

    if distance == "cosine":
        t, c, p = test, candidate, pool
        dist = cosine_delta
    else:
        mean, std = fit_zscore(np.vstack([candidate, pool]))
        t, c, p = zscore(test, mean, std), zscore(candidate, mean, std), zscore(pool, mean, std)
        dist = burrows_delta if distance == "delta" else cosine_delta

    rng = np.random.default_rng(seed)
    wins = 0
    for _ in range(trials):
        feats = rng.choice(n_feat, size=m, replace=False)
        imps = rng.choice(n_pool, size=k, replace=False)
        tf = t[feats]
        d_c = dist(tf, c[feats])
        d_i = min(dist(tf, p[j, feats]) for j in imps)
        if d_c < d_i:
            wins += 1
    return wins / trials
