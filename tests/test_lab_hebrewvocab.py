"""BOM-132: the King James Old Testament concordance, its folding, the check and the pairings."""

from __future__ import annotations

from lab import hebrewvocab as H

ROWS = [
    {"book": "GEN", "section": "OT", "text": "The father and his mother smote the honour."},
    {"book": "EXO", "section": "OT", "text": "The father smite the people."},
    {"book": "MAT", "section": "NT", "text": "The parents of the church smiting."},
    {"book": "TOB", "section": "Apocrypha", "text": "The parents of the church."},
]
CFG = {"block_words": 2, "boot": 50, "boot_seed": 1}


def test_tokens_join_broken_words_and_read_long_s():
    assert H.tokens("over-\ntake the ſon") == ["overtake", "the", "son"]


def test_keys_fold_inflection_and_spelling():
    assert "smite" in H.keys("smiting", 3)
    assert "honour" in H.keys("honor", 3)
    assert "carry" in H.keys("carried", 3)
    assert H.keys("best", 3) == {"best"}  # no base shorter than the minimum


def test_concordance_holds_out_a_book():
    c = H.Concordance(ROWS, 3)
    assert c.in_ot("smiting")  # folded to smite
    assert not c.in_ot("smiting", fold=False)
    assert c.in_ot("honor") and not c.in_ot("honor", fold=False)
    assert not c.in_ot("parents") and c.in_nt_ap("parents")
    assert c.in_ot("mother") and not c.in_ot("mother", hold="GEN")  # only Genesis has it
    assert c.in_ot("father", hold="GEN")


def test_marks_leave_names_out_and_filter_by_lexicon():
    c = H.Concordance(ROWS, 3)
    kept, flag = H.marks(["the", "parents", "nephi", "xqzt"], c, {"nephi"}, {"the", "parents"})
    assert kept == ["the", "parents", "xqzt"] and flag == [0, 1, 0]
    _k, raw = H.marks(["the", "parents", "xqzt"], c, set(), None)
    assert raw == [0, 1, 1]


def test_interval_needs_two_blocks():
    assert H.interval([1], 1000, 10, 1) is None
    lo, hi = H.interval([1, 0, 0, 0] * 50, 4, 200, 1)
    assert lo <= 2500 <= hi


def test_pairings_count_both_orders_and_collectives():
    p = H.pairings(
        "his Father and his mother; mother and father; parents, a parent; sons and daughters",
        {"parents": ["\\b(?:father|fathers)\\s+and\\s+(?:\\w+\\s+)?(?:mother|mothers)\\b"
                     "|\\b(?:mother|mothers)\\s+and\\s+(?:\\w+\\s+)?(?:father|fathers)\\b",
                     "\\bparents?\\b"]},
    )  # fmt: skip
    assert p["parents"] == {"pair": 2, "collective": 2, "collective_share": 0.5}


def test_known_answer_passes_only_when_every_ot_book_is_lower():
    c = H.Concordance(ROWS, 3)
    ctx = {"conc": c, "kjv_names": set(), "lexicon": None}
    res = H.known_answer(ctx)
    by = {r["book"]: r["per_10k"] for r in res["books"]}
    # Genesis held out: "his", "mother" and "honour" are its own; Exodus held out: "people"
    assert by["MAT"] > 0 and by["TOB"] > 0
    assert res["passed"] == (max(by["GEN"], by["EXO"]) < min(by["MAT"], by["TOB"]))


def test_usfm_word_pattern_reads_nested_words():
    line = (
        '\\v 26 my \\w progenitors|strong="H2029"\\w* the \\nd \\+w LORD|strong="H3068"\\+w*\\nd*'
    )
    assert H.USFM_WORD.findall(line) == [("progenitors", "H2029"), ("LORD", "H3068")]
    assert H.strong_num("H0430") == 430 and H.strong_num("G2316") is None
