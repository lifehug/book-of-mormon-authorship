"""Spelling normalisation (BOM-15)."""

from pathlib import Path

from ocr_fix.normalize import artifacts, load_eme, normalize, regime, standardize

TABLE = {"vnto": "unto", "loue": "love", "haue": "have"}
CFG = {
    "corpus": {
        "spelling_normalization": {
            "pre_1700": "morphadorner_emod_lexicon",
            "post_1780": "artifacts_only",
        }
    }
}


def test_artifacts() -> None:
    assert artifacts("firſt ﬁne") == ("first fine", 2)


def test_standardize_preserves_case() -> None:
    text, applied = standardize("Vnto them I loue, LOUE and haue", TABLE)
    assert text == "Unto them I love, LOVE and have"
    assert sum(applied.values()) == 4


def test_regimes() -> None:
    assert regime(1611, CFG) == "morphadorner_emod_lexicon"
    assert regime(1785, CFG) == "artifacts_only"
    assert regime(1750, CFG) == "artifacts_only"
    assert normalize("loue ſhew", "artifacts_only", TABLE)[0] == "loue shew"
    assert normalize("loue ſhew", "morphadorner_emod_lexicon", TABLE)[0] == "love shew"


def test_table_skips_malformed_and_case_only(tmp_path: Path) -> None:
    f = tmp_path / "pairs.tab"
    f.write_text("﻿vnto\tunto\nABANTES\tAbantes\nchin\tchins\tchinned\n")
    assert load_eme(f) == {"vnto": "unto"}
