"""BOM-104: the dictations test's own pieces behave as stated (no model, no text)."""

import numpy as np

from lab.dictations import (
    PUBLISHED,
    combined,
    known_answer,
    lecture_table,
    pieces,
    profiles,
    spearman,
    strip_editorial,
    votes,
)
from lab.dictations_alm import scored_keys

T = {"known_bar": 0.8, "min_each": 0.5, "profile_chunks": 2, "resamples": 50, "seed": 1,
     "clear_share": 0.95}  # fmt: skip
CANDS = ["a", "b"]


def test_strip_editorial_drops_page_marks_and_keeps_supplied_words():
    s = strip_editorial("came [to] pass [p. 12] and -[§ iii. ¶ 26.]- end [page blank]")
    assert "to pass" in s and "p." not in s and "§" not in s and "blank" not in s


def test_pieces_keep_a_long_enough_tail():
    toks = [str(i) for i in range(2600)]
    assert [len(p) for p in pieces(toks, 1000, 500)] == [1000, 1000, 600]
    assert [len(p) for p in pieces(toks[:2300], 1000, 500)] == [1000, 1000]


def _scores(right_a: int, right_b: int, n: int = 10) -> dict:
    sc = {}
    for i in range(n):
        sc[f"cand|a|test|{i}"] = {"a": 0.0, "b": 1.0} if i < right_a else {"a": 1.0, "b": 0.0}
        sc[f"cand|b|test|{i}"] = {"a": 1.0, "b": 0.0} if i < right_b else {"a": 0.0, "b": 1.0}
    return sc


def test_known_answer_needs_the_macro_and_every_candidate():
    ok = known_answer(_scores(9, 8), CANDS, T)
    assert ok["passed"] and ok["macro"] == 0.85
    one_low = known_answer(_scores(10, 4), CANDS, T)  # macro 0.7 and b below min_each
    assert not one_low["passed"] and one_low["own_rate"]["b"] == 0.4
    assert one_low["pull"]["a"] == 0.6  # six of b's ten chunks drawn to a


def test_votes_and_lecture_table_pick_the_lowest():
    sc = {"lecw|1": {"a": 0.2, "b": 0.5}, "lec|1|0": {"a": 0.9, "b": 0.1},
          "lec|1|1": {"a": 0.1, "b": 0.3}}  # fmt: skip
    t = lecture_table(sc, CANDS, sc.keys())
    assert t["1"]["winner"] == "a" and t["1"]["margin"] == 0.3
    assert t["1"]["piece_votes"] == {"b": 1, "a": 1}
    assert votes(sc, ["lec|1|0"], CANDS) == {"b": 1}


def test_spearman_signs():
    assert spearman([0, 1, 2, 3], [1, 2, 3, 4]) == 1.0
    assert spearman([0, 1, 2, 3], [4, 3, 2, 1]) == -1.0


def test_profiles_find_a_growing_distance_and_the_nearer_reference():
    rng = np.random.default_rng(0)
    vecs = {}
    for i in range(6):
        vecs[f"bom|{i}"] = rng.normal(0, 0.01, 3)
        for c in CANDS:
            vecs[f"cand|{c}|train|{i}"] = rng.normal(5, 0.01, 3)
        # revelation periods drift away from the book; joseph_smith is the ordinary reference
        for p, shift in (("rev_1828-30", 0.0), ("rev_1831", 1.0), ("rev_1832", 2.0),
                         ("rev_1833-34", 3.0)):  # fmt: skip
            vecs[f"grp|{p}|{i}"] = rng.normal(shift, 0.01, 3)
    groups = ["rev_1828-30", "rev_1831", "rev_1832", "rev_1833-34"]
    vecs.update({f"cand|joseph_smith|train|{i}": rng.normal(5, 0.01, 3) for i in range(6)})
    res = profiles(
        vecs, groups, ["joseph_smith", *CANDS], lambda x, y: float(np.mean(np.abs(x - y))), T
    )
    assert res["years_revelations_to_bom"]["verdict"] == "grows"
    assert res["groups"]["rev_1828-30"]["verdict_bom_vs_ordinary"] == "closer to the Book of Mormon"


def test_combined_needs_every_passing_measure_to_agree():
    lec = {str(n): {"winner": "sidney_rigdon"} for n in range(1, 8)}
    other = {str(n): {"winner": "sidney_rigdon" if n != 5 else "joseph_smith"}
             for n in range(1, 8)}  # fmt: skip
    res = combined({"encoder_bom30": {"lectures": lec}, "encoder_v2": {"lectures": other},
                    "function_words_burrows": {"stopped": "missed"}}, None)  # fmt: skip
    assert res["per_lecture"]["1"]["attributed"] == "sidney_rigdon"
    assert res["per_lecture"]["5"]["attributed"] == "measures disagree"
    assert res["agreement_with_published"]["reynolds_2005"]["combined"] == 6
    assert res["agreement_with_published"]["phipps_1977"]["encoder_v2"] == 7
    assert set(PUBLISHED["phipps_1977"].values()) == {"sidney_rigdon", "joseph_smith"}


def test_author_models_score_everything_but_training_chunks():
    b = {"items": {"cand|a|train|0": [], "cand|a|test|0": [], "bom|0": []},
         "whole": {"lecw|1": []}}  # fmt: skip
    assert scored_keys(b) == ["bom|0", "cand|a|test|0", "lecw|1"]


def test_v2_series_rule_keeps_blockquotes_only():
    from lab.dictations_v2 import series_text

    raw = (
        "<p>Editor's introduction</p><blockquote><center>Vol. II. Kirtland</center>"
        "<p align=center>MILLENIUM. No. I.</p>T<small>HE</small> subject [Isa. LII. 8] is "
        "{Continued from our last.} plain. TO BE CONTINUED.</blockquote><p>Editor's note</p>"
    )
    words = series_text(raw).split()
    assert words == ["THE", "subject", "is", "plain."]


def test_v2_settings_override_the_first_attempt():
    from lab.dictations_v2 import settings

    cfg = {"lab": {"dictations": {"train_chunks": 8, "known_bar": 0.8,
                                  "v2": {"train_chunks": 20}}}}  # fmt: skip
    t = settings(cfg)
    assert t["train_chunks"] == 20 and t["known_bar"] == 0.8 and "v2" not in t
