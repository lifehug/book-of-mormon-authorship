"""BOM-120: the one-break fit finds a planted switch and none where there is none; the Metcalfe
recount compares cells, reads the switch and parses the 1920 verse text."""

from lab.wherefore import agrees, blocks, compare, grouped, one_break, switch, tw, verses_1920


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


# Metcalfe 1993 recount (`python -m lab.wherefore metcalfe`)
M = {"tol_abs": 2, "tol_rel": 0.03}


def test_tw_counts_in_metcalfes_order():
    assert tw(["wherefore", "therefore", "therefore", "where", "fore"]) == [2, 1]


def test_agreement_uses_the_larger_of_the_two_tolerances():
    assert agrees(288, 286, M)  # within 2
    assert not agrees(19, 22, M)  # 3 off, 3% of 22 is under 1
    assert agrees(209, 200, M) is False and agrees(206, 200, M)  # 3% of 200 is 6


def test_compare_names_the_cells_that_disagree_and_the_missing_rows():
    res = compare({"Alma": [288, 3]}, {"Alma": (286, 3), "Ether": (24, 63)}, M)
    assert not res["reproduced"]
    assert res["disagree"] == ["Ether: not counted"]
    assert res["rows"]["Alma"]["agree"]


def test_switch_reads_the_mosiah_first_order():
    table = {"Mosiah": (9, 1), "Mormon": (5, 0), "Ether": (2, 8), "1 Nephi": (1, 9)}
    assert switch(table) == {"first_wherefore_book": "Ether", "holds": True}
    table["Mormon"] = (1, 5)
    assert switch(table)["holds"] is False


def test_verses_1920_assigns_books_and_reads_the_4_nephi_form():
    text = (
        "1 Nephi Chapter 1\n\n1:1 And therefore I\nwrote wherefore.\n\n1:2 Wherefore.\n\n"
        " FOURTH NEPHI\n\n4 Nephi 1:1 Therefore they\nhad all things.\n\n"
        "4 Nephi 1:2 And so.\n"
    )
    vs = verses_1920(text)
    assert [(b, c, v, tw(w)) for b, c, v, w in vs] == [
        ("1 Nephi", 1, 1, [1, 1]),
        ("1 Nephi", 1, 2, [0, 1]),
        ("4 Nephi", 1, 1, [1, 0]),
        ("4 Nephi", 1, 2, [0, 0]),
    ]
