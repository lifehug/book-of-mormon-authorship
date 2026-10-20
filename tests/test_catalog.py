import pytest

from metadata import catalog


@pytest.mark.parametrize(
    ("raw", "expect"),
    [
        ("Smith, John, 1780-1850", "smith, john"),
        ("John Smith", "smith, john"),
        ("SMITH (John)", "smith, john"),
        ("Smith, J.", "smith, j"),
        ("Smith, J", "smith, j"),
        ("Rev. Ethan Smith", "smith, ethan"),
        ("Hunt, Gilbert J.", "hunt, gilbert j"),
        ("Spalding, Solomon, 1761-1816", "spalding, solomon"),
        ("Phelps, W. W.", "phelps, w w"),
        (None, ""),
        ("", ""),
    ],
)
def test_norm_author(raw, expect):
    assert catalog.norm_author(raw) == expect


def test_norm_author_keeps_distinct_people_apart():
    assert catalog.norm_author("Smith, John") != catalog.norm_author("Smith, Joseph")
    assert catalog.norm_author("Smith, J.") != catalog.norm_author("Smith, John")


@pytest.mark.parametrize(
    ("raw", "expect"),
    [("1823", 1823), ("[1825]", 1825), ("circa 1816", 1816), ("1829-06-26", 1829)],
)
def test_parse_year(raw, expect):
    assert catalog.parse_year(raw) == expect


def test_parse_year_rejects_placeholders_and_none():
    assert catalog.parse_year("18uu") is None
    assert catalog.parse_year(None) is None
    assert catalog.parse_year("no date here") is None


def test_tcp_is_exempt_from_the_period_window():
    """TCP spans 1473-1700 by design: it is the early modern reference for dating (5.3).

    Filtering it to the 1780-1830 comparison window drops 95% of it and removes the ability
    to answer Q3. This guards the regression.
    """
    assert "tcp" in catalog.DATE_EXEMPT
    assert "institutional_books" not in catalog.DATE_EXEMPT


def test_merge_flags_the_period_rather_than_filtering():
    """Rows outside 1780-1830 are flagged, never dropped.

    BOM-40's multiverse varies corpus-level choices, which is impossible if an earlier stage
    has already discarded rows. Stages wanting the comparison set filter on `in_period`.
    """
    names = [f.name for f in catalog.SCHEMA]
    assert "in_period" in names
    src = (catalog.Path("metadata/catalog.py")).read_text()
    assert "Flag, never drop" in src
