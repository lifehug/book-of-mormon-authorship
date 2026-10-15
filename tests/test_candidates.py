from pathlib import Path

import pytest

from ingest import candidates as c


def entry(**kw):
    e = {
        "id": "gh-1816-late-war",
        "candidate": "Gilbert J. Hunt",
        "title": "The Late War",
        "url": "https://archive.org/details/latewarbetween_00hunt",
        "kind": "ia_djvu",
        "provenance": "printed_by_author",
        "license": "public domain",
        "private": False,
    }
    e.update(kw)
    return e


JSP = dict(
    id="js-1832-history",
    candidate="Joseph Smith",
    url="https://www.josephsmithpapers.org/paper-summary/history-circa-summer-1832",
    kind="jsp_page",
    provenance="mixed",
    private=True,
)


def test_real_manifest_is_valid():
    entries = c.load_manifest()
    assert len(entries) > 20
    assert {e["candidate"] for e in entries} == set(c.CANDIDATES)
    assert all(e["private"] for e in entries if e["kind"] == "jsp_page")


def test_valid_entry_has_no_errors():
    assert c.validate_entry(entry()) == []
    assert c.validate_entry(entry(**JSP)) == []


@pytest.mark.parametrize(
    "bad",
    [
        {"kind": "pdf"},
        {"provenance": "ghostwritten"},
        {"candidate": "Mark Twain"},
        {"private": "no"},
        {"id": "Bad_ID"},
        {"url": "https://archive.org/stream/latewarbetween_00hunt"},
    ],
)
def test_invalid_entries(bad):
    assert c.validate_entry(entry(**bad))


def test_missing_field():
    e = entry()
    del e["license"]
    assert c.validate_entry(e) == ["gh-1816-late-war: missing license"]


def test_jsp_must_be_private_and_slug_only():
    assert c.validate_entry(entry(**{**JSP, "private": False}))
    assert c.validate_entry(entry(**{**JSP, "url": JSP["url"] + "/1"}))


def test_duplicate_ids():
    errs = c.validate_manifest([entry(), entry()])
    assert errs == ["gh-1816-late-war: duplicate id"]


def test_output_paths():
    root = Path("/r")
    assert c.output_path(entry(), root) == root / "data/candidates/text/gh-1816-late-war.txt"
    assert (
        c.output_path(entry(private=True), root)
        == root / "data/private/candidates/gh-1816-late-war.txt"
    )
    assert (
        c.output_path(entry(**JSP), root) == root / "data/private/candidates/js-1832-history.jsonl"
    )
    assert c.output_path(entry(kind="wikisource"), root) is None
    assert c.raw_dir(entry(**JSP), root) == root / "data/private/candidates/raw/js-1832-history"


def test_url_helpers():
    assert c.ia_text_url(entry()) == (
        "https://archive.org/download/latewarbetween_00hunt/latewarbetween_00hunt_djvu.txt"
    )
    e = entry(url="https://archive.org/details/X", file="A B_djvu.txt")
    assert c.ia_text_url(e) == "https://archive.org/download/X/A%20B_djvu.txt"
    assert c.jsp_slug(JSP["url"]) == "history-circa-summer-1832"
    with pytest.raises(ValueError):
        c.jsp_slug("https://example.org/x")


def test_select():
    es = [entry(), entry(id="p", private=True), entry(id="w", kind="wikisource")]
    assert [e["id"] for e in c.select(es)] == ["gh-1816-late-war", "p"]
    assert [e["id"] for e in c.select(es, public_only=True)] == ["gh-1816-late-war"]
    assert [e["id"] for e in c.select(es, ids=["p"])] == ["p"]
    with pytest.raises(ValueError):
        c.select(es, ids=["nope"])


def test_run_skips_existing(tmp_path):
    out = c.output_path(entry(), tmp_path)
    out.parent.mkdir(parents=True)
    out.write_text("already here")
    assert c.run([entry()], root=tmp_path, delay=0) == []
