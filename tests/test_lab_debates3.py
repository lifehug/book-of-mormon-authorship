"""BOM-103 third design: topic rules, profile distances, placement, verdict and era helpers."""

import numpy as np

from lab.debates3 import (
    adjacent,
    blocks,
    compile_topics,
    counts_of,
    draw,
    era_of,
    is_reprint,
    jsd,
    life_eras,
    norm,
    parse_yes_no,
    part_b_parse,
    placed_era,
    shares,
    topics_of,
    verdict,
)
from metadata.config import load

ERAS = {"E1": [1640, 1659], "E2": [1660, 1699], "E3": [1700, 1769], "E4": [1770, 1799],
        "E5": [1800, 1814], "E6": [1815, 1829]}  # fmt: skip


def test_topic_rule_needs_every_group_and_enough_hits():
    c = compile_topics({"a": [r"\bbapti[sz]", r"\binfants?\b"], "b": [r"sabbath"]})
    assert topics_of(norm("Infants need no BAPTISM,  for baptizing them"), c, 2) == [0]
    assert topics_of("he was baptized in the river", c, 2) == []
    assert topics_of("the sabbath", c, 2) == []  # one match is not enough
    assert topics_of("the sabbath and the sabbath", c, 2) == [1]


def test_configured_rules_compile_and_match_both_registers():
    d = load()["lab"]["debates3"]
    c = compile_topics(d["topics"])
    names = list(d["topics"])
    assert len(names) == 39 and set(d["campbell"].values()) <= set(names)
    assert set(d["markers"]) <= set(names) and set(d["survey_terms"]) == set(names)
    kj = "and they went forth to preach the word among the heathen"
    assert names.index("missions_bible_societies") in topics_of(kj, c, d["min_hits"])
    plain = "the bible society sent a missionary to the heathen"
    assert names.index("missions_bible_societies") in topics_of(plain, c, d["min_hits"])


def test_shares_and_distance():
    p = shares(np.array([10, 0, 0]), 0.5)
    assert abs(p.sum() - 1) < 1e-12 and p[0] > p[1] == p[2]
    assert jsd(p, p) == 0
    a, b = np.array([1.0, 0.0]), np.array([0.0, 1.0])
    assert abs(jsd(a, b) - 1.0) < 1e-9
    q = shares(np.array([5, 5, 0]), 0.5)
    assert 0 < jsd(p, q) < 1 and abs(jsd(p, q) - jsd(q, p)) < 1e-12
    assert list(counts_of([[0, 2], [2]], 3)) == [1, 0, 2]


def test_draw_flags_replacement():
    rng = np.random.default_rng(0)
    idx, rep = draw(150, 100, rng)
    assert len(set(idx.tolist())) == 100 and not rep
    idx, rep = draw(30, 100, rng)
    assert len(idx) == 100 and rep


def test_eras_reprints_and_life():
    assert era_of(1645, ERAS) == "E1" and era_of(1829, ERAS) == "E6" and era_of(1830, ERAS) is None
    assert is_reprint(1688, 1825, 30) and not is_reprint(1800, 1825, 30)
    assert not is_reprint(None, 1825, 30)
    assert life_eras(1688, ERAS, 40) == {"E1", "E2"}
    assert life_eras(1546, ERAS, 40) == {"E1"}  # Luther: before the first era
    assert life_eras(1748, ERAS, 40) == {"E3"}
    assert adjacent("E2", "E3", list(ERAS)) and not adjacent("E1", "E3", list(ERAS))


def test_placement_and_verdict():
    med = {"E1": 0.3, "E6": 0.2}
    assert placed_era(["E1", "E6", "E6"], med) == "E6"
    assert placed_era(["E1", "E6"], med) == "E6"  # tie: smaller median distance
    d = {"yes_share": 0.8, "yes_gap_share": 0.95, "no_share": 0.8, "no_rank": 3}
    assert verdict({"E6": 0.9}, 1.0, 1, False, d) == "yes"
    assert verdict({"E6": 0.9}, 0.9, 1, False, d) == "cannot tell"
    assert verdict({"E2": 0.85, "E6": 0.15}, 0.0, 2, False, d) == "no"
    assert verdict({"E5": 0.6, "E6": 0.4}, 0.5, 3, False, d) == "no"
    assert verdict({"E6": 1.0}, 1.0, 1, True, d) == "cannot tell"


def test_blocks_and_parsers():
    b = blocks(" ".join(str(i) for i in range(10)), 4)
    assert len(b) == 4 and sum(len(x.split()) for x in b) == 10
    assert parse_yes_no(" Yes.") == "YES" and parse_yes_no("maybe") is None
    assert part_b_parse("AGAINST, because", "infant_baptism") == "AGAINST"
    assert part_b_parse("KINGS", "infant_baptism") is None
