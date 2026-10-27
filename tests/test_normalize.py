"""Spelling normalisation (BOM-15)."""

import pytest

from ocr_fix.morphadorner import rebuild
from ocr_fix.normalize import artifacts, normalize, regime

# MorphAdorner's (token, standard) output for "Vnto them I loue,\nye part ſhew"
ADORNED = [("Vnto", "Unto"), ("them", "them"), ("I", "I"), ("loue", "love"), (",", ","),
            ("ye", "the"), ("part", "part"), ("ſhew", "show")]  # fmt: skip
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


def test_rebuild_keeps_layout_and_skips_inserted_tokens() -> None:
    text, applied, missed = rebuild("Vnto them I loue,\nye part ſhew", [("¶", "¶"), *ADORNED])
    assert text == "Unto them I love,\nthe part show"
    assert missed == 1
    assert applied[("loue", "love")] == 1 and ("part", "partly") not in applied


def test_regimes() -> None:
    assert regime(1611, CFG) == "morphadorner_emod_lexicon"
    assert regime(1785, CFG) == "artifacts_only"
    assert regime(1750, CFG) == "artifacts_only"
    assert normalize("loue ſhew", "artifacts_only")[0] == "loue shew"
    text = "Vnto them I loue,\nye part ſhew"
    assert (
        normalize(text, "morphadorner_emod_lexicon", ADORNED)[0]
        == "Unto them I love,\nthe part show"
    )
    with pytest.raises(ValueError):
        normalize(text, "morphadorner_emod_lexicon")
