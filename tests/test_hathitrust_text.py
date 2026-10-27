"""HathiTrust rsync zips -> one text file per volume, and the catalog's path to it (BOM-12)."""

import zipfile
from pathlib import Path

from ingest.hathitrust import clean_id, text_of, zip_path
from metadata.catalog import map_row


def test_clean_id_and_pairtree_path() -> None:
    htid = "uc2.ark:/13960/t1zc7t220"
    assert clean_id(htid) == "uc2.ark+=13960=t1zc7t220"
    expected = (
        "uc2/pairtree_root/ar/k+/=1/39/60/=t/1z/c7/t2/20/"
        "ark+=13960=t1zc7t220/ark+=13960=t1zc7t220.zip"
    )
    assert zip_path(htid, Path("")) == Path(expected)
    assert clean_id("mdp.39015022632585") == "mdp.39015022632585"


def test_pages_join_in_page_order(tmp_path: Path) -> None:
    z = tmp_path / "v.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("v/00000002.txt", "second")
        zf.writestr("v/00000001.txt", "first")
        zf.writestr("v/notes.xml", "<x/>")
    assert text_of(z) == "first\n\f\nsecond"


def test_catalog_row_points_at_extracted_text(tmp_path: Path) -> None:
    (tmp_path / "uc2.ark+=13960=t1zc7t220.txt").write_text("text")
    row = {
        "htid": "uc2.ark:/13960/t1zc7t220",
        "title": "Letters of the late Lord Lyttleton",
        "author": "Combe, William, 1742-1823.",
        "year": 1807,
        "rights_date_used": "1807",
        "lang": "eng",
        "bib_fmt": "BK",
    }
    out = map_row("hathitrust", row, tmp_path)
    assert out["work_id"] == "hathitrust:uc2.ark:/13960/t1zc7t220"
    assert out["has_text"] and out["text_path"].endswith("uc2.ark+=13960=t1zc7t220.txt")
    assert out["year"] == 1807 and out["author_norm"] == "combe, william"
