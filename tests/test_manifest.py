from pathlib import Path

from metadata import manifest


def _make_tree(root: Path) -> None:
    (root / "a.txt").write_text("alpha")
    (root / "sub").mkdir()
    (root / "sub" / "b.txt").write_text("beta")
    (root / ".hidden").write_text("ignored")


def test_build_lists_files_sorted_and_skips_hidden(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    records = manifest.build(tmp_path)
    assert [r["path"] for r in records] == ["a.txt", "sub/b.txt"]
    assert records[0]["bytes"] == 5
    assert len(records[0]["sha256"]) == 64


def test_roundtrip_and_verify_ok(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    out = tmp_path / "manifest.jsonl"
    records = manifest.build(tmp_path, exclude=[out])
    manifest.write(records, out)
    assert manifest.read(out) == records
    assert manifest.verify(tmp_path, records) == []


def test_verify_reports_changed_and_missing(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    records = manifest.build(tmp_path)
    (tmp_path / "a.txt").write_text("ALPHA")  # same size, different bytes
    (tmp_path / "sub" / "b.txt").unlink()
    problems = manifest.verify(tmp_path, records)
    assert problems == ["checksum changed: a.txt", "missing: sub/b.txt"]


def test_cli_build_then_verify(tmp_path: Path) -> None:
    _make_tree(tmp_path)
    out = tmp_path / "m.jsonl"
    assert manifest.main(["build", str(tmp_path), "-o", str(out)]) == 0
    assert manifest.main(["verify", str(tmp_path), str(out)]) == 0
    (tmp_path / "a.txt").write_text("changed!")
    assert manifest.main(["verify", str(tmp_path), str(out)]) == 1
