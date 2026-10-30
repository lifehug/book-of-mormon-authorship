"""Extended nearest shrunken centroids as published (BOM-57 fidelity check).

A line-by-line port of the R code in Funai (2010), *Extensions of Nearest Shrunken Centroid Method
for Classification*, MS thesis, Brigham Young University, Appendix C ("extended NSC proposed by
Schaalje et al."), which implements Schaalje, Fields, Roper and Snow (2011), *Literary and
Linguistic Computing* 26(1): 71-88, equations 2.14-2.16 of the thesis. Sources and links:
``data/benchmark/fidelity/SOURCES.md``.

It differs from ``classic/ensc.py`` (BOM-20's reconstruction, which BOM-21 validated and failed)
in how "none of the above" is decided. Here the unknown author is a class of its own, competing
in the posterior:

- class means ``xbar_ij`` and pooled within-class sd ``s_j`` (n - m degrees of freedom);
- fudge factor ``s0`` = median of ``s_j``;
- shrinkage: ``q_ij = (s_j + s0) sqrt(1/n_i + 1/n)`` (the code's sign: plus, where Tibshirani
  et al. have minus), soft-thresholded at ``shrinkage``, giving shrunken means ``c_ij``;
- for a test text ``x``: ``z_ij = (x_j - c_ij) / s_j`` (no fudge factor here; ``s_j = 0`` is
  set to 1e-6), and the latent author's ``a_j = min(max_i |z_ij|, lam)``;
- posterior of class k among the m candidates and the latent author:
  ``pi_k exp(-sum_j z_kj^2 / 2)`` normalised over all m + 1 classes, with ``pi = 1/(m + 1)``
  for every class;
- the text goes to the class with the highest posterior.

Inputs are relative word frequencies, unstandardised, as in the R code.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence

import numpy as np

LATENT = "latent"


class ENSCPublished:
    """``fit(X, y)`` then ``predict(x)``; ``shrinkage`` is the R code's ``thresh``."""

    def __init__(self, *, shrinkage: float, lam: float) -> None:
        if shrinkage < 0 or lam <= 0:
            raise ValueError("shrinkage must be >= 0 and lam > 0")
        self.shrinkage = shrinkage
        self.lam = lam

    def fit(self, X: np.ndarray, y: Sequence[Hashable]) -> ENSCPublished:
        X = np.atleast_2d(np.asarray(X, dtype=float))
        y = list(y)
        n, _ = X.shape
        classes = list(dict.fromkeys(y))  # the R code keeps the order the classes are given in
        m = len(classes)
        if m < 2 or n <= m:
            raise ValueError("need at least two classes and more texts than classes")
        idx = np.array([classes.index(v) for v in y])
        ni = np.bincount(idx, minlength=m).astype(float)
        xbar = np.vstack([X[idx == i].mean(axis=0) for i in range(m)])
        overall = xbar.mean(axis=0)  # R: the unweighted mean of the class means
        ss = np.vstack([(X[idx == i] ** 2).sum(axis=0) for i in range(m)])
        s = np.sqrt((ss - xbar**2 * ni[:, None]).sum(axis=0) / (n - m))
        s0 = float(np.median(s))
        q = (s + s0)[None, :] * np.sqrt(1.0 / ni + 1.0 / n)[:, None]
        diff = xbar - overall
        shrunk = np.maximum(np.abs(diff / q) - self.shrinkage, 0.0) * q * np.sign(diff)
        self.classes_ = classes
        self.centroids_ = overall + shrunk
        self.s_ = np.where(s == 0, 1e-6, s)
        return self

    def posteriors(self, x: np.ndarray) -> dict:
        z = (np.asarray(x, dtype=float)[None, :] - self.centroids_) / self.s_
        a = np.minimum(np.abs(z).max(axis=0), self.lam)
        log = -0.5 * np.concatenate([(z**2).sum(axis=1), [(a**2).sum()]])
        w = np.exp(log - log.max())  # equal priors cancel
        w /= w.sum()
        return dict(zip([*self.classes_, LATENT], w.tolist(), strict=True))

    def predict(self, x: np.ndarray) -> Hashable:
        post = self.posteriors(x)
        return max(post, key=post.__getitem__)
