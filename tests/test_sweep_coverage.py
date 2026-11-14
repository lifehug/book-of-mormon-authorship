"""The sweep's coverage tags (BOM-89, BOM-91)."""

from sweep.coverage import coverage, genre_class, identity, life, primary


def test_life_dates_from_catalog_author() -> None:
    assert life("Smith, Ethan, 1762-1849") == ("1762", "1849")
    assert life("Hunt, Gilbert J., 1780?-") == ("1780", "")
    assert life("Smith, Ethan") is None and life(None) is None


def test_identity_classes() -> None:
    a, b = ("1762", "1849"), ("1790", "1860")
    assert identity([a], [a, a]) == "verified"
    assert identity([a], [a, None]) == "same_dates_some_undated"
    assert identity([a], [b]) == "conflict"
    assert identity([a], [None]) == "one_side_dated"
    assert identity([None], [None]) == "undated"


def test_genre_class() -> None:
    assert (
        primary("sermon_devotional,other") == "sermon_devotional" and primary(None) == "uncertain"
    )
    assert genre_class("fiction_narrative", ["fiction_narrative"] * 3 + ["other"], 0.5)[0] == "same"
    assert (
        genre_class("fiction_narrative", ["other"] * 3 + ["fiction_narrative"], 0.5)[0] == "mixed"
    )
    assert genre_class("fiction_narrative", ["other"] * 4, 0.5) == ("cross", 0.0)
    assert genre_class("uncertain", ["other"], 0.5)[0] == "unknown"


def test_coverage_at_k() -> None:
    assert coverage([1, 5, 50, 500], [1, 10, 100]) == {"1": 0.25, "10": 0.5, "100": 0.75}
