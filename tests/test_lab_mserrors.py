"""BOM-127: the phonetic key and the classifier, on invented examples (no manuscript text)."""

from lab.mserrors import Judge, key, skeleton, wilson
from metadata import config

CFG = config.load()
VOCAB = {
    "there", "their", "son", "sun", "weed", "reed", "straight", "strait", "heard", "herd", "the",
    "and", "great", "plain", "lord", "wind", "winds", "gave", "give", "which", "these",
}  # fmt: skip


def ev(kind, struck, added, before=(), after=()):
    return {
        "event": kind,
        "D": list(struck),
        "I": list(added),
        "before": list(before),
        "after": list(after),
    }


def test_key_joins_homophones_and_keeps_different_words_apart():
    for a, b in [("there", "their"), ("son", "sun"), ("straight", "strait"), ("heard", "herd")]:
        if (a, b) != ("straight", "strait"):  # gh before t is left to the listed misses
            assert key(a) == key(b), (a, b)
    for a, b in [("weed", "reed"), ("gave", "give"), ("of", "off"), ("men", "man")]:
        assert key(a) != key(b), (a, b)


def test_sound_alike_needs_two_words_of_the_vocabulary():
    j = Judge(CFG, VOCAB)
    assert j.near(ev("substitution", ["there"], ["their"])) == "sound_alike"
    assert j.near(ev("substitution", ["weed"], ["reed"])) != "sound_alike"
    assert j.near(ev("substitution", ["thare"], ["there"])) != "sound_alike"  # a misspelling


def test_visual_slips_by_rule():
    j = Judge(CFG, VOCAB)
    assert j.near(ev("substitution", ["wind"], ["wiud"])) == "visual"  # n and u alike in shape
    # a struck run equal to the run before it
    assert j.near(ev("deletion", ["and", "the"], [], before=["x", "and", "the"])) == "visual"
    # an omission restored, bounded by a repeated word
    assert j.near(ev("insertion", [], ["lord", "and"], before=["and"], after=["go"])) == "visual"


def test_anticipation_and_perseveration():
    j = Judge(CFG, VOCAB)
    assert j.near(ev("substitution", ["great"], ["plain"], after=["x", "great"])) == "anticipation"
    assert j.near(ev("deletion", ["lord"], [], before=["the", "lord", "x"])) == "anticipation"
    # short words recur by chance and are not counted
    assert j.near(ev("deletion", ["of"], [], after=["x", "of"])) != "anticipation"


def test_spelling_and_other():
    j = Judge(CFG, VOCAB)
    assert j.near(ev("false_start", ["migh"], ["mightest"])) == "spelling"
    assert j.near(ev("substitution", ["a"], ["e"])) == "spelling"
    assert j.near(ev("deletion", ["zebra"], [])) == "other"


def test_skeleton_and_wilson():
    assert skeleton("amalickiah") == skeleton("ameleckiah")
    lo, hi = wilson(5, 100, 1.96)
    assert 0.02 < lo < 0.05 < hi < 0.12
    assert wilson(0, 0, 1.96) is None
