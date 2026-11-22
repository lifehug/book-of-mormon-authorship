"""BOM-122: the aligner finds a planted Isaiah variant, its reading is searched in context, and a
decoy is the same edit at another place."""

import pytest

from lab import isaiah as I
from metadata.config import load


@pytest.fixture(scope="module")
def setup():
    return I.Isaiah(), load()["lab"]["isaiah"]


def test_tokens_fold_spelling():
    assert I.tokens("The Honour of the LORD's labours, four") == [
        "the", "honor", "of", "the", "lord", "s", "labors", "four",
    ]  # fmt: skip


def test_runs_group_consecutive_chapters():
    assert I.runs([1, 2, 3, 52, 53]) == [[1, 2, 3], [52, 53]]


def test_planted_change_is_found_on_its_verse(setup):
    isa, d = setup
    a, b = isa.span([14])
    q = list(isa.words[a:b])
    pos = len(q) - 1 - q[::-1].index("nation")  # the last "nation" of Isaiah 14 is in verse 32
    q[pos] = "nations"
    found, kept, touched = I.variants_of("test", q, [14], isa, d)
    assert len(found) == 1
    v = found[0]
    assert (v["ref"], v["kind"], v["kjv"], v["new"]) == ("14:32", "changed", "nation", "nations")
    assert v["searchable"] and "nations" in v["reading"]
    assert not isa.in_bible(v["reading"])
    assert a + pos in touched and a + pos not in kept


def test_decoy_is_the_same_edit_elsewhere(setup):
    isa, d = setup
    a, b = isa.span([13, 14])
    q = list(isa.words[a:b])
    i = q.index("nation")
    q[i] = "nations"
    built = I.build([("test", q, [[13, 14]])], isa, d)
    assert built["readings"]
    for x in built["decoys"]:
        assert "nations" in x["reading"]
        assert x["ref"] != built["readings"][0]["ref"]


def test_match_needs_the_verse_context():
    p = {"items": [("r0", ["messengers", "of", "the", "nations"], ["zion", "founded", "poor"])],
         "window": 10, "min_context": 2}  # fmt: skip
    I._init(p, {"messengers": 5, "of": 9, "the": 9, "nations": 7})
    near = "the lord hath founded zion answer the messengers of the nations".split()
    bare = ("answer the messengers of the nations " + "and so on " * 20 + "zion").split()
    assert I.match(near) == {0: 7}
    assert I.match(bare) == {}


def test_v2_split_word_is_spelling_not_a_variant(setup):
    isa, d = setup
    a, b = isa.span([14])
    q = list(isa.words[a:b])
    i = q.index("nation")
    q[i : i + 1] = ["na", "tion"]
    found, kept, touched = I.variants_of("test", q, [14], isa, d | {"join_spelling": True})
    assert [v["kind"] for v in found] == ["spelling"]
    assert a + i in kept and a + i not in touched


def test_v2_each_work_against_its_own_decoys():
    d = {"ci": 0.95, "special_p": 0.01}
    works = [
        {"work_id": "copy", "readings": 60, "decoys": 1, "excess": 59.0},
        {"work_id": "paraphrase", "readings": 20, "decoys": 40, "excess": 0.0},
    ]
    res = {w["work_id"]: w for w in I.judged(works, 100, 200, d)}
    assert res["copy"]["clears"] and res["copy"]["rank_excess"] == 1
    assert res["copy"]["ratio_ci"][0] > 1
    assert not res["paraphrase"]["clears"]
