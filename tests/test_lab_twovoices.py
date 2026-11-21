"""BOM-105 / BOM-99: the pieces of the two-voices test behave as stated (no corpus text needed)."""

import numpy as np

from lab.twovoices import (
    attraction,
    attribute,
    chunks,
    clean_lines,
    delta,
    drop_kjv,
    features,
    tokens,
    verse_mask,
)

CFG = {
    "lab": {
        "two_voices": {
            "header_upper_share": 0.7,
            "header_max_words": 8,
            "verse_min_lines": 3,
            "verse_max_words": 10,
        }
    }
}


def test_running_headers_and_specks_are_blanked_in_place():
    lines = clean_lines("PRIVATE COMMUNICATIONS. 1831.\nand the Lord said\nF 2\n", CFG)
    assert lines == ["", "and the Lord said", "", ""]


def test_a_verse_run_is_found_and_prose_is_not():
    text = [
        "wrapped prose line that goes on",
        "Then he would fear and care,",
        "",
        "The days were hastening on;",
        "And that will be his destiny",
        "and back to prose again here",
    ]
    assert verse_mask(text, CFG) == [False, True, False, True, True, False]


def test_long_s_is_repaired_only_where_the_s_form_is_a_word():
    vocab = {"shall", "so", "first", "fat"}
    toks, fixed = tokens("He fhall fo firfl eat fat official", vocab)
    assert toks == ["he", "shall", "so", "first", "eat", "fat", "official"]
    assert fixed == 3


def test_king_james_ngrams_are_dropped_whole():
    grams = {"in the beginning god created"}
    toks = "and in the beginning god created all".split()
    assert drop_kjv(toks, grams, 5) == ["and", "all"]


def test_chunks_drop_the_short_tail():
    assert [len(c) for c in chunks(list("abcdefg"), 3)] == [3, 3]


def test_features_skip_dropped_words():
    w = [["the", "the", "thou", "and"], ["the", "thou", "of"]]
    assert features(w, 2, {"thou"}) == ["the", "of"]


def test_nearest_centroid_and_attraction():
    train = {"a": np.array([[0.0, 0.0]]), "b": np.array([[5.0, 5.0]])}
    test = {"a": np.array([[0.1, 0.0], [4.9, 5.0]]), "b": np.array([[5.0, 4.8]])}
    got = attribute(train, test, delta)
    assert got["a"][:2] == [2, 1] and got["b"][:2] == [1, 1]
    assert attraction(got) == {"a": 0.0, "b": 0.5}
