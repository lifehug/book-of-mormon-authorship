"""BOM-31's imitation-robustness scoring helpers (section 9; Amendments 7 and 31)."""

import pytest

from eval.imitation import clopper_pearson, summarise, weight, windows

BANDS = [[0.8, 1.0], [0.6, 0.5]]


def test_windows_do_not_overlap() -> None:
    assert windows(list(range(12_345)), 5000) == [(0, 5000), (5000, 10_000)]
    assert windows(list(range(4999)), 5000) == []


def test_section_9_bands() -> None:
    assert weight(0.8, BANDS) == 1.0
    assert weight(0.79, BANDS) == 0.5
    assert weight(0.6, BANDS) == 0.5
    assert weight(0.59, BANDS) == 0.0


def test_clopper_pearson() -> None:
    lo, hi = clopper_pearson(3, 3)
    assert hi == 1.0 and lo == pytest.approx(0.292, abs=0.001)  # Amendment 7's "about 29-100%"
    assert clopper_pearson(0, 4)[0] == 0.0
    assert clopper_pearson(0, 0) == (0.0, 1.0)


def test_summarise() -> None:
    recs = [{"author": "a", "predicted": "a"}] * 3 + [{"author": "b", "predicted": "a"},
                                                    {"author": "b", "predicted": "b"}]  # fmt: skip
    s = summarise(recs, BANDS)
    assert (s["tests"], s["correct"], s["accuracy"]) == (5, 4, 0.8)
    assert s["by_author"] == {"a": 1.0, "b": 0.5}
    assert s["authors_majority_right"] == 1 and s["weight"] == 1.0
