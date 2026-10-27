"""`genre rules --append` must keep every existing label and add only missing rows."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata import genre


def test_append_keeps_existing_labels(tmp_path: Path, monkeypatch) -> None:
    cat = tmp_path / "catalog.parquet"
    out = tmp_path / "genre.parquet"
    rows = [
        {"work_id": "a", "source": "tcp", "title_norm": "poems", "genre_src": "",
         "date_raw": "", "has_text": True},
        {"work_id": "b", "source": "chronicling_america", "title_norm": "x", "genre_src": "",
         "date_raw": "", "has_text": True},
        {"work_id": "c", "source": "hathitrust", "title_norm": "y", "genre_src": "BK",
         "date_raw": "", "has_text": False},
    ]  # fmt: skip
    pq.write_table(pa.Table.from_pylist(rows), cat)
    model_row = {"work_id": "a", "genre": "other", "decided_by": "m", "model": "m"}
    pq.write_table(pa.Table.from_pylist([model_row], schema=genre.SCHEMA), out)
    monkeypatch.setattr(genre, "CATALOG", cat)
    monkeypatch.setattr(genre, "OUT", out)
    genre.run_rules(append=True)
    got = {r["work_id"]: r for r in pq.read_table(out).to_pylist()}
    assert {k: got["a"][k] for k in model_row} == model_row
    assert got["b"]["genre"] == "newspaper_periodical"
    assert got["c"]["genre"] == "uncertain" and got["c"]["decided_by"] == "rule:no_text"


def test_transient_pattern_ignores_quotation() -> None:
    from metadata.genre import _TRANSIENT

    assert not _TRANSIENT.search("the quotation continues through verse 4")
    assert _TRANSIENT.search("you have exceeded your quota")
