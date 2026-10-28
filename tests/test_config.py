from pathlib import Path

import pytest
import yaml

from metadata import config


def _write(root: Path, cfg: dict) -> Path:
    path = root / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return path


def test_shipped_config_loads_and_matches_the_preregistration() -> None:
    cfg = config.load()
    assert cfg["corpus"]["ocr_max_cer"] == 0.10
    assert cfg["corpus"]["dedup"] == {
        "method": "minhash",
        "shingle": 5,
        "threshold": 0.8,
        "keep": "earliest",
        # Amendment 6
        "metadata_pass": {
            "keys": ["title_norm", "author_norm", "year"],
            "across_sources": True,
            "keep": "earliest",
        },
    }
    assert cfg["kjv_mask"]["verbatim"] == {"min_identity": 0.90, "min_tokens": 8}
    assert cfg["segmentation"]["chunk_words"] == [2000, 5000]
    assert cfg["sealing"]["contamination_min_tokens"] == 12


def test_every_pinned_path_is_present_in_the_shipped_config() -> None:
    cfg = config.load()
    for path in config.PINNED:
        config._dig(cfg, path)


def test_changing_a_registered_value_is_rejected(tmp_path: Path) -> None:
    cfg = config.load()
    cfg["corpus"]["ocr_max_cer"] = 0.20
    path = _write(tmp_path, cfg)
    with pytest.raises(config.ConfigError, match="dated OSF amendment"):
        config.load(path)


def test_missing_registered_key_is_rejected(tmp_path: Path) -> None:
    cfg = config.load()
    del cfg["kjv_mask"]["verbatim"]["min_tokens"]
    path = _write(tmp_path, cfg)
    with pytest.raises(config.ConfigError, match="missing required key"):
        config.load(path)


def test_missing_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(config.ConfigError, match="no config at"):
        config.load(tmp_path / "absent.yaml")


def test_hash_is_stable_and_changes_with_content(tmp_path: Path) -> None:
    first = config.sha256_of_config()
    assert len(first) == 64
    assert first == config.sha256_of_config()

    cfg = config.load()
    cfg["version"] = 99
    assert config.sha256_of_config(_write(tmp_path, cfg)) != first


def test_pending_amendment_entries_are_complete() -> None:
    rows = config.pending()
    assert rows, "the unregistered choices must stay listed until they are amended in"
    for row in rows:
        assert set(row) == {"key", "issue", "note"}
        assert row["issue"].startswith("BOM-")


def test_unregistered_choices_are_absent_from_the_config_body() -> None:
    """A pending choice must not also appear as a value, or it reads as registered."""
    cfg = config.load()
    for row in config.pending(cfg):
        path = tuple(row["key"].split("."))
        with pytest.raises(config.ConfigError):
            config._dig(cfg, path)


def test_cli_validate_and_hash(capsys: pytest.CaptureFixture[str]) -> None:
    assert config.main(["validate"]) == 0
    assert "match" in capsys.readouterr().out
    assert config.main(["hash"]) == 0
    assert len(capsys.readouterr().out.strip()) == 64


def test_cli_reports_error_for_bad_config(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("just a string\n", encoding="utf-8")
    assert config.main(["show", "-c", str(bad)]) == 1
