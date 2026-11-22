"""BOM-112: the Dale and Dale checklist is keyed by rule and its arithmetic reproduced."""

import math
import re

import pytest

from lab import dalechecklist as d
from lab import dalechecklist_coding as coding
from metadata import config


def test_toy_product_and_their_example():
    assert math.isclose(10 ** d.log10_product([0.5, 0.1, 0.02]), 0.001)
    assert d.sci(131 * math.log10(0.5)) == "3.67e-40"
    assert d.matches(math.log10(2.69e-151), 2.69e-151, 0.005)
    assert not d.matches(math.log10(2.0e-13), 4.0e-14, 0.005)


def test_posterior_is_prior_times_ratios():
    lg = d.posterior([0.1, 0.1], [10.0], 1e9)
    assert math.isclose(lg, 9 - 2 + 1)


FRAGMENT = """1. Political Correspondences
1.1 First feature of the
city
  Coe's standard: quoted words (p. 1).
  Analysis of correspondence: Specific. Likelihood = 0.02.
1.2 Second feature
  Coe's standard: words.
  Analysis: we do not think this merits a likelihood of 0.02, but Likelihood = 0.1.
Calculation of overall likelihood for political correspondences
Nine have a likelihood of 0.5.
"""


def test_items_split_label_ratio_and_stop_at_summary():
    rows = d._lines_with_pages(FRAGMENT, 99)
    head = re.compile(r"^\s{0,4}(?P<num>\d\.\d{1,2})\.?\s+(?P<label>[A-Z].*)$")
    got = d._items(rows[1:], head)
    assert [g["num"] for g in got] == ["1.1", "1.2"]
    assert got[0]["label_full"] == "First feature of the city"
    assert got[0]["ratio"] == 0.02
    assert got[1]["ratio"] == 0.1  # the last stated ratio, not the section summary's
    assert got[0]["page"] == 99


def test_footnote_numbers_do_not_start_items():
    text = "1. Horses existed\n Likelihood = 50.0.\n 42. A footnote line\n"
    text += "2. Wheat existed\n weight of 2.0\n"
    rows = d._lines_with_pages(text, 1)
    head = re.compile(r"^\s{0,4}(?P<num>\d{1,2})\.\s+(?P<label>[A-Z].*)$")
    got = d._items(rows, head, sequential=True)
    assert [g["num"] for g in got] == ["1", "2"]
    assert [g["ratio"] for g in got] == [50.0, 2.0]


def test_short_label_cuts_at_a_word():
    assert (
        d.short("“Capital” or leading city-state dominates a cluster", 20)
        == "Capital or leading ..."
    )


def test_coding_table_is_complete_and_valid():
    assert len(coding.ADDED) == 131
    assert len(coding.NEG_GROUP) == 18
    for v in coding.ADDED.values():
        assert v["near_east"] in coding.VALUES and v["generic"] in coding.VALUES
    for pat in coding.KEYWORDS.values():
        re.compile(pat)
    assert set(coding.FEATURE) == set(coding.KEYWORDS)


def test_candidates_rank_by_distinct_terms_without_overlap():
    text = " ".join(["filler"] * 50 + ["king", "throne", "palace"] + ["filler"] * 50 + ["king"])
    got = d.candidates(text, re.compile(r"\b(king|throne|palace)\b"), 10, 5, 2)
    assert len(got) == 2
    assert "throne" in got[0] or "throne" in got[1]


@pytest.mark.skipif(not (d.PDF.exists() or d.TEXT.exists()), reason="private paper not held")
def test_known_answer_on_the_paper():
    cfg = config.load()
    k = d.keyed(cfg)
    ka = d.known_answer(k["items"], cfg)
    assert ka["passed"]
    assert all(ka["counts_ok"].values())
    assert set(ka["discrepancies_in_the_paper"]) == {"military"}
