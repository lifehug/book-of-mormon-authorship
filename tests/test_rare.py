"""BOM-45: rare-phrase scoring pieces."""

from reuse import rare


def test_gram_ids_counts_distinct_ngrams():
    toks = "the late war between the united states".split()
    assert len(rare.gram_ids(toks, 4)) == 4
    assert rare.gram_ids(toks, 4) == rare.gram_ids(list(toks), 4)  # stable hashing


def test_scores_count_only_rare_shared_grams_per_length():
    recs = [{"work_id": "a", "words": 10000, "hits": [1, 2]},
            {"work_id": "b", "words": 5000, "hits": [2]},
            {"work_id": "c", "words": 20000, "hits": [2, 3]}]  # fmt: skip
    # gram 2 is in 3 documents: with max_df 2 it is not rare
    sc = rare.scores(recs, max_df=2, per_words=10000)
    assert sc == {"a": 1.0, "b": 0.0, "c": 0.5}
