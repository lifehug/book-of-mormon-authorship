"""Sichel's distribution for vocabulary spectra, fitted as Holmes (1992) did (BOM-22).

Sichel (1975), with the Bessel order fixed at -1/2: the probability that a word type occurs
exactly ``r`` times (``r >= 1``) is proportional to ``(alpha theta / 2)^r / r! K_{r-1/2}(alpha)``,
``alpha > 0``, ``0 < theta < 1`` (Holmes 1992, section 2.4; normalised here numerically over
``r``, which is the same zero-truncated distribution). Holmes fits ``alpha`` and ``theta`` by
minimising chi-square between the observed and expected spectrum, and converts them to
"10,000-equivalent" values through Sichel's invariants ``b = alpha sqrt(1 - theta)`` and
``c = theta / ((1 - theta) N)``, which do not change with text length ``N``.

Holmes applies it to the spectrum of nouns: ``V_r``, the number of noun types used ``r`` times,
for ``r = 1..15`` and ``r > 15`` (his Tables 3-4). Cells are pooled from the tail until every
expected count is at least ``MIN_EXPECTED``, the usual rule for chi-square, which reproduces
his degrees of freedom.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

MAX_R = 200000  # hard stop on terms summed; in practice the sum stops far earlier
TOL = 1e-15  # stop once a term is this small relative to the largest
MIN_EXPECTED = 5.0


def _terms(alpha: float, theta: float) -> np.ndarray:
    """Unnormalised ``(alpha theta / 2)^r / r! K_{r-1/2}(alpha)``, r = 1, 2, ..., by the
    recurrence ``K_{v+1} = K_{v-1} + (2v/alpha) K_v`` on the ratio ``q_r = K_{r+1/2}/K_{r-1/2}``
    (``q_0 = 1``, since ``K_{1/2} = K_{-1/2}``), which is exact and avoids high-order Bessel calls.
    """
    x = alpha * theta / 2.0
    out = [x * 1.0]  # r = 1: x^1 / 1! * K_{1/2}, with K_{1/2} taken as 1 (cancels on normalising)
    q = 1.0
    peak = out[0]
    r = 1
    while r < MAX_R:
        q = 1.0 / q + (2 * r - 1) / alpha  # q_r = K_{r+1/2} / K_{r-1/2}
        r += 1
        out.append(out[-1] * x / r * q)
        peak = max(peak, out[-1])
        if out[-1] < TOL * peak and r > 50:
            break
    return np.array(out)


def pmf(alpha: float, theta: float, top: int) -> np.ndarray:
    """P(r) for r = 1..top, and as the last element P(r > top)."""
    w = _terms(alpha, theta)
    w = w / w.sum()
    if len(w) <= top:
        w = np.concatenate([w, np.zeros(top + 1 - len(w))])
    return np.concatenate([w[:top], [w[top:].sum()]])


def _cells(observed: np.ndarray, expected: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    o, e = list(observed), list(expected)
    while len(e) > 2 and e[-1] < MIN_EXPECTED:  # pool the tail
        e[-2] += e.pop()
        o[-2] += o.pop()
    return np.array(o, dtype=float), np.array(e, dtype=float)


def chi_square(spectrum: list[int], tail: int, alpha: float, theta: float) -> tuple[float, int]:
    """Chi-square and degrees of freedom for ``spectrum`` (V_1..V_top) plus ``tail`` (V_{>top})."""
    observed = np.array([*spectrum, tail], dtype=float)
    expected = observed.sum() * pmf(alpha, theta, len(spectrum))
    o, e = _cells(observed, expected)
    return float(((o - e) ** 2 / e).sum()), len(o) - 3


def fit(spectrum: list[int], tail: int) -> dict:
    """Minimum chi-square ``alpha`` and ``theta`` (Holmes 1992)."""

    def loss(p: np.ndarray) -> float:
        alpha, theta = np.exp(p[0]), 1.0 / (1.0 + np.exp(-p[1]))
        return chi_square(spectrum, tail, alpha, theta)[0]

    best = None
    for a0 in (0.3, 1.0, 3.0):
        for t0 in (0.9, 0.97, 0.995):
            res = minimize(loss, [np.log(a0), np.log(t0 / (1 - t0))], method="Nelder-Mead",
                           options={"xatol": 1e-9, "fatol": 1e-9, "maxiter": 4000})  # fmt: skip
            if best is None or res.fun < best.fun:
                best = res
    alpha, theta = float(np.exp(best.x[0])), float(1.0 / (1.0 + np.exp(-best.x[1])))
    chi2, dof = chi_square(spectrum, tail, alpha, theta)
    return {"alpha": alpha, "theta": theta, "chi2": chi2, "dof": dof}


def equivalent(alpha: float, theta: float, n: int, target: int = 10000) -> tuple[float, float]:
    """``alpha`` and ``theta`` for a text of ``target`` tokens, through Sichel's invariants."""
    b = alpha * np.sqrt(1.0 - theta)
    c = theta / ((1.0 - theta) * n)
    t = c * target / (1.0 + c * target)
    return float(b / np.sqrt(1.0 - t)), float(t)
