"""BOM-135: the pinned rules of the sermon outline test: the cut at Chapin's markers, the
point-match threshold, the verdict, the floor on the order p, the known-answer rule, the seeded
scramble, both outline variants' jobs, and a planted outline found in order."""

import numpy as np
import pytest

from lab.sermon_outline import (
    ka_passed,
    match_threshold,
    order_test,
    outline_jobs,
    outlines_of,
    p_floor,
    paragraphs,
    place,
    scramble,
    split_id,
    trim,
    unrelated_cosines,
    verdict,
)

CARD = {
    "block_words": 5,
    "max_points": 12,
    "match_score": 1.0,
    "mismatch_score": -0.5,
    "gap_score": -0.5,
    "shuffles": 1000,
    "max_order_p": 0.01,
    "no_share": 0.10,
}
SERMON = (
    "Digitized by Google FAREWELL SERMON, title page\n"
    "EXODUS XXXII. 6. And the people sat down. This is evident, 1. From other passages\n"
    "IMPROVEMENT. 1. We learn ...... FAREWELL ......\n"
    "RESULT OF COUNCIL 1. The conduct of his ordaining council"
)


def test_trim_keeps_only_the_sermon():
    got = trim(SERMON, "EXODUS XXXII", "FAREWELL")
    assert got.startswith("EXODUS XXXII") and got.endswith("FAREWELL")
    assert "Google" not in got and "RESULT OF COUNCIL" not in got
    assert "IMPROVEMENT. 1." in got
    with pytest.raises(ValueError):
        trim(SERMON, "GENESIS", "FAREWELL")
    with pytest.raises(ValueError):
        trim("EXODUS XXXII and no end", "EXODUS XXXII", "FAREWELL")


def test_threshold_is_the_quantile_of_unrelated_cosines():
    assert match_threshold(np.arange(101) / 100, 0.99) == pytest.approx(0.99)
    assert match_threshold([[0.1, 0.2], [0.3, 0.4]], 0.5) == pytest.approx(0.25)
    with pytest.raises(ValueError):
        match_threshold([], 0.99)
    vec = {"a": np.eye(3)[:2], "b": np.eye(3)[[0]], "c": np.zeros((0, 3))}
    assert sorted(unrelated_cosines(vec).tolist()) == [0.0, 1.0]  # a with b; never a with a


def test_verdict_follows_the_card():
    assert verdict(1, 0.005, 61, CARD) == "stands out"
    assert verdict(1, 0.05, 61, CARD) == "cannot tell"  # first, but the order is not shown
    assert verdict(1, None, 61, CARD) == "cannot tell"  # nothing aligned counts as p = 1
    assert verdict(6, 0.001, 61, CARD) == "cannot tell"  # 6 of 61 is inside the top 10%
    assert verdict(7, 0.001, 61, CARD) == "no"
    assert verdict(None, None, 61, CARD) == "not placed"


def test_p_floor_says_when_p_cannot_reach_the_bar():
    assert p_floor(1, 1000) == 1.0
    assert p_floor(4, 1000) == pytest.approx((1 + 1000 / 24) / 1001)
    assert p_floor(4, 1000) > 0.01  # four aligned points: 24 orders, p never reaches 0.01
    assert p_floor(5, 1000) < 0.01
    assert p_floor(40, 1000) == pytest.approx(1 / 1001)


def test_known_answer_rule():
    assert ka_passed(1, 0.001, 0.5, 0.01)
    assert ka_passed(1, 0.001, None, 0.01)  # the scrambled version aligned nothing
    assert not ka_passed(2, 0.001, 0.5, 0.01)
    assert not ka_passed(1, 0.02, 0.5, 0.01)
    assert not ka_passed(1, None, 0.5, 0.01)
    assert not ka_passed(1, 0.001, 0.005, 0.01)  # scrambling did not break the order test


def test_scramble_is_seeded_and_never_the_original_order():
    paras = [f"p{i}" for i in range(8)]
    a = scramble(paras, "20261130:scramble")
    assert a == scramble(paras, "20261130:scramble")
    assert sorted(a) == sorted(paras) and a != paras
    assert paras == [f"p{i}" for i in range(8)]  # the input is left as it was
    assert scramble(["x", "y"], 0) == ["y", "x"]
    assert scramble(["only"], 0) == ["only"]
    assert paragraphs("a b\n\n  c\nd \n \n\ne") == ["a b", "c d", "e"]


def test_outline_jobs_of_both_variants():
    texts = {"t": " ".join(f"w{i}" for i in range(12)), "empty": "  "}
    blocks = outline_jobs(texts, "blocks", CARD)
    assert [j["id"] for j in blocks] == ["blocks|t|0|3", "blocks|t|1|3", "blocks|t|2|3"]
    whole = outline_jobs(texts, "whole", CARD)
    assert [j["id"] for j in whole] == ["whole|t|0|1"]
    assert "w0 w1" in whole[0]["prompt"] and "w11" in whole[0]["prompt"]
    for word in ("mormon", "nephi", "chapin", "sermon", "universal"):
        assert word not in whole[0]["prompt"].lower()
    assert split_id("blocks|ib:1|2|3") == ("blocks", "ib:1", 2, 3)
    with pytest.raises(ValueError):
        outline_jobs(texts, "pages", CARD)


def test_outlines_wait_for_every_block():
    jobs = outline_jobs({"a": "x " * 12, "b": "y y y"}, "blocks", CARD)
    ans = [
        {"id": "blocks|a|1|3", "reply": "- two\n- three"},
        {"id": "blocks|a|0|3", "reply": "- one"},
        {"id": "blocks|a|2|3", "reply": "I cannot read this"},
    ]
    got = outlines_of(jobs, ans, 12)
    assert got["points"] == {"a": ["one", "two", "three"]}
    assert got["open"] == {"b": 1} and got["unreadable"] == ["blocks|a|2|3"]
    got = outlines_of(jobs, [*ans, {"id": "blocks|b|0|1", "reply": "NONE"}], 12)
    assert got["points"]["b"] == [] and not got["open"]


def test_place_counts_ties_against_the_text():
    others = [5.0, 3.0, 3.0, 1.0] + [0.0] * 16
    tie = place(5.0, 0.001, 8, others, CARD)
    assert tie["rank"] == 2 and tie["of"] == 21 and tie["verdict"] == "cannot tell"
    top = place(6.0, 0.001, 8, others, CARD)
    assert top["rank"] == 1 and top["verdict"] == "stands out" and top["p_can_reach_bar"]
    short = place(6.0, 0.04, 4, others, CARD)
    assert short["verdict"] == "cannot tell" and not short["p_can_reach_bar"]


def test_a_planted_outline_in_order_gives_a_small_p_and_reversed_does_not():
    eye = np.eye(64)
    points, noise = eye[:8], eye[8:40]
    cand = np.concatenate([noise[:10], points, noise[10:20]])
    got = order_test(points, cand, 0.9, 7, CARD)
    assert got["matched"] == 8 and got["span"] == 8
    assert got["order_p"] <= 0.01
    rev = np.concatenate([noise[:10], points[::-1], noise[10:20]])
    bad = order_test(points, rev, 0.9, 7, CARD)
    assert bad["matched"] == 1 and bad["order_p"] > 0.01
    empty = order_test(points, np.zeros((0, 64)), 0.9, 7, CARD)
    assert empty["order_p"] is None and empty["span"] == 0


def test_anchored_points_follow_their_markers():
    from lab.sermon_outline import anchor, in_marker_order

    assert anchor([f"w{i}" for i in range(5)], 2) == "[1] w0 w1 [2] w2 w3 [3] w4"
    pts, lost = in_marker_order(["late point. [9]", "early [2].", "no marker", "also early [2]"])
    assert pts == ["early", "also early", "late point."] and lost == 1
    pts, lost = in_marker_order(["c [6, 7, 8]", "a [1-3]", "b [3 – 4]", "x [2] then"])
    assert pts == ["a", "b", "c"] and lost == 1
    jobs = outline_jobs({"t": "a b c d e"}, "anchored", {**CARD, "anchor_words": 2})
    assert jobs[0]["id"] == "anchored|t|0|1" and "[3] e" in jobs[0]["prompt"]
    got = outlines_of(jobs, [{"id": "anchored|t|0|1", "reply": "- second [3]\n- first [1]"}], 12)
    assert got["points"] == {"t": ["first", "second"]} and got["unanchored"] == 0
