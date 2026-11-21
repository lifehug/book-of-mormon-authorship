"""BOM-105 follow-up: the encoder version's own pieces behave as stated (no model, no text)."""

import numpy as np

from lab.twovoices import cosine_delta
from lab.twovoices_enc import chunk_ids, fw_voice_or_person, gaps, voice_or_person

CFG = {"lab": {"two_voices": {"seed": 1, "profile_chunks": 2, "resamples": 20}}}


def _unit(*xs):
    v = np.array(xs, dtype=float)
    return v / np.linalg.norm(v)


def test_a_chunk_is_cut_to_one_trained_episode():
    assert len(chunk_ids(list(range(1300)), 128, 8)) == 1024
    assert len(chunk_ids(list(range(900)), 128, 8)) == 900


def test_gap_index_is_large_for_a_writer_whose_voices_differ():
    # "a" has two unlike voices; "b" and "c" write alike in both
    a = {"prophetic": np.array([_unit(1, 0, 0)] * 3), "ordinary": np.array([_unit(0, 1, 0)] * 3)}
    b = {
        "prophetic": np.array([_unit(0, 1, 0.1)] * 3),
        "ordinary": np.array([_unit(0, 1, 0.2)] * 3),
    }
    c = {
        "prophetic": np.array([_unit(0, 1, 0.3)] * 3),
        "ordinary": np.array([_unit(0, 1, 0.4)] * 3),
    }
    g = gaps({"a": a, "b": b, "c": c}, CFG, cosine_delta)
    assert g["order_by_gap_index"][0] == "a"


def test_voice_or_person_counts_writers_nearer_the_other_voice():
    # scripture voices all alike, ordinary voices all different: grouped by voice
    z = {
        w: {"prophetic": np.array([_unit(1, 0, 0, 0)]), "ordinary": np.array([_unit(0, *o)])}
        for w, o in (("a", (1, 0, 0)), ("b", (0, 1, 0)), ("c", (0, 0, 1)))
    }
    r = voice_or_person(z)
    assert r["share_by_voice_mean"] == 1.0 and r["share_by_voice_closest"] == 1.0


def test_function_word_count_reads_medians():
    fw = {
        "gaps": {
            "per_writer": {
                "a": {"median_delta_to_other_prophetic": [0, 0.5, 0], "self_gap": [0, 0.9, 0]},
                "b": {"median_delta_to_other_prophetic": [0, 0.9, 0], "self_gap": [0, 0.5, 0]},
            }
        }
    }
    assert fw_voice_or_person(fw) == {"by_voice": {"a": True, "b": False}, "share_by_voice": 0.5}
