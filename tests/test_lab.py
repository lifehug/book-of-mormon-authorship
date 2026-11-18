"""The lab reads everything and writes only to its own folders; rule sets select as written."""

import re
from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest

from lab import paths, registry
from metadata.config import load

WRITERS = re.compile(r"\.write_text\(|\.write_bytes\(|write_table\(|open_memmap\(|np\.save|"
                     r"\.open\(\s*[\"'][wax]|\bopen\([^)]*[\"'][wax]")  # fmt: skip


def test_out_refuses_paths_outside_the_lab(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert paths.out("data/lab/x.json") == Path("data/lab/x.json")
    assert Path("data/lab").is_dir()
    for bad in ("data/sweep/bom_ranking.json", "config/preregistered.yaml", "paper/paper.md",
                "data/lab/../blind/x.json"):  # fmt: skip
        with pytest.raises(PermissionError):
            paths.out(bad)


def test_every_lab_write_goes_through_out() -> None:
    loose = []
    for f in sorted(Path("lab").glob("*.py")):
        lines = f.read_text().split("\n")
        for i, line in enumerate(lines):
            if WRITERS.search(line) and "out(" not in line + lines[i - 1]:
                loose.append(f"{f}:{i + 1}")
    assert not loose, f"lab code writes without lab.paths.out: {loose}"


def test_rule_sets_name_real_columns_and_select() -> None:
    views = load()["lab"]["views"]
    for name, view in views.items():
        assert set(view) <= set(registry.COLUMNS), name
    t = pa.Table.from_pylist([
        {"has_text": True, "kind": "work", "year": 1825, "words": 9000, "author_life": "alive"},
        {"has_text": True, "kind": "work", "year": None, "words": 9000, "author_life": "dead"},
        {"has_text": False, "kind": "newspaper_page", "year": 1825, "words": None,
         "author_life": None},
    ])  # fmt: skip
    assert registry.select(t, {}).num_rows == 3
    assert registry.select(t, {"has_text": True}).num_rows == 2
    assert registry.select(t, {"year": {"min": 1780, "max": 1830}}).num_rows == 2
    assert registry.select(t, {"words": {"min": 5000}, "kind": "work"}).num_rows == 2
    assert registry.select(t, {"author_life": {"any": ["alive", "unknown"]}}).num_rows == 1
    with pytest.raises(KeyError):
        registry.select(t, {"no_such_column": True})


def test_fast_pass_keeps_the_true_neighbour() -> None:
    pytest.importorskip("pyarrow")
    from lab.passages import Index

    rng = np.random.default_rng(0)
    vec = rng.standard_normal((5000, 384)).astype(np.float32)
    vec /= np.linalg.norm(vec, axis=1, keepdims=True)
    ix = object.__new__(Index)
    ix.codes = np.packbits(vec > 0, axis=1)
    ix.rows = (np.arange(5000) % 50).astype(np.int32)
    ix.works = [f"w{i}" for i in range(50)]
    q = vec[1234] + 0.05 * rng.standard_normal(384).astype(np.float32)
    assert 1234 in ix.candidates(q, None, 20, 1000)
    ok = ix.allowed({f"w{i}" for i in range(50) if i != 1234 % 50})
    kept = ix.candidates(q, ok, 20, 1000)
    assert 1234 not in kept and len(kept) == 20
    assert all(ix.rows[r] != 1234 % 50 for r in kept)
