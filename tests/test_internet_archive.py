from ingest.internet_archive import (
    in_window,
    item_year,
    likely_has_text,
    norm_title,
    overlaps_harvard,
    parse_year,
)


def test_norm_title_strips_punctuation_and_truncates():
    assert norm_title("The  Book, of: Mormon!") == "the book of mormon"
    assert norm_title(None) == ""
    long = "a" * 100
    assert norm_title(long) == "a" * 60


def test_parse_year():
    assert parse_year("1812-01-01T00:00:00Z") == 1812
    assert parse_year(1830) == 1830
    assert parse_year("[1815?]") == 1815
    assert parse_year("18--") is None
    assert parse_year("12345") is None
    assert parse_year(None) is None


def test_item_year_prefers_year_field_and_handles_lists():
    assert item_year({"year": "1799", "date": "1800"}) == 1799
    assert item_year({"date": ["1805-01-01T00:00:00Z"]}) == 1805
    assert item_year({}) is None


def test_in_window():
    assert in_window(1780) and in_window(1830)
    assert not in_window(1779) and not in_window(1831) and not in_window(None)


def test_overlaps_harvard_matches_title_and_year():
    keys = {(norm_title("A View of the Hebrews."), 1823)}
    assert overlaps_harvard({"title": "A view of the Hebrews", "year": 1823}, keys)
    assert overlaps_harvard({"title": ["A View of the Hebrews;"], "date": "1823"}, keys)
    assert not overlaps_harvard({"title": "A view of the Hebrews", "year": 1825}, keys)
    assert not overlaps_harvard({"title": "", "year": 1823}, keys)


def test_likely_has_text():
    assert likely_has_text({"imagecount": 120, "collection": ["americana"]})
    assert not likely_has_text({"collection": ["americana"]})
    assert not likely_has_text({"imagecount": 5, "collection": ["etree"]})
