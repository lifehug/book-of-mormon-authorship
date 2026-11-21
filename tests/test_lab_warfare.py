"""BOM-115: the war terms match what the card says, and the rule and the placement behave."""

from collections import Counter

import numpy as np

from lab.warfare import (
    CRX,
    NAMES,
    RX,
    chapter_map,
    cosine,
    figure_stats,
    figures,
    min_span,
    passage_chapters,
    pick_threshold,
    profile,
    repair_long_s,
)

CFG = {
    "lab": {
        "numbers": {"year_lo": 1000, "year_hi": 1899},
        "warfare": {
            "figure_span": 8,
            "figure_min": 10,
            "casualty_words": ["slain", "killed"],
            "density_grid": [0.01, 0.02],
            "fpr_max": 0.05,
            "tpr_min": 0.4,
        },
    }
}


def n(name: str, text: str) -> int:
    return len(RX[name].findall(text))


def test_terms_match_as_the_card_says():
    assert n("cimeter", "a scimitar and two cimeters and a scymitar") == 3
    assert n("bow", "the bow and the bows but they bow down and bow before him") == 2
    assert n("captain", "the captain and chief captain and captains") == 2
    assert n("chief_captain", "the captain and chief captain and captains") == 1
    assert n("arm_shield", "arm shields and shields") == 1
    assert n("shield", "arm shields and shields and a shield") == 2
    assert n("heap_of_earth", "heaps of earth and a heap of dirt") == 2
    assert n("flag", "a flag, a white flag, a flag of truce") == 1
    assert n("flag_of_truce", "a flag, a white flag, a flag of truce") == 2
    assert n("stronghold", "a strong hold and a stronghold") == 2
    assert n("breastplate", "breast plate breastplates") == 2
    assert n("month_named", "in march and may and june") == 1


def test_every_term_has_a_class_and_a_regex():
    assert len(NAMES) == len({name for _, name in NAMES}) == len(RX)
    assert {c for c, _ in NAMES} == {
        "weapons", "armour", "fortification", "organisation", "prisoners", "time"
    }  # fmt: skip


def test_cluster_groups():
    assert len(CRX["ditch"].findall("a ditch and trenches")) == 2
    assert len(CRX["pickets"].findall("pickets, a palisade and a stockade")) == 3
    assert len(CRX["bank"].findall("a bank of earth, heaps of dirt, an embankment")) == 3


def test_min_span_finds_the_tightest_stretch():
    pos = {g: np.array(p) for g, p in {"a": [0, 50], "b": [60], "c": [55, 200]}.items()}
    assert min_span(pos, ["a", "b", "c"]) == (11, 50)
    assert min_span({"a": np.array([1]), "b": np.array([])}, ["a", "b"]) is None


def test_long_s_repair_changes_only_what_is_not_a_word():
    vocab = Counter({"sword": 5, "the": 9, "fire": 4, "fought": 3, "stone": 2})
    assert repair_long_s("the fword and the ftone", vocab) == "the sword and the stone"
    assert repair_long_s("the fire fought", vocab) == "the fire fought"
    assert repair_long_s("the ſword", vocab) == "the sword"


def test_threshold_is_the_smallest_with_few_false_alarms():
    peace = np.array([0.0] * 95 + [0.015] * 5)  # 5% at 0.01 and below
    war = np.array([0.03] * 5 + [0.0] * 5)
    rule = pick_threshold({"kjv_new_testament": peace, "josephus_wars_whiston": war}, CFG)
    assert rule["chosen"] == 0.01
    assert rule["passed"] is True
    weak = pick_threshold({"kjv_new_testament": peace, "josephus_wars_whiston": war * 0}, CFG)
    assert weak["passed"] is False


def test_figures_split_armies_from_casualties():
    text = (
        "an army of ten thousand men came to the city that stood upon the plain by the river "
        "and in the battle that followed twelve thousand were slain"
    )
    got = figures(text, CFG)
    assert [(v, c) for v, _u, _i, c, _a in got] == [(10000, False), (12000, True)]
    stats = figure_stats([1000, 2000, 50])
    assert (
        stats["n"] == 3 and stats["max"] == 2000 and stats["share_round_thousands_of_those"] == 1.0
    )


def test_profile_similarity_and_the_passage_finder():
    a, b = np.array([4, 0, 1]), np.array([4, 0, 1])
    assert cosine(profile(a, 10000), profile(b, 10000)) > 0.999
    assert cosine(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 0.0
    paras = [
        ("Alma", 1, "heaps of earth and timbers"),
        ("Alma", 1, "pickets and towers"),
        ("Alma", 2, "heaps of earth"),
    ]
    assert passage_chapters(paras) == [("Alma", 1)]
    starts, chap = chapter_map(paras)
    assert starts == [0, 5, 8] and chap[2] == ("Alma", 2)
