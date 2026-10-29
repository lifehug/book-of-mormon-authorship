"""BOM-21: the benchmark's calibration rules."""

from eval import benchmark


def test_gi_thresholds_follow_6_1():
    pos = [0.9, 0.95, 1.0, 0.8, 0.85] * 20
    neg = [0.0, 0.05, 0.1, 0.2, 0.3] * 20
    th = benchmark.calibrate_gi(pos, neg, 0.05)
    assert th["match"] >= 0.3 - 1e-9 and th["match"] <= 0.3 + 1e-9  # 95th pct of negatives
    assert th["non_match"] == 0.8  # 5th pct of positives
