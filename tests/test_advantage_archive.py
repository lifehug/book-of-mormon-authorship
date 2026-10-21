import datetime as dt

from ingest import advantage_archive as aa


def test_page_name_roundtrip():
    name = aa.page_name("lake_light_usa_new_york_trumansburg", dt.date(1828, 8, 20), 2)
    assert name == "lake_light_usa_new_york_trumansburg_18280820_english_2"
    assert aa.parse_name(name) == ("1828-08-20", 2)


def test_pubdate_id_from_viewer_shell():
    html = (
        '<a href="/GetViewer?url=%2fviewer%2f%3ffn%3dx&amp;PubdateId=157741350'
        '&amp;file=/viewer/GetPdfFile?157741350#zoom=page-width">'
    )
    assert aa.pubdate_id(html) == "157741350"
    assert aa.pubdate_id("PDF can't be displayed") is None


def test_urls():
    assert aa.pdf_url("trumansburg", "1") == (
        "https://trumansburg.advantage-preservation.com/viewer/GetPdfFile?1"
    )
    u = aa.viewer_url("trumansburg", "34773,47247", "3142", "n")
    assert "cid=3142" in u and "fn=n" in u and "t=34773,47247" in u
