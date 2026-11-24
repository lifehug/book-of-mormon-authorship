"""Pure functions of lab.utoaztecan_vocab (BOM-117): his Comparative Vocabulary, synthetic data."""

import numpy as np

from lab import utoaztecan_vocab as v


def _r(initial, medial):
    return {"initial": initial, "medial": medial}


BRANCHES = {"Num": ["Mn", "NP", "Sh"], "Hp": ["Hp"], "Azt": ["CN"], "Cah": ["Yq", "AYq"]}


def test_parse_vocabulary_reads_heads_in_order():
    lines = [
        "intro 12. not a set",
        "                   PART THREE: THE COMPARATIVE VOCABULARY",
        "1a. *sami ‘bread’ (1a) or mud: Mn sami",
        "   more of set one",
        "2. *supa- ‘adobe’: Tr supa",
        "5. *kuLu / *kutu 'mescal': Hp kuru",
        "99. a stray number far ahead",
        "A UTO-AZTECAN BIBLIOGRAPHY",
        "7. after the end",
    ]
    sets = v.parse_vocabulary(lines)
    assert sorted(sets) == [1, 2, 5]
    assert sets[1]["form"] == "*sami" and sets[1]["gloss"] == "bread"
    assert "more of set one" in sets[1]["body"]
    assert sets[5]["form"] == "*kuLu" and sets[5]["gloss"] == "mescal"


def test_branches_of_counts_languages_followed_by_a_form():
    body = "M67-3 *ma: Mn kusa; NP kwasi; Sh(M) hunu; CN kwasi; B.Tep *bahi; Hopi text"
    assert v.branches_of(body, BRANCHES) == {"Num", "Azt"}
    assert v.branches_of("AYq bwasa; Yq bwasa", BRANCHES) == {"Cah"}


def test_uacv_cited_keeps_order_without_repeats():
    assert v.uacv_cited("see UACV-12 and UACV-7, also UACV-12") == [12, 7]
    assert v.uacv_cited("none") == []


def test_outputs_outside_his_inventory():
    table = {
        "kw": {"b": _r({"kw"}, {"kw"}), "g": _r({"ø", "ŋ"}, {"k"})},
        "p": {"b": _r({"b", "p"}, {"p"}), "l": _r({"l"}, {"r"})},
    }
    inv = ["p", "t", "k", "kw", "’", "h", "s", "c", "m", "n", "L", "w", "y"]
    assert v.outputs_outside(table, inv) == {"kw": ["ŋ"], "p": ["b"]}


def test_ipa_symbols_maps_consonants_and_refuses_unknown():
    mapping = {"k": "k", "t": "t", "ʃ": "š", "ts": "ṣ", "ʁ": "r", "tˤ": "ṭ", "n": "n"}
    assert v.ipa_symbols("k a tʰ ʃ i", mapping) == ["k", "t", "š"]
    assert v.ipa_symbols("ts u n", mapping) == ["ṣ", "n"]
    assert v.ipa_symbols("tˤ a ʁ", mapping) == ["ṭ", "r"]
    assert v.ipa_symbols("ɮ a", mapping) is None
    assert v.ipa_symbols("a i", mapping) == []


def test_shuffle_excess_finds_a_diagonal_and_not_a_flat_matrix():
    rng = np.random.default_rng(0)
    eye = np.eye(30, dtype=bool)
    r = v.shuffle_excess(eye, 500, rng)
    assert r["rate"] == 1.0 and r["p"] < 0.01 and r["excess"] > 0.9
    flat = np.ones((30, 30), dtype=bool)
    r = v.shuffle_excess(flat, 200, rng)
    assert r["excess"] == 0.0 and r["p"] == 1.0


def test_passes_uses_any_column_and_fails_an_unreadable_one():
    table = {
        "kw": {"b": _r({"kw"}, {"kw"}), "s1": _r({"s"}, {"s"})},
        "e": {"b": _r({"p"}, {"p"})},
    }
    assert v.passes(["b", "š"], ["kw", "s"], ["kw"], table, 3)
    assert not v.passes(["b", "š"], ["p", "s"], ["kw"], table, 3)
    assert not v.passes(["b", "š"], ["p", "s"], ["e"], table, 3)  # e cannot read š
    assert v.passes(["b"], ["p"], ["kw", "e"], table, 3)


def test_verdict():
    prim = {"p": 0.001, "excess": 0.05}
    assert v.verdict(prim, {"a": {"excess": 0.01}}, 0.01) == "his rules pick it out"
    assert v.verdict(prim, {"a": {"excess": 0.06}}, 0.01).startswith("his rules find")
    assert v.verdict({"p": 0.2, "excess": 0.05}, {}, 0.01).startswith("his rules find")
