"""BOM-103: topic rules, decade profiles against the gallery's shape, and the hit rule."""

import numpy as np

from lab.debates import compile_topics, death_year, decades, hit, l1, profile, topics_of
from metadata.config import load


def test_topic_rule_needs_every_group_and_enough_hits():
    topics = compile_topics({"topics": {"infant_baptism": [r"\bbapti[sz]", r"\binfants?\b"]}})
    assert topics_of("Infants need no baptism, for baptizing them is vain", topics, 2) == [
        "infant_baptism"
    ]
    assert topics_of("he was baptized in the river", topics, 2) == []
    assert topics_of("one infant", topics, 2) == []


def test_configured_topics_compile_and_catch_their_own_wording():
    d = load()["lab"]["debates"]
    topics = compile_topics(d)
    assert len(topics) >= 15
    text = "they did build up secret combinations and did administer their oaths and covenants"
    assert "secret_combinations" in topics_of(text, topics, d["min_hits"])
    assert decades(d)[0] == 1640 and decades(d)[-1] == 1820


def test_profile_divides_by_the_gallery_shape():
    decs = [1780, 1790, 1800, 1810, 1820]
    base = np.array([0.05, 0.05, 0.1, 0.3, 0.5])
    # Neighbours in proportion to the gallery: no decade stands out (all ratios 1).
    flat = profile(np.array([5, 5, 10, 30, 50]), base, decs, 1)
    assert all(abs(r - 1) < 1e-9 for r in flat["ratio"].values())
    # Few in absolute terms, but far above the 1780s' share: the peak is the 1780s.
    early = profile(np.array([20, 10, 10, 25, 35]), base, decs, 0)
    assert early["peak_decade"] == 1780
    assert early["median_decade"] == 1810
    assert l1(flat, flat) == 0


def test_hit_window_and_death_years():
    assert hit(1750, 1740, 1) and hit(1730, 1740, 1) and not hit(1760, 1740, 1)
    assert death_year("Bunyan, John, 1628-1688.") == 1688
    assert death_year("Watts, Isaac, d. 1748") == 1748
    assert death_year("Smith, Ethan") is None
