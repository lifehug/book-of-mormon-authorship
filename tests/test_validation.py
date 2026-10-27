"""The BOM-12 review page must show text for every record, verse included."""

from pathlib import Path

from metadata.validation import excerpt


def test_verse_gets_an_excerpt(tmp_path: Path) -> None:
    verse = tmp_path / "verse.txt"
    verse.write_text(
        "O Myghty fader in heuen on hye\nOne god and perses thre\n\nThat made bothe daye\n"
    )
    assert excerpt({"text_path": str(verse)}) == (
        "O Myghty fader in heuen on hye / One god and perses thre / That made bothe daye"
    )


def test_prose_keeps_the_usual_excerpt(tmp_path: Path) -> None:
    prose = tmp_path / "prose.txt"
    line = "A long line of ordinary prose that is well over forty characters."
    prose.write_text(f"Title\n{line}\n")
    assert excerpt({"text_path": str(prose)}) == line


def test_no_text_path() -> None:
    assert excerpt({"text_path": None}) == ""


def test_build_reads_the_frozen_index(tmp_path: Path, monkeypatch) -> None:
    import json

    import pyarrow as pa
    import pyarrow.parquet as pq

    from metadata import validation

    text = tmp_path / "t.txt"
    text.write_text("A long line of ordinary prose that is well over forty characters.\n")
    cat = tmp_path / "catalog.parquet"
    row = {"work_id": "tcp:A1", "title": "T", "author": "A", "text_path": str(text)}
    pq.write_table(pa.Table.from_pylist([row, {**row, "work_id": "tcp:A2"}]), cat)
    rec = {k: None for k in validation.PUBLIC_FIELDS} | {"work_id": "tcp:A1", "stratum": "s"}
    index = tmp_path / "index.json"
    index.write_text(json.dumps([rec]))
    for name, path in (("CATALOG", cat), ("INDEX", index)):
        monkeypatch.setattr(validation, name, path)
    for name in ("SAMPLE", "PAGE"):
        monkeypatch.setattr(validation, name, tmp_path / name)
    validation.build()
    got = json.loads((tmp_path / "SAMPLE").read_text())
    assert [r["work_id"] for r in got] == ["tcp:A1"]
    assert got[0]["excerpt"].startswith("A long line")
    assert json.loads(index.read_text()) == [rec]
