"""BOM-131: pure functions of the Luke 12 commentaries test."""

from collections import Counter

from lab.luke12_commentaries import (
    check_of,
    distinctive,
    find_uses,
    group_uses,
    locate_chapter,
    parse_gen,
    rates,
    tokens,
    verdict,
)

G = {"shingle": 3, "min_share": 0.5, "min_shingles": 3, "span_factor": 1.5,
     "min_anchor_verses": 2, "region_words": 50}  # fmt: skip
D = {"stop_words": ["the", "and", "with", "be", "shall"], "ngram": 4, "min_content": 2,
     "max_pair_word_freq": 5}  # fmt: skip


def test_tokens_fold_spelling_and_long_s():
    assert tokens("The Labour of ſtripes!") == ["the", "labor", "of", "stripes"]


def test_distinctive_keeps_only_grams_of_its_own_chapter():
    verse = tokens("he shall be beaten with few stripes")
    grams = {tuple(verse[i : i + 4]): {("LUK", 12)} for i in range(len(verse) - 3)}
    grams[("he", "shall", "be", "beaten")] = {("LUK", 12), ("DEU", 25)}
    pairs = {("beaten", "few"): {("LUK", 12)}, ("few", "stripes"): {("LUK", 12)},
             ("he", "beaten"): {("LUK", 12), ("ACT", 16)}}  # fmt: skip
    freq = Counter({"beaten": 9, "few": 100, "stripes": 3, "he": 1000})
    got = distinctive(verse, ("LUK", 12), grams, pairs, freq, D)
    assert ("ngram", ("he", "shall", "be", "beaten")) not in got
    assert ("pair", ("few", "stripes")) in got
    assert ("pair", ("he", "beaten")) not in got


def test_pairs_skip_stop_words_between_but_not_far():
    words = tokens("god will beat us with a few stripes and at last")
    assert find_uses(words, [("pair", ("few", "stripes"))], set(D["stop_words"])) == [
        (6, "few stripes")
    ]
    far = tokens("few men and women of every kind came to the stripes")
    assert not find_uses(far, [("pair", ("few", "stripes"))], {"and", "of", "to", "the"})


def test_uses_grouped_by_verse_and_paragraph():
    one = {"ref": "Luke 12:19", "key": ["LUK", 12, 19], "seq": 485}
    u = [one | {"at": 3, "gram": "a"}, one | {"at": 9, "gram": "b"}]
    g = group_uses(u)
    assert len(g) == 1 and g[0]["grams"] == ["a", "b"] and g[0]["at"] == 3


def test_locator_finds_a_garbled_verse_inside_the_chapter_region():
    v1 = tokens("and he spake a parable unto them saying the ground of a certain rich man")
    v2 = tokens("and he thought within himself saying what shall i do because i have no room")
    v3 = tokens("soul thou hast much goods laid up for many years take thine ease eat drink")
    garbled = list(v3)
    garbled[5] = "goodz"
    text = ["x"] * 30 + v1 + ["note"] * 20 + v2 + ["note"] * 20 + garbled + ["x"] * 30
    loc = locate_chapter(text, {16: v1, 17: v2, 19: v3}, G)
    assert set(loc) == {16, 17, 19}
    assert loc[19]["share"] < 1


def test_generation_reply_is_read():
    assert parse_gen("DIFFERENT\nPASSAGE: And they said, eat and be merry.") == (
        "And they said, eat and be merry."
    )
    assert parse_gen("SAME\nboth notes agree") is None
    assert parse_gen("DIFFERENT but no passage") is None


def test_check_needs_both_answers_right_and_every_item():
    ids = ["check|0|henry|yes", "check|0|clarke|no", "check|1|poole|yes", "check|1|scott|no"]
    ans = {ids[0]: "YES", ids[1]: "NO", ids[2]: "YES", ids[3]: "YES"}
    r = check_of(ids, ans, 0.85, 2)
    assert r["attempted"] and r["right"] == 1 and not r["passed"]
    assert not check_of(ids[:2], {ids[0]: "YES"}, 0.5, 1)["attempted"]


def test_rates_count_open_answers_apart():
    ids = ["henry|Luke 12:19|485", "henry|Luke 12:48|485", "decoy|henry|Luke 12:47|9"]
    r = rates({ids[0]: "YES", ids[1]: None, ids[2]: "NO"}, ids)
    assert r["henry"]["asked"] == 2 and r["henry"]["open_or_unparsed"] == 1
    assert r["henry"]["yes"] == 1 and r["henry"]["verses"] == 2


def _r(rate, verses=12):
    return {"rate": rate, "verses": verses, "asked": verses}


DV = {"lead_points": 20, "min_verses": 10, "min_commentaries": 8}


def test_verdict_follows_the_card():
    base = {f"c{i}": _r(0.3 + 0.01 * i) for i in range(7)}
    assert (
        verdict(base | {"henry": _r(0.6), "clarke": _r(0.33)}, ["henry", "clarke"], DV)["verdict"]
        == "henry"
    )
    assert (
        verdict(base | {"henry": _r(0.6, 8), "clarke": _r(0.33)}, ["henry", "clarke"], DV)[
            "verdict"
        ]
        == "cannot tell"
    )
    assert (
        verdict(base | {"henry": _r(0.32), "clarke": _r(0.34)}, ["henry", "clarke"], DV)["verdict"]
        == "neither"
    )
    assert verdict({"henry": _r(0.9)}, ["henry"], DV)["verdict"] == "cannot tell"
