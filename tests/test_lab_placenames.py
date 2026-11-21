"""BOM-110: the sound key, the matching rule, the gazetteer reader and the percentile."""

import random

import numpy as np

from lab.placenames import (
    close,
    entry_keys,
    key,
    length_matched,
    match_ids,
    one_edit,
    percentile,
    world_entries,
)

GROUPS = {"new_york": {"marks": ["N. Y."]}, "england": {"marks": ["Eng."]}}


def test_key_folds_spelling_to_sound():
    assert key("Oneida") == key("Onidah") or close(key("Oneida"), key("Onidah"), 0.35)
    assert key("Phenice") == "fenis"
    assert key("Hellam") == key("Helam")
    assert key("Sharon") != key("Saron")  # sh is one sound, kept apart from s


def test_entry_keys_drop_generic_and_short_words():
    assert entry_keys("Ripple Lake", {"lake"}, 3) == [key("Ripple")]
    assert entry_keys("Sainte-Agathe-des-Monts", {"sainte", "des"}, 3) == ["agaT", "monts"]


def test_close_is_edit_distance_over_the_longer_key():
    assert close("morin", "moron", 0.2)
    assert not close("morin", "moron", 0.15)
    assert not close("gid", "gad", 0.3)


def test_match_ids_agrees_with_close():
    keys = ["moron", "morin", "manti", "mantua", "angola", "onida", "oneida"]
    got = match_ids(["moron", "manti"], keys, 0.2)
    assert sorted(keys[i] for i in got[0]) == ["morin", "moron"]
    assert sorted(keys[i] for i in got[1]) == ["manti"]


def test_world_entries_take_the_first_mark_after_the_headword():
    text = (
        "Chester, p-v. Orange co. N. Y. ; 104 S. by W.\n\n"
        "Manchester, t. Eng. in Lancashire, the great centre.\n\n"
        "Delft, city, Neth., in S. Holland.\n\nnot an entry at all"
    )
    assert world_entries(text, GROUPS, 80) == [
        ("Chester", "new_york"),
        ("Manchester", "england"),
        ("Delft", None),
    ]


def test_one_edit_changes_a_key_by_one():
    rng = random.Random(1)
    for _ in range(50):
        assert close("kanandaigua", one_edit("kanandaigua", rng), 0.1)


def test_length_matched_and_percentile():
    got = length_matched(["ab", "abc", "abcd", "abcde"], [3, 3, 5], random.Random(0))
    assert sorted(map(len, got)) == [3, 4, 5] or sorted(map(len, got)) == [2, 3, 5]
    assert percentile(0.5, [0.1, 0.2, 0.5, 0.9]) == 62.5
    assert percentile(1.0, list(np.linspace(0, 0.9, 10))) == 100.0
