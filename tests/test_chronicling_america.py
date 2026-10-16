import json

from ingest.chronicling_america import (
    expand_issue,
    guess_state,
    page_path,
    parse_text,
    split_articles,
)

IMG = (
    "https://tile.loc.gov/image-services/iiif/service:ndnp:msar:batch_msar_emerald_ver02:"
    "data:2018270507:00414212621:1820040101:0035/full/pct:6.25/0/default.jpg"
)
ISSUE = {
    "id": "http://www.loc.gov/item/2018270507/1820-04-01/ed-1/",
    "location_state": ["mississippi"],
    "location_city": ["monticello"],
    "item": {"newspaper_title": ["Monticello Republican."]},
    "resources": [{"segments": 3, "image": IMG}],
}


def test_expand_issue() -> None:
    rows = expand_issue(ISSUE)
    assert [r["sequence"] for r in rows] == [1, 2, 3]
    r = rows[1]
    assert (r["lccn"], r["date"], r["edition"], r["state"], r["city"]) == (
        "2018270507", "1820-04-01", 1, "Mississippi", "Monticello",
    )  # fmt: skip
    assert "1820040101/0036.xml" in r["ocr_url"]
    assert page_path(r).as_posix().endswith("text/2018270507/1820-04-01-ed1-seq2.txt")


def test_expand_issue_without_image_or_id() -> None:
    bare = dict(ISSUE, resources=[{"segments": 2}])
    assert [r["ocr_url"] for r in expand_issue(bare)] == [None, None]
    assert expand_issue({"id": "http://www.loc.gov/item/sn84038116/"}) == []


def test_parse_text() -> None:
    payload = json.dumps({"/a/0036.xml": {"full_text": "Hello\nworld"}}).encode()
    assert parse_text(payload) == "Hello\nworld"


def test_split_articles() -> None:
    text = (
        "FOREIGN NEWS.\nLondon, March 3. The king has arrived at the palace and was received "
        "with great joy by the assembled people of the city, who had waited since morning "
        "in the cold and rain to see him pass.\n\nFor sale, a farm of fifty acres.\n"
        "Apply to the printer.\n\nSHIP NEWS\nArrived, brig Hope."
    )
    arts = split_articles(text)
    assert len(arts) == 3
    assert arts[0].startswith("FOREIGN NEWS.") and arts[1].startswith("For sale")
    assert arts[2] == "SHIP NEWS Arrived, brig Hope."
    assert split_articles("") == []


def test_sgp_image_and_state_fallback() -> None:
    img = (
        "https://tile.loc.gov/image-services/iiif/service:sgp:sgpbatches:batch_dlc_laperm_ver01:"
        "data:sn83025881:print:1800010101:0001/full/pct:6.25/0/default.jpg"
    )
    res = {
        "id": "http://www.loc.gov/item/sn83025881/1800-01-01/ed-1/",
        "item": {"place_of_publication": "Wilmington, Del."},
        "resources": [{"segments": 2, "image": img}],
    }
    rows = expand_issue(res)
    assert rows[1]["state"] == "Delaware"
    assert rows[1]["ocr_url"].count("sgp/sgpbatches/batch_dlc_laperm_ver01/data/sn83025881/print")
    assert "/1800010101/0002.xml" in rows[1]["ocr_url"]
    assert guess_state("Washington, D.C.") == "District of Columbia"
