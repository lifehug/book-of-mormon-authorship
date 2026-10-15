import pytest

from classic.decide import INCONCLUSIVE, MATCH, NON_MATCH, Thresholds, calibrate, decide


def test_decide_three_way() -> None:
    th = Thresholds(match=0.8, non_match=0.3)
    assert decide(0.9, th) == MATCH
    assert decide(0.1, th) == NON_MATCH
    assert decide(0.5, th) == INCONCLUSIVE
    assert decide(0.8, th) == INCONCLUSIVE  # strict
    assert decide(0.3, th) == INCONCLUSIVE


def test_decide_lower_is_match() -> None:
    th = Thresholds(match=0.2, non_match=0.6, higher_is_match=False)
    assert decide(0.1, th) == MATCH
    assert decide(0.7, th) == NON_MATCH
    assert decide(0.4, th) == INCONCLUSIVE


def test_crossed_thresholds_conflict_is_inconclusive() -> None:
    th = Thresholds(match=0.6, non_match=0.8)
    assert decide(0.9, th) == MATCH
    assert decide(0.7, th) == INCONCLUSIVE
    assert decide(0.5, th) == NON_MATCH


def test_decide_rejects_nan() -> None:
    with pytest.raises(ValueError):
        decide(float("nan"), Thresholds(0.8, 0.3))


def test_calibrate_rates() -> None:
    diff = [i / 100 for i in range(100)]  # wrong authors: 0.00 .. 0.99
    same = [0.5 + i / 200 for i in range(100)]  # true authors: 0.50 .. 0.995
    th = calibrate(same, diff, fpr=0.05, fnr=0.05)
    assert sum(s > th.match for s in diff) <= 5
    assert sum(s < th.non_match for s in same) <= 5
    assert th.match == pytest.approx(0.95)
    assert th.non_match == pytest.approx(0.52)
    dist = calibrate([1 - s for s in same], [1 - s for s in diff], higher_is_match=False)
    assert sum(s < dist.match for s in [1 - s for s in diff]) <= 5
    with pytest.raises(ValueError):
        calibrate([], diff)
