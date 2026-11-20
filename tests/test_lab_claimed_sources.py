"""BOM-126: the lookup's own pieces: finding copies, placing a score, cutting queries by chapter."""

from collections import Counter

import numpy as np

from lab.claimed_sources import (
    best_meaning,
    find_copies,
    meaning_row,
    place,
    rare_row,
    target_queries,
)


def test_find_copies_needs_author_and_title():
    cat = [
        {"work_id": "a", "title": "The pilgrim's progress", "author_norm": "bunyan, john"},
        {"work_id": "b", "title": "A review of The pilgrim's progress", "author_norm": "x, y"},
        {"work_id": "c", "title": "The holy war", "author_norm": "bunyan, john"},
        {"work_id": "d", "title": None, "author_norm": "bunyan, john"},
    ]
    found = find_copies({"pp": ["^bunyan, john", r"^\W*(the )?pilgrim.?s progress"]}, cat)
    assert found == {"pp": ["a"]}
    assert find_copies({"any": ["", "pilgrim"]}, cat) == {"any": ["a", "b"]}


def test_place_counts_sample_scores_above():
    sample = np.sort(np.linspace(0, 1, 1001))
    p = place(0.9, sample, 1_000_000)
    assert p["sample_above"] == 100
    assert p["estimated_rank"] == 1 + round(100 / 1001 * 1_000_000)
    assert place(2.0, sample, 1_000_000)["estimated_rank"] == 1


def test_target_queries_take_the_majority_of_words():
    paras = [Counter({1: 128}), Counter({1: 60, 2: 68}), Counter({2: 64, 3: 64}), Counter({3: 128})]
    assert target_queries(paras, {2}) == [1]
    assert target_queries(paras, {2, 3}) == [1, 2, 3]


def test_a_volume_outside_a_population_is_not_a_zero():
    t = {"rank": {"a": 1}, "population": 2, "density": {"a": 3.0}, "shared": {"a": 2},
         "words": {"a": 100}, "null": np.array([0.0, 3.0])}  # fmt: skip
    assert rare_row("b", t) is None
    row = rare_row("a", t)
    assert row["rank"] == 1 and row["tied_at_zero"] is False
    assert meaning_row("b", {}, {"b"})["status"] == "in the gallery, no parallel"
    assert meaning_row("c", {}, {"b"})["status"] == "not in the gallery"


def test_best_copy_is_highest_percentile_then_rank():
    ranking = {
        "a": {"work_id": "a", "percentile": 90.0, "rank": 5},
        "b": {"work_id": "b", "percentile": 99.0, "rank": 9},
        "c": {"work_id": "c", "percentile": 99.0, "rank": 7},
    }
    assert best_meaning(["a", "b", "c", "zz"], ranking) == "c"
    assert best_meaning(["zz"], ranking) is None
