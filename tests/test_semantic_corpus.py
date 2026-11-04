"""Whole-corpus semantic scoring (BOM-25): a source's score counts queries, not passages."""

import numpy as np

from semantic.corpus import _source_scores


def test_source_score_counts_each_query_once_and_only_scored_queries():
    hit_vol = [{"a", "b"}, {"a"}, {"a"}]
    scored = np.array([True, True, False])  # the third query is mostly King James: not scored
    sc = _source_scores(hit_vol, scored, scored_words=200)
    assert sc == {"a": 10000 * 2 / 200, "b": 10000 * 1 / 200}
