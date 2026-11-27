"""BOM-130: the pieces of the 2 Nephi 28 lookup: ranks with ties against the text, the meaning
order, which grams count as rare, the Late War window and the card's verdict."""

import numpy as np

from lab.nephi28_sources import (
    chapter_window,
    era_of,
    meaning_key,
    rank_against,
    rare_grams,
    seqs,
    verdict,
)

CARD = {"yes_share": 0.01, "no_share": 0.10}


def test_ties_count_against_the_text():
    pop = np.array([5.0, 3.0, 3.0, 0.0, 0.0])
    assert rank_against(5.0, pop, member=True) == 1
    assert rank_against(3.0, pop, member=True) == 3  # the other 3.0 comes first
    assert rank_against(0.0, pop, member=True) == 5  # sharing nothing is last, not "top"
    assert rank_against(3.0, pop, member=False) == 4  # an outside text is one more
    assert rank_against(9.0, pop, member=False) == 1


def test_meaning_orders_by_places_then_mean():
    k = meaning_key(np.array([1, 0, 1, 2]), np.array([0.2, 0.99, 0.5, -1.0]))
    assert list(np.argsort(-k)) == [3, 2, 0, 1]


def test_rare_grams_count_an_outside_text_itself():
    df = {1: 5, 2: 4, 3: 6}
    assert rare_grams({1, 2, 3, 9}, df, 5, outside=False) == {1, 2}
    assert rare_grams({1, 2, 3, 9}, df, 5, outside=True) == {2, 9}


def test_window_sits_in_the_middle():
    assert chapter_window(100, 1000) == (450, 550)
    assert chapter_window(2000, 1000) == (0, 1000)


def test_verdict_follows_the_card():
    assert verdict({"rare": 0.005, "meaning": 0.5}, {"rare": True}, CARD) == "yes"
    # top 1% but beaten by a topic control: not yes
    assert verdict({"rare": 0.005, "meaning": 0.5}, {"rare": False}, CARD) == "cannot tell"
    assert verdict({"rare": 0.2, "meaning": 0.5}, {}, CARD) == "no"
    assert verdict({"rare": 0.05, "meaning": 0.5}, {}, CARD) == "cannot tell"
    assert verdict({"rare": None, "meaning": None}, {}, CARD) == "not placed"


def test_spans_and_eras():
    assert seqs([485, 489]) == {485, 486, 487, 488, 489}
    eras = {"late": [1780, 1829], "early": [1640, 1779]}
    assert era_of(1700, eras) == "early" and era_of(1828, eras) == "late"
