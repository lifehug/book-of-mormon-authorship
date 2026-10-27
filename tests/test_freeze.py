"""metadata.freeze lists every frozen file with its hash and detects a later change (BOM-19)."""

from metadata import freeze


def test_index_lists_and_hashes(monkeypatch, tmp_path):
    (tmp_path / "data/manifests").mkdir(parents=True)
    (tmp_path / "data/manifests/a.jsonl").write_text("x\n")
    (tmp_path / "data/controls").mkdir(parents=True)
    (tmp_path / "data/controls/history.txt").write_text("w1\nw2\n")
    monkeypatch.setattr(freeze, "FROZEN", ["data/controls/*.txt"])
    rec = freeze.index("t", tmp_path)
    assert set(rec["files"]) == {"data/controls/history.txt", "data/manifests/a.jsonl"}
    assert rec["files"]["data/controls/history.txt"]["bytes"] == 6


def test_missing_pattern_refuses(monkeypatch, tmp_path):
    monkeypatch.setattr(freeze, "FROZEN", ["data/nothing/*.txt"])
    try:
        freeze.files(tmp_path)
    except SystemExit as e:
        assert "nothing matches" in str(e)
    else:
        raise AssertionError("should refuse")
