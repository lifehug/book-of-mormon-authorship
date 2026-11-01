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


def test_body_correction(monkeypatch):
    monkeypatch.setattr(dates, "_verdicts", lambda: {"b": ("title_page", 1815)})
    monkeypatch.setattr(dates, "_body", lambda: {"b": 1844, "s": 1865})
    assert dates.effective_year("s", 1817) == 1865
    assert dates.effective_year("b", 1800) == 1844
    assert dates.effective_year("m", 1817) == 1817


def test_body_counts_flags_later_years_by_count():
    cfg = {"dates": {"latest_year": 1949, "slack_years": 2, "min_later_mentions": 10,
                     "min_later_share": 0.20, "min_year_mentions": 3}}  # fmt: skip
    serial = " ".join(["1817"] * 5 + ["1865"] * 12 + ["1998"] * 40)
    r = dates.body_counts(serial, 1817, cfg)
    assert r["flagged"] and r["corrected_year"] == 1865
    stamp = " ".join(["1817"] * 50 + ["1819"] * 30 + ["1923"] * 3)
    assert not dates.body_counts(stamp, 1817, cfg)["flagged"]
