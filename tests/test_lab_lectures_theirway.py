"""BOM-104 their-way reruns (lab.lectures_theirway) on tiny synthetic data."""

import math

import numpy as np

from lab import lectures_theirway as L

T = {"phipps_skip_within": 1, "phipps_floor_cell": 1}


def test_split_counts_phipps_word_a():
    # Phipps pp. 28-29, the word "a": Pratt and Cowdery, median 13.5, lectures 8 -> 4 to 2.
    pratt, cowdery = [20, 14, 13, 13, 10, 6], [25, 22, 19, 14, 13, 12]
    med, (ah, bh, al, bl) = L.split_counts(pratt, cowdery)
    assert med == 13.5 and (ah, bh, al, bl) == (2, 4, 4, 2)
    assert L.word_odds(pratt, cowdery, 8, T) == 2


def test_split_counts_shares_ties_phipps_word_all():
    # Phipps pp. 29-31, "all": blocks on the median shared out; 4.67 to 1.33 for Pratt.
    pratt, cowdery = [10, 7, 5, 5, 4, 4], [7, 4, 2, 1, 0, 0]
    med, (ah, bh, _, _) = L.split_counts(pratt, cowdery)
    assert med == 4
    assert math.isclose(ah, 4 + 2 / 3) and math.isclose(bh, 1 + 1 / 3)
    assert math.isclose(L.word_odds(pratt, cowdery, 10, T), 3.5)


def test_word_odds_floor_and_skip():
    a, b = [9, 9, 9, 9, 9, 9], [1, 1, 1, 1, 1, 1]
    assert L.word_odds(a, b, 8, T) == 6  # 6 to 0, the zero floored at 1
    assert L.word_odds(a, b, 2, T) == 1 / 6
    assert L.word_odds(a, b, 5, T) is None  # median 5: within 1 of the target, skipped
    assert L.word_odds([5] * 6, [4] * 6, 5, T) is None  # median 4.5, target 5: skipped


def test_six_pairs_twelve_blocks_and_rounds_down():
    blocks = [["a"] * 3 + ["x"] * 997] * 12
    assert L.six("joseph_smith", blocks, "a") == [3] * 6
    assert L.six("x", [["a"] * 19 + ["x"] * 981], "a") == [19]


def test_cut_drops_headings_markers_and_brackets():
    paras = ["MASTHEAD", "FAITH OF THE CHURCH. No. I.", "[Continued from our last.]",
             "The first [sic] words.", "(page 12)", "NO. II.", "More words.", "TO BE CONTINUED.",
             "Other item."]  # fmt: skip
    got = L.cut(paras, r"^FAITH OF THE CHURCH", r"^TO BE CONTINUED")
    assert got == "The first   words.\nMore words."


def test_paragraphs_from_html():
    raw = "<html><P>One <i>two</i>.</P><p>Three&amp;four<br>five</p></html>"
    assert L.paragraphs(raw) == ["One two .", "Three&four", "five"]


def test_stepwise_and_lda_separate_groups():
    rng = np.random.default_rng(0)
    X, y = [], []
    for g, mu in (("a", [0, 0, 0]), ("b", [3, 0, 0]), ("c", [0, 3, 0])):
        for _ in range(8):
            X.append(np.array(mu) + rng.normal(0, 0.3, 3))
            y.append(g)
    X = np.array(X)
    sel = L.stepwise(X, y, 2)
    assert sorted(sel) == [0, 1]
    m = L.LDA(X[:, sel], y)
    post = m.posterior(np.array([3.0, 0.0, 0.0])[sel])
    assert max(post, key=post.get) == "b" and math.isclose(sum(post.values()), 1)


def test_arcsine_rates():
    r = L.arcsine_rates(["a", "b", "a", "c"], ["a", "z"])
    assert math.isclose(r[0], math.asin(math.sqrt(0.5))) and r[1] == 0


def test_count_phrases_and_reynolds_control():
    phrases = {"first": r"\bin the first instance\b", "facts": r"\bfacts?\b"}
    n, c = L.count_phrases("In the first\ninstance, the FACTS; and in the first instance.", phrases)
    assert n == 11 and c == {"first": 2, "facts": 1}
    cfg = {"lab": {"lectures_theirway": {
        "reynolds_phrases": phrases, "reynolds_broad": ["facts"], "reynolds_factor": 1.5,
        "reynolds_smith_max": 0.2, "reynolds_control_share": 0.5}}}  # fmt: skip
    texts = {"rigdon": [("r", "in the first instance " * 2 + "x " * 992)],
             "lectures": [("l", "in the first instance " * 4 + "x " * 984)],
             "joseph_smith": [("s", "x " * 1000)],
             "oliver_cowdery": [("c", "in the first instance " + "x " * 996)]}  # fmt: skip
    res = L.reynolds(cfg, texts)
    assert res["corpora"]["rigdon"]["rate_per_1000"] == 2.0
    assert res["corpora"]["lectures"]["rate_per_1000"] == 4.0
    assert res["reproduced"] is True
    assert res["control"]["oliver_cowdery"]["share_of_rigdon_rate"] == 0.5
    assert res["control_reaches_share"] is True
