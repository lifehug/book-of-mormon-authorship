"""BOM-120: the one-break fit finds a planted switch and reports none where there is none."""

from lab.wherefore import blocks, grouped, one_break


def test_blocks_count_the_two_words():
    words = ["wherefore", "a", "therefore", "b"] * 3
    assert blocks(words, 4) == [(1, 1)] * 3


def test_one_break_finds_the_planted_switch():
    rows = [(0, 9)] * 10 + [(8, 1)] * 6
    fit = one_break(rows)
    assert fit["break_block"] == 10
    assert fit["sharpness"] > 0.8
    assert fit["deviance"] > 50


def test_one_break_is_flat_without_a_switch():
    fit = one_break([(1, 9)] * 12)
    assert fit["deviance"] < 1e-6


def test_grouped_gives_a_share_per_group():
    res = grouped({"a": (9, 1), "b": (1, 9)})
    assert res["groups"]["a"][2] == 0.9
