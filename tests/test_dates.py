"""BOM-56: reading a volume's own title page for its year."""

from metadata import dates


def test_roman_and_arabic_years():
    assert dates.roman("MDCCCXLII") == 1842
    assert dates.roman("M.DCC.XCVI") == 1796
    assert dates.years_in("LONDON: PRINTED 1800. Sold by ... MDCCCXLII") == [1800, 1842]
    assert dates.years_in("Digitized in 2007; page 1945") == []  # outside 1600-1899


def test_verdicts():
    assert dates.verdict([1800, 1842], 1780, 1830) == ("post1830", 1842)
    assert dates.verdict([1776, 1800], 1780, 1830) == ("confirmed", 1800)
    assert dates.verdict([1776, 1812, 1815], 1780, 1830) == ("title_page", 1815)
    assert dates.verdict([1688], 1780, 1830) == ("undated", None)
    assert dates.verdict([], 1780, 1830) == ("undated", None)


def test_effective_year(monkeypatch):
    monkeypatch.setattr(dates, "_verdicts", lambda: {"a": ("post1830", 1842),
                                                     "b": ("title_page", 1815)})  # fmt: skip
    assert dates.effective_year("a", 1800) is None
    assert dates.effective_year("b", 1800) == 1815
    assert dates.effective_year("c", 1799) == 1799
