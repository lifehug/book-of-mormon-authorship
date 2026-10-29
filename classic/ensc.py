"""Nearest shrunken centroids with an open-set "none of the above" rule (BOM-20).

Closed-set part: Tibshirani, Hastie, Narasimhan & Chu (2002), "Diagnosis of multiple cancer
types by shrunken centroids of gene expression", PNAS 99(10):6567-6572. Open-set extension
after Fields, Schaalje & Roper (2011), "Extended nearest shrunken centroid classification: a
new method for open-set authorship attribution of texts of varying sizes", Literary and
Linguistic Computing 26(1):71-88.

Fit, on a documents x features matrix X with class labels (n documents, K classes):

- class centroids ``c_k``, overall centroid ``c``;
- pooled within-class standard deviation ``s_i = sqrt(sum_k sum_{j in k} (x_ij - c_ki)^2
  / (n - K))`` and ``s0 = median(s_i)``;
- ``m_k = sqrt(1/n_k - 1/n)``, ``d_ki = (c_ki - c_i) / (m_k (s_i + s0))``;
- soft threshold ``d'_ki = sign(d_ki) (|d_ki| - shrinkage)_+``;
- shrunken centroid ``c'_ki = c_i + m_k (s_i + s0) d'_ki``.

Closed-set classification (Tibshirani et al. eq. 4-5): discriminant
``delta_k(x) = sum_i (x_i - c'_ki)^2 / (s_i + s0)^2 - 2 log pi_k`` and posterior
``p_k = exp(-delta_k / 2) / sum_l exp(-delta_l / 2)``. Priors ``pi_k`` default to class
proportions; pass ``priors="uniform"`` for equal priors.

Open-set rule (this module's exact implementation). For each class, the test document's
standardized squared distance to that class's (unshrunken) centroid is

    D_k(x) = [sum over features i with s_i > 0 of (x_i - c_ki)^2 / s_i^2] / (1 + 1/n_k)

The factor ``1 + 1/n_k`` is the predictive-variance correction for a centroid estimated
from ``n_k`` documents. Under the model that a class-k document's features are independent
normals around the class mean with within-class variance ``s_i^2``, ``D_k`` is
approximately chi-squared with p degrees of freedom (p = number of features with
``s_i > 0``). The class *likelihood* is the upper-tail probability
``L_k = P(chi2_p >= D_k(x))``. If ``max_k L_k < alpha`` the document is assigned ``NONE``
("none of the above"); otherwise it gets the class with the highest closed-set posterior.

``alpha`` is the open-set threshold. On toy multinomial data the chi-squared reference is
anti-conservative (true-class likelihoods have a heavier lower tail than uniform, because
features are correlated and ``s_i`` is estimated), so ``alpha`` must be calibrated on the
benchmark (BOM-21) rather than read as a nominal p-value.

Choices that differ from, or go beyond, what we can confirm of Fields et al. (2011), to be
checked during the BOM-22 replication: the open-set statistic uses unshrunken centroids and
unregularized ``s_i`` (shrunken centroids are biased toward the overall mean, which made
true-class documents fail the test as shrinkage grew); it ignores feature correlation; and
it works on relative frequencies without the paper's explicit modelling of text length
(their "texts of varying sizes" extension). The shrinkage amount is a parameter; Tibshirani
et al. choose it by cross-validation, which belongs to the benchmark stage.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2

NONE = "none"


@dataclass
class ENSCResult:
    label: Hashable
    posteriors: dict
    likelihoods: dict


class ENSC:
    """Extended nearest shrunken centroids. ``fit(X, y)`` then ``predict(x)``."""

    def __init__(self, *, shrinkage: float, alpha: float, priors: str) -> None:
        """All three are required (BOM-40): shrinkage is selected on the benchmark (Amendment 2),
        alpha and priors come from ``config.classic.ensc``."""
        if shrinkage < 0:
            raise ValueError("shrinkage must be >= 0")
        if not 0.0 <= alpha < 1.0:
            raise ValueError("alpha must be in [0, 1)")
        if priors not in ("proportional", "uniform"):
            raise ValueError("priors must be 'proportional' or 'uniform'")
        self.shrinkage = shrinkage
        self.alpha = alpha
        self.priors = priors

    def fit(self, X: np.ndarray, y: Sequence[Hashable]) -> ENSC:
        X = np.atleast_2d(np.asarray(X, dtype=float))
        y = list(y)
        n, p = X.shape
        if len(y) != n:
            raise ValueError("X and y lengths differ")
        classes = sorted(set(y), key=str)
        K = len(classes)
        if K < 2:
            raise ValueError("need at least two classes")
        if n <= K:
            raise ValueError("need more documents than classes to pool within-class variance")
        yarr = np.array([classes.index(v) for v in y])
        counts = np.bincount(yarr, minlength=K).astype(float)
        centroids = np.vstack([X[yarr == k].mean(axis=0) for k in range(K)])
        overall = X.mean(axis=0)
        resid = X - centroids[yarr]
        s = np.sqrt((resid**2).sum(axis=0) / (n - K))
        s0 = float(np.median(s))
        if s0 == 0:
            s0 = float(s[s > 0].mean()) if np.any(s > 0) else 1.0
        m = np.sqrt(1.0 / counts - 1.0 / n)
        scale = m[:, None] * (s + s0)[None, :]
        d = (centroids - overall) / scale
        d_shrunk = np.sign(d) * np.maximum(np.abs(d) - self.shrinkage, 0.0)
        self.classes_ = classes
        self.class_counts_ = counts
        self.centroids_ = centroids
        self.overall_ = overall
        self.s_ = s
        self.s0_ = s0
        self.d_shrunk_ = d_shrunk
        self.shrunken_centroids_ = overall + scale * d_shrunk
        if self.priors == "uniform":
            self.prior_ = np.full(K, 1.0 / K)
        else:
            self.prior_ = counts / n
        self.active_features_ = np.flatnonzero(np.any(d_shrunk != 0, axis=0))
        return self

    def discriminants(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        sd = self.s_ + self.s0_
        dist = (((x[None, :] - self.shrunken_centroids_) / sd) ** 2).sum(axis=1)
        return dist - 2.0 * np.log(self.prior_)

    def posteriors(self, x: np.ndarray) -> dict:
        delta = self.discriminants(x)
        z = -0.5 * (delta - delta.min())
        w = np.exp(z)
        w /= w.sum()
        return dict(zip(self.classes_, w.tolist(), strict=True))

    def likelihoods(self, x: np.ndarray) -> dict:
        """Open-set class likelihoods ``L_k = P(chi2_p >= D_k(x))`` (see module docstring)."""
        x = np.asarray(x, dtype=float)
        keep = self.s_ > 0
        dof = int(keep.sum())
        if dof == 0:
            return dict.fromkeys(self.classes_, 1.0)
        diff = (x[None, keep] - self.centroids_[:, keep]) / self.s_[keep]
        D = (diff**2).sum(axis=1) / (1.0 + 1.0 / self.class_counts_)
        return dict(zip(self.classes_, chi2.sf(D, dof).tolist(), strict=True))

    def classify(self, x: np.ndarray) -> ENSCResult:
        post = self.posteriors(x)
        lik = self.likelihoods(x)
        if max(lik.values()) < self.alpha:
            label: Hashable = NONE
        else:
            label = max(post, key=post.__getitem__)
        return ENSCResult(label=label, posteriors=post, likelihoods=lik)

    def predict(self, x: np.ndarray) -> Hashable:
        return self.classify(x).label
