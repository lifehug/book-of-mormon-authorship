"""BOM-73: period assignment and the within-writer slope (eval.js_time)."""

import numpy as np

from eval.js_time import _slope, period_of

BINS = [[1829, 1830], [1831, 1833], [1834, 1836], [1837, 1839], [1840, 1844]]


def test_period_of():
    assert period_of(1829, BINS) == 0
    assert period_of(1833, BINS) == 1
    assert period_of(1834, BINS) == 2
    assert period_of(1844, BINS) == 4
    assert period_of(1845, BINS) is None


def test_slope_removes_writer_levels():
    # two writers at different levels, both falling by 1 per period: slope -1, not the level gap
    per = np.array([1, 2, 3, 1, 2, 3])
    writer = np.array(["a"] * 3 + ["b"] * 3)
    d = np.array([10.0, 9.0, 8.0, 3.0, 2.0, 1.0])
    assert abs(_slope(d, per, writer) - (-1.0)) < 1e-12


def test_slope_single_period_writer_adds_nothing():
    per = np.array([1, 2, 3, 2, 2])
    writer = np.array(["a", "a", "a", "b", "b"])
    d = np.array([1.0, 2.0, 3.0, 50.0, -50.0])
    assert abs(_slope(d, per, writer) - 1.0) < 1e-12
