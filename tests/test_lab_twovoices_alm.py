"""BOM-105 follow-up: the author-model version's own pieces behave as stated (no model, no text)."""

import numpy as np

from lab.twovoices_alm import (
    analyse,
    attribution,
    larger_sequences,
    place,
    split,
    voice_or_person,
    wilson,
)

CFG = {
    "lab": {
        "two_voices": {"known_bar": 0.8, "cross_share": 0.5, "min_writers": 2},
    }
}


def test_split_holds_out_only_words_no_training_token_touched():
    words = [f"w{i}" for i in range(10)]
    text = " ".join(words)
    # one token per word, offsets into the joined text
    offs, pos = [], 0
    for w in words:
        offs.append((pos, pos + len(w)))
        pos += len(w) + 1
    ids = list(range(10))
    tr, used, held = split(words, ids, offs, 3, 2)
    assert tr == [0, 1, 2] and used == 3
    assert held == [["w3", "w4"], ["w5", "w6"], ["w7", "w8"]]  # last partial chunk dropped
    assert text  # joined form is what the offsets index
    assert split(words, ids, offs, 11, 2) == ([], 0, [])


def test_larger_dose_is_the_most_that_leaves_enough_held_out():
    # 10,000 words at one token a word; 1,000-token sequences; 1,000-word chunks; need 5 chunks
    s = larger_sequences({"a": 10_000}, 1000, 11, 2, 5, 1000, {"a": 1.0})
    assert s == 5
    assert larger_sequences({"a": 3_000}, 1000, 11, 2, 5, 1000, {"a": 1.0}) == 0


def test_wilson_interval_brackets_the_rate():
    lo, hi = wilson(8, 10)
    assert lo < 0.8 < hi
    assert wilson(0, 0) is None


def test_place_uses_the_range_rule():
    assert place(0.5, [0.2, 0.9], "above", "below") == "typical"
    assert place(1.0, [0.2, 1.0], "above", "below") == "typical"
    assert place(0.1, [0.2, 0.9], "above", "below") == "below"
    assert place(0.95, [0.2, 0.9], "above", "below") == "above"


def _toy():
    """Three writers; each model fits its own writer's chunks in both voices best (-1), so the
    person is found across the voice."""
    writers = ["a", "b", "joseph_smith"]
    names = [f"{w}|{v}" for w in writers for v in ("prophetic", "ordinary")]
    meta = [(w, v, i) for w in writers for v in ("prophetic", "ordinary") for i in range(3)]
    S = np.zeros((len(meta), len(names)))
    for r, (w, _, _) in enumerate(meta):
        for c, n in enumerate(names):
            S[r, c] = -1.0 if n.split("|")[0] == w else 0.0
    return S, meta, writers, {n: i for i, n in enumerate(names)}


def test_attribution_and_pull():
    S, meta, writers, ix = _toy()
    r = attribution(S, meta, ix, writers, "prophetic", "ordinary")
    assert r["macro"] == 1.0 and all(p == 0.0 for p in r["pull"].values())
    assert r["per_writer"]["a"]["mean_own_rank"] == 1.0


def test_analyse_finds_the_person_and_places_joseph_smith():
    S, meta, writers, _ = _toy()
    res = analyse(S, meta, writers, CFG)
    assert res["known_answer"]["passed"]
    v = res["verdicts"]
    assert v["others_crossing"] == 2 and not v["genre_effect"]
    assert v["joseph_smith"]["ordinary_models_on_scripture_chunks"]["rate"] == "typical"


def test_voice_or_person_counts_scripture_models_that_beat_own_ordinary():
    S, meta, writers, ix = _toy()
    # make every scripture-voice model fit every scripture chunk best: grouped by voice
    for r, (_, v, _) in enumerate(meta):
        if v == "prophetic":
            for n, c in ix.items():
                S[r, c] = -2.0 if n.endswith("|prophetic") else 0.0
    vp = voice_or_person(S, meta, ix, writers)
    assert all(p["any_other_beats_own_ordinary"] == 1.0 for p in vp.values())


def test_analyse_stops_when_the_known_answer_misses():
    S, meta, writers, _ = _toy()
    res = analyse(np.zeros_like(S), meta, writers, CFG)  # all ties: names decide, a wins
    assert not res["known_answer"]["passed"] and "cross_voice" not in res
