"""BOM-129: New Testament phrases in a new sense (lab.newsenses), on made-up inputs."""

from __future__ import annotations

import json

from lab import newsenses as ns

D = {"eras": {"early": [1640, 1779], "late": [1780, 1829]}, "min_uses_per_era": 2,
     "boot": 500, "seed": 1, "period_points": 0.15, "older_points": 0.05}  # fmt: skip


def test_doc_passage_marks_phrase_as_printed():
    doc = ns.Doc("x", "Then said they, Eat, drink, and be merry; for to-morrow we die.")
    s = doc.words.index("eat")
    p = doc.passage(s, s + 5, 2)
    assert p == "said they, [Eat, drink, and be merry]; for to"


def test_mark_allows_punctuation_and_curly_apostrophe():
    assert ns.mark("Bear ye one another’s burdens, and so", "bear ye one another's burdens") == (
        "[Bear ye one another’s burdens], and so"
    )


def test_first_uses_two_word_and_long_phrases():
    table = ns.phrase_table(["few stripes", "eat drink and be merry"])
    words = "he shall be beaten with few stripes and few stripes eat drink and be merry".split()
    assert ns.first_uses(words, table) == {0: 5, 1: 10}
    assert ns.first_uses("eat drink and be sad".split(), table) == {}


def test_parsers():
    p = ns.parse1("NEW\nSENSE: light punishment, then salvation\nTOPIC: AFTERLIFE")
    assert p == {"answer": "NEW", "sense": "light punishment, then salvation", "topic": "AFTERLIFE"}
    assert ns.parse1("**SAME**\nSENSE: as in Luke\nTOPIC: OTHER")["answer"] == "SAME"
    assert ns.parse1("I cannot tell") is None
    assert ns.parse2("YES\nSIDE: AGAINST") == {"answer": "YES", "side": "AGAINST"}
    assert ns.parse2("No.") == {"answer": "NO", "side": None}
    assert ns.parse2("") is None


def test_kappa():
    assert ns.kappa(["SAME", "NEW", "SAME", "NEW"], ["SAME", "NEW", "SAME", "NEW"]) == 1.0
    assert ns.kappa(["SAME", "SAME", "NEW", "NEW"], ["SAME", "NEW", "SAME", "NEW"]) == 0.0


def test_verdict_rule():
    assert ns.verdict([0.3, 0.25, 0.2, 0.35, 0.3], D)["verdict"] == "period sense"
    assert ns.verdict([0.0, 0.02, -0.03, 0.01], D)["verdict"] == "older sense"
    assert ns.verdict([-0.2, -0.1, -0.3], D)["verdict"] == "older sense"
    assert ns.verdict([0.1, 0.08, 0.12], D)["verdict"] == "cannot tell"
    assert ns.verdict([], D)["verdict"] == "cannot tell"


def test_era_and_enough():
    assert ns.era_of(1700, D) == "early" and ns.era_of(1829, D) == "late"
    assert ns.era_of(1630, D) is None
    assert ns.enough({"early": ["a", "b"], "late": ["c", "d"]}, D)
    assert not ns.enough({"early": ["a", "b"], "late": ["c"]}, D)


def test_check_items_mark_and_count():
    items = json.loads(ns.CHECK_ITEMS.read_text()) if ns.CHECK_ITEMS.exists() else None
    if items is None:  # the private repository is not cloned here
        return
    assert [len(items[k]) for k in ("same", "new", "use")] == [20, 20, 20]
    for it in items["new"] + items["use"]:
        assert "[" in ns.mark(it["passage"], it["phrase"])
