"""dedup --text normalized reads the normalised tree and writes its own outputs (BOM-15)."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata import dedup
from ocr_fix import clean, normalize


def test_normalized_path_mirrors_cleaned_tree(monkeypatch, tmp_path):
    monkeypatch.setattr(clean, "OUT_DIR", tmp_path / "cleaned")
    monkeypatch.setattr(normalize, "OUT_DIR", tmp_path / "normalized")
    row = {"source": "chronicling_america", "text_path": "/x/sn123/1825-04-27_p3.txt"}
    assert dedup._text_path(row, "raw") == "/x/sn123/1825-04-27_p3.txt"
    assert dedup._text_path(row, "normalized") == str(
        tmp_path / "normalized" / "chronicling_america" / "sn123" / "1825-04-27_p3.txt"
    )


def test_variant_writes_separate_outputs(monkeypatch, tmp_path):
    monkeypatch.setattr(clean, "OUT_DIR", tmp_path / "cleaned")
    monkeypatch.setattr(normalize, "OUT_DIR", tmp_path / "normalized")
    words = " ".join(f"w{i}" for i in range(400))
    rows = []
    for i, text in enumerate([words, words + " tail", "something else entirely " * 50]):
        raw = tmp_path / "raw" / f"doc{i}.txt"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("RAW " * 300 + str(i))  # raw texts are all different
        row = {"work_id": f"internet_archive:doc{i}", "source": "internet_archive",
               "text_path": str(raw), "has_text": True, "year": 1800 + i,
               "author_norm": "a"}  # fmt: skip
        dst = normalize.norm_path(row)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text)
        rows.append(row)
    cat = tmp_path / "catalog.parquet"
    pq.write_table(pa.Table.from_pylist(rows), cat)
    monkeypatch.setattr(dedup, "CATALOG", cat)
    raw_out = (tmp_path / "sig_raw", tmp_path / "dupes_raw.parquet", tmp_path / "auth_raw.parquet")
    norm_out = (tmp_path / "sig_n", tmp_path / "dupes_n.parquet", tmp_path / "auth_n.parquet")
    monkeypatch.setattr(dedup, "OUTPUTS", {"raw": raw_out, "normalized": norm_out})

    assert dedup.signatures(1, None, "normalized") == 0
    assert dedup.pairs(2000, "normalized") == 0
    d = pq.read_table(norm_out[1]).to_pylist()
    assert {r["work_id"] for r in d} == {"internet_archive:doc0", "internet_archive:doc1"}
    assert [r["work_id"] for r in d if r["is_keeper"]] == ["internet_archive:doc0"]
    assert dedup.authors("normalized") == 0
    assert pq.read_table(norm_out[2]).to_pylist()[0]["works"] == 2  # doc1 is a non-keeper
    assert not Path(raw_out[0]).exists() and not raw_out[1].exists()
