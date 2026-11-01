import numpy as np

from eval.known_answer import GENUINE, MODERN, SET, separation
from reuse.rare import doc_freq, p_value


def test_p_value_counts_ties_against_the_source():
    null = np.array([0.0, 0.0, 1.0, 2.0])
    assert p_value(null, 2.0) == 2 / 5
    assert p_value(null, 3.0) == 1 / 5


def test_doc_freq_by_volume_counts_every_copy():
    recs = [{"work_id": "a", "hits": [1, 2]}, {"work_id": "b", "hits": [1]}]
    assert doc_freq(recs, by_text=False) == {1: 2, 2: 1}


def test_separation_on_a_perfect_split():
    cfg = {"known_answer": {"separation_p": 0.01}}
    groups = {k: g for k, g, primary, *_ in SET if primary}
    scores = {k: (1.0 + i if g == MODERN else 0.1 * i) for i, (k, g) in enumerate(groups.items())}
    res = separation(scores, cfg)
    assert sum(g == GENUINE for g in groups.values()) == 9
    assert res["U"] == res["of"] == 27 and res["p"] == 1 / 220 and res["separates"]
