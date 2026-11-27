"""BOM-128: joined King James phrases (lab.joined), on a small Bible and made-up texts."""

from __future__ import annotations

from lab import joined

ROWS = [
    {"book": "ISA", "section": "OT", "ref": "Isaiah 22:13",
     "text": "And behold joy and gladness, slaying oxen, and killing sheep, eating flesh, and "
             "drinking wine: let us eat and drink; for to morrow we shall die."},
    {"book": "LUK", "section": "NT", "ref": "Luke 12:19",
     "text": "And I will say to my soul, Soul, thou hast much goods laid up for many years; take "
             "thine ease, eat, drink, and be merry."},
    {"book": "LUK", "section": "NT", "ref": "Luke 12:20",
     "text": "But God said unto him, Thou fool, this night thy soul shall be required of thee."},
    {"book": "1CO", "section": "NT", "ref": "1 Corinthians 15:32",
     "text": "If after the manner of men I have fought with beasts at Ephesus, what advantageth "
             "it me, if the dead rise not? let us eat and drink; for to morrow we die."},
    {"book": "TOB", "section": "Apocrypha", "ref": "Tobit 1:1", "text": "eat drink and be merry"},
]  # fmt: skip
D = {"window": 25, "ngram_sizes": [4, 5], "min_phrase_words": 4, "independent_works": 2,
     "late_from": 1750, "min_current_joins": 2, "title_key_words": 4,
     "late_percentile": 90, "old_percentile": 75}  # fmt: skip


def bible():
    return joined.Bible(ROWS, [4, 5])


def test_apocrypha_left_out_and_books_kept_apart():
    b = bible()
    assert "Tobit 1:1" not in b.refs
    assert b.verses(("eat", "drink", "and", "be", "merry")) == {b.refs.index("Luke 12:19")}


def test_seed_join_found():
    b = bible()
    words = joined.tokens("they say Eat, drink, and be merry, for to-morrow we die; and it is well")
    js = joined.joins_in(words, b, b.grams, D)
    keys = {joined.join_key(j["a"], j["b"]) for j in js}
    assert "eat drink and be merry | for to morrow we die" in keys


def test_bible_neighbours_are_not_a_join():
    b = bible()  # Luke 12:19 and 12:20 sit side by side in the Bible
    words = joined.tokens("take thine ease eat drink and be merry and then thou fool this night "
                          "thy soul shall be required of thee")  # fmt: skip
    assert joined.joins_in(words, b, b.grams, D) == []


def test_same_verse_and_too_far_are_not_joins():
    b = bible()
    far = " filler" * 30
    words = joined.tokens("eat drink and be merry" + far + " for to morrow we die")
    assert joined.joins_in(words, b, b.grams, D) == []
    # two pieces of one verse are not a join
    words = joined.tokens("let us eat and drink and so for to morrow we die")
    assert joined.joins_in(words, b, b.grams, D) == []


def test_rare_filter_drops_common_grams():
    b = bible()
    rare = {g: v for g, v in b.grams.items() if g != ("eat", "drink", "and", "be")}
    rare = {g: v for g, v in rare.items() if g[:4] != ("eat", "drink", "and", "be")}
    ph = joined.phrases_in(joined.tokens("eat drink and be merry"), rare, [4, 5], 4)
    assert ph == [(1, 5, ("drink", "and", "be", "merry"))]


def test_holds_and_dating():
    a, b2 = ("eat", "drink", "and", "be", "merry"), ("for", "to", "morrow", "we", "die")
    phrases, pairs = joined.phrase_table([(a, b2)])
    text = joined.tokens("eat drink and be merry quoth he for to morrow we die")
    assert joined.holds(text, phrases, pairs, 25) == [0]
    assert joined.holds(joined.tokens("eat drink and be merry"), phrases, pairs, 25) == []
    assert joined.first_current([1820, 1655, 1790], 2) == 1790
    assert joined.first_current([1820], 2) is None
    meta = {"w1": {"year": 1652, "author": "Baxter, Richard", "title": "Saints rest"},
            "w2": {"year": 1658, "author": "Baxter, Richard", "title": "Call"},
            "w3": {"year": 1821, "author": None, "title": "A sermon"},
            "own": {"year": 1650, "author": "X", "title": "Y"}}  # fmt: skip
    dj = joined.date_join("k", ["w1", "w2", "w3", "own"], {"own"}, meta, D)
    assert dj["first_current"] == 1650 and dj["first_current_distinct_authors"] == 1820
    s = joined.book_shares([dj, {**dj, "first_current": 1820}], 1650, D, "first_current")
    assert s["share_late"] == 0.5 and s["share_by_own_decade"] == 0.5 and s["usable"]


def test_verdict_rule():
    early = [0.0, 0.1, 0.2, 0.3, 0.4]
    late = [0.5, 0.6, 0.7]
    assert joined.verdict(0.9, early, late, D) == "late"
    assert joined.verdict(0.1, early, late, D) == "old"
    assert joined.verdict(0.35, early, late, D) == "cannot tell"
    assert joined.verdict(None, early, late, D) == "cannot tell"


def test_own_copies():
    rows = [
        {"work_id": "a", "group": 1, "author": "Baxter, Richard, 1615-1691",
         "title": "The saints everlasting rest"},
        {"work_id": "b", "group": 2, "author": "Baxter, Richard",
         "title": "The saints everlasting rest, abridged"},
        {"work_id": "c", "group": 1, "author": "Other", "title": "Other"},
        {"work_id": "d", "group": 3, "author": "Baxter, Richard", "title": "A call"},
    ]  # fmt: skip
    book = {"work_id": "a", "group": 1, "author": rows[0]["author"], "title": rows[0]["title"]}
    assert joined.own_copies(book, rows, D) == {"a", "b", "c"}
    spec = {"exclude_author": "baxter, richard", "exclude_title": "everlasting rest"}
    assert joined.own_copies(spec, rows, D) == {"a", "b"}


def test_design2_distinctive_filter():
    b = bible()
    df = {("eat", "drink", "and", "be"): 5}
    kept = joined.distinctive(b, df, 100, 0.02, {"function_rule": False})
    assert ("eat", "drink", "and", "be") not in kept and ("drink", "and", "be", "merry") in kept
    kept = joined.distinctive(b, {}, 100, 0.02, {"function_rule": True})
    assert ("for", "to", "morrow", "we") not in kept  # function words and one other word
    assert ("to", "morrow", "we", "die") in kept


def test_settings_design2_overrides():
    cfg = {
        "lab": {"joined_phrases": {"window": 25, "seed": 1, "design2": {"seed": 2, "design": 2}}}
    }
    assert joined.settings(cfg) == {"window": 25, "seed": 2, "design": 2}


def test_design3_samples_and_majority():
    rows = [{"work_id": f"w{y}_{i}", "year": y} for y in (1650, 1655, 1780) for i in range(3)]
    d3 = {"draws": 4, "per_decade": None, "min_per_decade": 1, "sample_seed": 1}
    ds = joined.decade_samples(rows, d3)
    assert ds["per_decade"] == 3 and all(len(s) == 6 for s in ds["draws"])
    meta = {r["work_id"]: {"year": r["year"], "author": r["work_id"], "title": "t"} for r in rows}
    dd = {**D, "year_min": 1640, "year_max": 1829, "majority": 0.5}
    draws = [{"a", "b", "c"}, {"a", "b", "c"}, {"a", "c"}, {"a", "c"}]
    meta2 = {"a": {"year": 1650}, "b": {"year": 1652}, "c": {"year": 1785}}
    # by 1650 in 2 of 4 draws only (not a majority); by 1780 in all 4
    assert joined.sampled_first(["a", "b", "c"], set(), meta2, draws, dd) == (1780, 1.0)
    assert joined.sampled_first(["a", "b", "c"], {"c"}, meta2, draws, dd) == (None, 0.5)
    assert meta  # rows reach the sampler


def test_design4_onset_by_rate():
    dd = {**D, "onset_share": 0.25}
    tot = {x: 1000 for x in joined.DECADES} | {1820: 10000}
    # 1650s: 2 per 1,000; 1820s: 10 per 10,000 = 1 per 1,000 -> peak 1650s, onset 1650s
    assert joined.onset({1650: 2, 1820: 10}, tot, dd)[:2] == (1650, 1650)
    # a weak early holder under a quarter of the peak does not set the onset
    assert joined.onset({1650: 1, 1700: 10}, tot, dd)[:2] == (1700, 1700)
    assert joined.onset({1650: 1}, tot, dd)[0] is None  # one holder: not dated
