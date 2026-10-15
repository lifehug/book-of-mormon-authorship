"""Score-to-decision mapping for attribution (BOM-20; pre-registration section 6.1).

A method returns *match* for a candidate when its verification score exceeds the threshold
calibrated on the open-set benchmark at a 5% false-positive rate, *non-match* when the score
falls below the threshold calibrated at a 5% false-negative rate, and *inconclusive* in
between.

``calibrate`` takes benchmark scores for true-author pairs (same) and wrong-author pairs
(different):

- match threshold = the (1 - fpr) quantile of the different-author scores, so at most
  ``fpr`` of wrong authors score strictly above it;
- non-match threshold = the ``fnr`` quantile of the same-author scores, so at most ``fnr``
  of true authors score strictly below it.

Quantiles use numpy's ``"higher"`` / ``"lower"`` methods respectively, i.e. actual observed
scores, erring toward fewer matches and fewer non-matches.

``decide`` is strict: ``score > match`` is a match, ``score < non_match`` is a non-match.
When the two distributions barely overlap, the calibrated non-match threshold can lie above
the match threshold; a score that then satisfies both rules is reported *inconclusive*,
because the two calibrated rules disagree. For scores where lower means more similar (a
distance), set ``higher_is_match=False``; the comparisons are mirrored.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

MATCH = "match"
NON_MATCH = "non-match"
INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class Thresholds:
    match: float
    non_match: float
    higher_is_match: bool = True


def decide(score: float, thresholds: Thresholds) -> str:
    """Map one verification score to match / non-match / inconclusive."""
    if score is None or not np.isfinite(score):
        raise ValueError(f"score must be a finite number, got {score!r}")
    sign = 1.0 if thresholds.higher_is_match else -1.0
    s = sign * score
    is_match = s > sign * thresholds.match
    is_non = s < sign * thresholds.non_match
    if is_match and not is_non:
        return MATCH
    if is_non and not is_match:
        return NON_MATCH
    return INCONCLUSIVE


def calibrate(
    same_author_scores: Sequence[float],
    different_author_scores: Sequence[float],
    fpr: float = 0.05,
    fnr: float = 0.05,
    higher_is_match: bool = True,
) -> Thresholds:
    """Thresholds at the given false-positive and false-negative rates (see module doc)."""
    same = np.asarray(same_author_scores, dtype=float)
    diff = np.asarray(different_author_scores, dtype=float)
    if same.size == 0 or diff.size == 0:
        raise ValueError("need both same-author and different-author scores")
    if not (0 < fpr < 1 and 0 < fnr < 1):
        raise ValueError("fpr and fnr must be in (0, 1)")
    if higher_is_match:
        match = float(np.quantile(diff, 1 - fpr, method="higher"))
        non = float(np.quantile(same, fnr, method="lower"))
    else:
        match = float(np.quantile(diff, fpr, method="lower"))
        non = float(np.quantile(same, 1 - fnr, method="higher"))
    return Thresholds(match=match, non_match=non, higher_is_match=higher_is_match)
