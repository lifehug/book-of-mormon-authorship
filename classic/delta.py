"""Burrows' Delta and its variants (BOM-20; pre-registration section 5.1).

All distances take two z-scored feature vectors. Z-scores are computed per feature against
a reference set (by default the author profiles being compared), using the mean and the
sample standard deviation (ddof=1) across that set; features with zero spread get std 1
so they contribute nothing.

- Burrows' Delta (Burrows 2002): mean absolute difference of z-scores.
- Cosine Delta (Smith & Aldridge 2011; Jannidis et al. 2015): 1 - cosine similarity of the
  z-score vectors.
- Eder's Delta (Eder 2015, as in the R package ``stylo``): absolute z-differences weighted
  by feature rank, ``(1/n) * sum_i |a_i - b_i| * (n - i + 1) / n`` for i = 1..n, which
  assumes columns are in descending frequency order (as ``features.build_vocabulary``
  returns them).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

import numpy as np

Distance = Callable[[np.ndarray, np.ndarray], float]


def fit_zscore(reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per-feature mean and std (ddof=1) of a documents x features reference matrix."""
    ref = np.atleast_2d(np.asarray(reference, dtype=float))
    mean = ref.mean(axis=0)
    std = ref.std(axis=0, ddof=1) if ref.shape[0] > 1 else np.zeros(ref.shape[1])
    std = np.where(std > 0, std, 1.0)
    return mean, std


def zscore(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    return (np.asarray(x, dtype=float) - mean) / std


def burrows_delta(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(np.mean(np.abs(a - b)))


def cosine_delta(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 1.0
    return float(1.0 - np.dot(a, b) / (na * nb))


def eder_delta(a: np.ndarray, b: np.ndarray) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n = a.shape[0]
    weights = (n - np.arange(n)) / n  # rank 1 -> 1, rank n -> 1/n
    return float(np.sum(np.abs(a - b) * weights) / n)


DISTANCES: dict[str, Distance] = {
    "burrows": burrows_delta,
    "cosine": cosine_delta,
    "eder": eder_delta,
}


def get_distance(name: str) -> Distance:
    try:
        return DISTANCES[name]
    except KeyError:
        raise ValueError(f"unknown distance {name!r}; choose from {sorted(DISTANCES)}") from None


def nearest_authors(
    test_profile: np.ndarray,
    author_profiles: Mapping[str, np.ndarray],
    method: str = "burrows",
    reference: np.ndarray | None = None,
) -> list[tuple[str, float]]:
    """Rank authors by Delta distance from the test profile, nearest first.

    ``test_profile`` and each author profile are relative-frequency vectors over the same
    vocabulary. Z-scores use ``reference`` (documents x features, e.g. all training
    documents) if given, else the author profiles themselves (needs at least two).
    """
    if not author_profiles:
        raise ValueError("no author profiles")
    dist = get_distance(method)
    names = list(author_profiles)
    mat = np.vstack([np.asarray(author_profiles[n], dtype=float) for n in names])
    if reference is None:
        if len(names) < 2:
            raise ValueError("need a reference matrix or at least two author profiles")
        reference = mat
    mean, std = fit_zscore(reference)
    t = zscore(test_profile, mean, std)
    zs = zscore(mat, mean, std)
    out = [(n, dist(t, zs[i])) for i, n in enumerate(names)]
    out.sort(key=lambda p: (p[1], p[0]))
    return out
