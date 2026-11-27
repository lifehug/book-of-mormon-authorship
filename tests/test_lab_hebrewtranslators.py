"""BOM-133: the fixed places, the classifying rule, the OCR reader and the verse locator."""

from __future__ import annotations

from lab import hebrewtranslators as H

LOC = {
    "anchors": 3,
    "max_candidates": 6000,
    "min_cover": 0.5,
    "min_context": 0.2,
    "context_words": 80,
    "context_weight": 0.5,
    "number_bonus": 0.15,
    "number_reach": 20,
    "pad_extra": 3,
    "pad_cap": 12,
    "stem_len": 6,
    "span_factor": 1.3,
}


def test_candidates_need_both_lemmas_close_and_hebrew():
    heb = {
        "Gen.2.24": [("1", "HNcmsc"), ("c/517", "HC/Ncfsc")],
        "Gen.1.1": [("1", "HNcmsc")] + [("853", "HTo")] * 10 + [("517", "HNcfsc")],
        "Dan.5.2": [("2", "ANcmsc"), ("517", "ANcfsc")],
    }
    assert H.candidates(heb, 8) == ["Gen.2.24"]


def test_check_places_reports_missing_lemma_and_english_numbering():
    w = {"lemma_window": 8, "places": {"pair": ["Gen.2.24"], "harah": ["Hos.2.7"]},
         "lemmas": {"harah": 2029}}  # fmt: skip
    heb = {"Gen.2.24": [("1", "HNcmsc"), ("c/517", "HC/Ncfsc")], "Hos.2.7": [("3205", "HVqrfsc")]}
    res, ref = H.check_places(H.places(w), heb, {"Hos.2.7": "Hos.2.5"}, w)
    assert res["participle_places_without_lemma"] == ["Hos.2.7:harah"] and not res["pass"]
    assert ref["Hos.2.7:harah"] == "Hos.2.5"


def test_classify_pair_and_participle_places():
    zech_young = "his father and his mother his parents thou dost not live"
    assert H.classify(zech_young, "pair")[0] == "FATHER_AND_MOTHER"
    assert H.classify(zech_young, "yalad") == ("PARENTS", "mother his parents")
    assert H.classify("his father and his mother that begat him", "yalad")[0] == "PARTICIPLE"
    assert H.classify("when her parents were dead", "pair")[0] == "PARENTS"
    assert H.classify("the blessings of my progenitors", "horay") == ("OTHER", None)
    assert H.classify("the blessings of thy father and of thy mother", "horay")[0] == (
        "FATHER_AND_MOTHER"
    )
    assert H.classify("bitterness to her bringing him forth", "yalad")[0] == "PARTICIPLE"
    assert H.classify("she that had borne seven", "yalad")[0] == "PARTICIPLE"


def test_reader_reads_ocr_variants_and_leaves_real_words():
    r = H.Reader({"farther": 3132, "bother": 42, "fother": 10, "fa": 100, "ther": 100}, 30, 2)
    assert r.read(["iatlier", "fiither", "motlier", "bom", "pareuts"]) == [
        "father", "father", "mother", "born", "parents"]  # fmt: skip
    assert r.read(["farther", "bother", "fother"]) == ["farther", "bother", "father"]
    assert r.read(["his", "fa", "ther"]) == ["his", "father"]
    assert r.variant("jether") is None and r.variant("maher") is None  # names
    assert r.variant("paran") is None


def test_long_s_reads_f_as_s_only_when_much_commoner():
    fix = H.long_s({"say": 5000, "fay": 20, "same": 5000, "fame": 3000, "thrust": 900}, 10)
    assert [fix(w) for w in ("fay", "fame", "thruft", "father")] == [
        "say", "fame", "thrust", "father"]  # fmt: skip


def test_stem_folds_parent_words_and_spelling():
    assert H.stem("father", 6) == H.stem("parents", 6) == H.stem("begat", 6) == H.PARENT_CLASS
    assert H.stem("honour", 6) == H.stem("honor", 6)
    assert H.stem("prolonged", 6) == H.stem("prolong", 6) == H.stem("prolongeth", 6)


def _verse(kjv: str, ylt: str, prev: str, nxt: str, number: int) -> dict:
    return {
        "kjv": H.tokens(kjv),
        "ylt": H.tokens(ylt),
        "prev": set(H.content(H.tokens(prev), 6)),
        "next": set(H.content(H.tokens(nxt), 6)),
        "number": number,
        "next_number": number + 1,
    }


def test_locate_prefers_the_verse_with_its_neighbours_and_number():
    filler = " ".join(["the land was quiet and the people were glad"] * 30)
    lookalike = "he that smiteth a man shall surely be put to death"
    prev = "whoso stealeth an ox shall restore five oxen"
    nxt = "if men strive together and one smite another with a stone"
    text = (
        f"{filler} 12 {lookalike} 13 {filler} "
        f"14 {prev} 15 and he that smiteth his father or his mother shall surely be put to "
        f"death 16 {nxt} {filler}"
    )
    tx = H.Text(text, 6)
    v = _verse("And he that smiteth his father, or his mother, shall be surely put to death.",
               "And he who smiteth his father or his mother is certainly put to death.",
               prev, nxt, 15)  # fmt: skip
    hit = H.locate(tx, v, LOC)
    a, b = hit["span"]
    words = " ".join(tx.toks[a:b])
    assert hit["found"] and "his father or his mother" in words and "man" not in words
    assert H.classify(words, "pair")[0] == "FATHER_AND_MOTHER"


def test_locate_reports_not_found_when_the_verse_is_absent():
    tx = H.Text(" ".join(["the land was quiet and the people were glad"] * 50), 6)
    v = _verse("Honour thy father and thy mother.", "Honour thy father and thy mother.",
               "remember the sabbath", "thou shalt not kill", 12)  # fmt: skip
    assert not H.locate(tx, v, LOC)["found"]


def test_increasing_flags_the_misplaced_one():
    at = {"a": 10, "b": 900, "c": 30, "d": 40}
    assert H.increasing(["a", "b", "c", "d"], at) == ["a", "c", "d"]


def test_summary_counts_classes_and_coverage():
    rows = {
        "Gen.2.24:pair": {"class": "FATHER_AND_MOTHER"},
        "Zech.13.3:yalad": {"class": "PARENTS"},
        "Gen.49.26:horay": {"class": "NOT_FOUND", "placed_class": "OTHER"},
    }
    s = H.summary(rows)
    assert s["located"] == 2 and s["coverage"] == 0.667 and s["parents_at_places"] == 1
    assert s["out_of_order"] == 1 and s["pair_and_parallel"] == {"FATHER_AND_MOTHER": 1}
