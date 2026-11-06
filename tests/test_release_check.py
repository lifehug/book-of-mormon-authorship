"""The pre-release checks and the explorer's panels (BOM-37)."""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("release_check", ROOT / "scripts/release_check.py")
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)


def test_long_strings_flags_text_but_not_notes() -> None:
    doc = {"a": "x" * 500, "tests_note": "y" * 500, "b": [{"c": "z" * 10}, "w" * 501]}
    assert sorted(rc.long_strings(doc, 400)) == [".a", ".b[1]"]


def test_panel_rows_modes(tmp_path: Path) -> None:
    (tmp_path / "r.json").write_text(
        json.dumps(
            {"m": {"x": {"v": 1}, "y": {"v": 2}}, "c": {"A": 3}, "g": {"G": {"rank": [{"t": 1}]}}}
        )
    )
    (tmp_path / "t.csv").write_text('a,b\n1,"two, three"\n')
    rows = rc.panel_rows({"file": "r.json", "path": "m", "mode": "rows", "rows": ["y"]}, tmp_path)
    assert rows == [{"name": "y", "v": 2}]
    assert rc.panel_rows({"file": "r.json", "path": "c", "mode": "counts"}, tmp_path) == [
        {"name": "A", "count": 3}]  # fmt: skip
    assert rc.panel_rows({"file": "r.json", "path": "g", "mode": "groups", "sub": "rank"},
                         tmp_path) == [{"group": "G", "t": 1}]  # fmt: skip
    assert rc.panel_rows({"file": "t.csv", "mode": "csv"}, tmp_path) == [
        {"a": "1", "b": "two, three"}
    ]
    assert rc.panel_rows({"file": "none.json", "mode": "rows"}, tmp_path) is None


def test_check_panels_catches_problems(tmp_path: Path) -> None:
    (tmp_path / "r.json").write_text(json.dumps({"m": {"x": {"v": "q" * 900}}}))
    panels = [{"id": "long", "file": "r.json", "path": "m", "mode": "rows", "columns": ["v"]},
              {"id": "gone", "file": "no.json", "mode": "rows"},
              {"id": "later", "file": "no.json", "mode": "summary", "pending": True},
              {"id": "col", "file": "r.json", "path": "m", "mode": "rows", "columns": ["w"],
               "max_text": 1000}]  # fmt: skip
    probs = rc.check_panels(panels, tmp_path, 400)
    assert any(p.startswith("long:") for p in probs)
    assert any(p.startswith("gone:") for p in probs)
    assert not any(p.startswith("later:") for p in probs)
    assert any(p.startswith("col:") for p in probs)


def test_explorer_loads_with_the_current_results() -> None:
    panels = json.loads((ROOT / "explorer/panels.json").read_text())["panels"]
    assert rc.check_panels(panels) == []
