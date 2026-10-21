import importlib.util
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "nyshn_browser_pull", Path(__file__).resolve().parents[1] / "scripts" / "nyshn_browser_pull.py"
)
nyshn = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nyshn)

BROWSE = (
    '<a href="/?a=cl&amp;cl=CL2.1823.10&amp;sp=ws&amp;e=-------en-20--1--txt-txIN----------">'
    'October</a> <a href="/?a=cl&amp;cl=CL2.1824.1&amp;sp=ws&amp;e=x">January</a>'
)
MONTH = (
    '<a href="/?a=d&amp;d=ws18231001-01&amp;e=x">1 October 1823</a>'
    '<a href="/?a=d&amp;d=ws18231008-01&amp;e=x">8 October 1823</a>'
)
ISSUE = (
    '<a href="/?a=d&amp;d=ws18231001-01.1.1&amp;e=x">Page 1</a>'
    '<a href="/?a=d&amp;d=ws18231001-01.1.4&amp;e=x">Page 4</a>'
    '<a href="/?a=d&amp;d=ws18231008-01&amp;e=x">Next issue</a>'
)
VIEW = (
    '<div id="ocrdisclaimer"><p>This text was automatically generated</p></div>'
    '<p dir="auto">TERMS :&#39; The  Sentinel</p><p dir="auto"> </p>'
    '<p dir="auto">Two <b>Dollars</b> &amp; Fifty</p></div><footer>x</footer>'
)
TITLES = (
    '<a href="/?a=cl&amp;cl=CL1&amp;sp=ws&amp;e=x">\n  Wayne Sentinel\n</a>'
    '<a href="/?a=cl&amp;cl=CL1&amp;sp=onr&amp;e=x">Ontario Repository</a>'
    '<a href="/?a=cl&amp;cl=CL1&amp;sp=onrb&amp;e=x">Ontario Repository</a>'
)


def test_month_links():
    got = {(m.group("y"), m.group("m"), m.group("code")) for m in nyshn.MONTH_LINK.finditer(BROWSE)}
    assert got == {("1823", "10", "ws"), ("1824", "1", "ws")}


def test_issue_links_ignore_page_links():
    issues = {
        (m.group("code"), m.group("date"), m.group("ed")) for m in nyshn.ISSUE_LINK.finditer(MONTH)
    }
    assert issues == {("ws", "18231001", "01"), ("ws", "18231008", "01")}
    on_issue_page = {m.group("date") for m in nyshn.ISSUE_LINK.finditer(ISSUE)}
    assert on_issue_page == {"18231008"}
    pages = {int(m.group("page")) for m in nyshn.PAGE_LINK.finditer(ISSUE)}
    assert pages == {1, 4}


def test_text_from_view_unescapes_and_drops_blank_paragraphs():
    assert nyshn.text_from_view(VIEW) == "TERMS :' The Sentinel\nTwo Dollars & Fifty\n"
    assert nyshn.text_from_view("<html>Oops!</html>") == ""


def test_title_codes_and_names():
    codes = nyshn.title_codes(TITLES)
    assert codes["wayne sentinel"] == ["ws"]
    assert codes["ontario repository"] == ["onr", "onrb"]
    assert nyshn.page_name("wayne_sentinel", "18231001", "01", 3) == "wayne_sentinel_18231001_p3"
    assert (
        nyshn.page_name("wayne_sentinel", "18231001", "02", 1) == "wayne_sentinel_18231001_ed2_p1"
    )


def test_month_in_range():
    import datetime as dt

    d0, d1 = dt.date(1823, 10, 15), dt.date(1824, 1, 1)
    assert nyshn.month_in_range(1823, 10, d0, d1)
    assert nyshn.month_in_range(1824, 1, d0, d1)
    assert not nyshn.month_in_range(1823, 9, d0, d1)
    assert not nyshn.month_in_range(1824, 2, d0, d1)
