"""Pure functions of lab.utoaztecan (BOM-117): sound classes, the permutation test, his rule."""

import numpy as np

from lab import utoaztecan as u

P, T, S, K, M, N, R, W, J, Z = range(10)


def test_ipa_class_and_first_two():
    assert u.ipa_class("tʃ") == "S"  # affricate with the sibilants
    assert u.ipa_class("bʷ") == "P"
    assert u.ipa_class("ⁿg") == "K"
    assert u.ipa_class("ɑ") == "V"
    assert u.ipa_word("s i l m æ") == (S, R)
    assert u.ipa_word("a n i a") == (Z, N)  # initial vowel is the laryngeal class
    assert u.ipa_word("k a") == (K, u.NONE)
    assert u.ipa_word("") is None


def test_hebrew_symbols_reads_shin_sin_and_vowel_letters():
    assert u.hebrew_symbols("אָב") == ["’", "b"]
    assert u.hebrew_symbols("שָׂדֶה") == ["ś", "d", "h"]
    assert u.hebrew_symbols("שָׁלוֹם") == ["š", "l", "m"]  # holam vav is a vowel letter


def test_coptic_symbols():
    assert u.coptic_symbols("ϩⲧⲟ") == ["h", "t"]
    assert u.coptic_symbols("ⲟⲩⲱϣ") == ["w", "š"]
    assert u.coptic_symbols("ⲥⲟⲛ") == ["s", "n"]


def test_chi2_is_zero_for_independence_and_large_for_identity():
    a = np.array([0, 1, 0, 1])
    assert abs(u.chi2(a, np.array([0, 0, 1, 1]), 2, 2)) < 1e-9
    assert u.chi2(a, a, 2, 2) == 4.0


def test_perm_test_finds_a_regular_correspondence_and_not_noise():
    rng = np.random.default_rng(1)
    a = rng.integers(0, 10, 200)
    shifted = (a + 3) % 10  # regular but never identical
    hit = u.perm_test(a, shifted, 999, np.random.default_rng(2))
    assert hit["p"] < 0.01
    noise = u.perm_test(a, rng.integers(0, 10, 200), 999, np.random.default_rng(3))
    assert noise["p"] > 0.01
    assert 0 < hit["p"] <= 1 and "score" in hit and "z" in hit


def test_multi_perm_test_sums_varieties():
    rng = np.random.default_rng(4)
    donor = rng.integers(0, 10, 120)
    mask = np.ones(120, dtype=bool)
    mask[::5] = False
    varieties = [(mask, donor[mask]), (mask, (donor[mask] + 1) % 10)]
    res = u.multi_perm_test(varieties, donor, 499, np.random.default_rng(5))
    assert res["varieties"] == 2 and res["p"] < 0.01


def test_holm():
    adj = u.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == 0.03 and adj["c"] == 0.06 and adj["b"] == 0.06


def test_plant_is_regular_and_non_identical():
    rng = np.random.default_rng(6)
    a1, a2 = rng.integers(0, 10, 50), rng.integers(0, 11, 50)
    b1, b2 = rng.integers(0, 10, 50), rng.integers(0, 11, 50)
    nb1, nb2 = u.plant(a1, a2, b1, b2, 50, rng)
    pairs = set(zip(a1.tolist(), nb1.tolist(), strict=True))
    assert len({x for x, _ in pairs}) == len(pairs)  # one image per class
    assert all(x != y for x, y in pairs)


def test_gloss_keys_and_closeness_levels():
    assert u.gloss_keys("the stone or rock") == ["stone", "rock"]
    assert u.gloss_keys("to swim") == ["swim"]
    assert u.gloss_keys("EARTH (SOIL)") == ["earth"]
    keyed = {"arm": {"1"}, "hand": {"2"}, "tamale": {"3"}}
    links = {"1": {"2"}, "2": {"1"}}
    assert u.closeness("lightning", "flash of lightning", keyed, links) == 0
    assert u.closeness("arm", "hand", keyed, links) == 1
    assert u.closeness("bury", "tamale", keyed, links) == 2


def test_map_lexicon_prefers_first_gloss_then_frequency():
    keys = {"father": "1", "house": "2"}
    entries = [
        {"id": "H9", "symbols": ["b"], "glosses": ["family", "house"], "rank": -900},
        {"id": "H1", "symbols": ["’", "b"], "glosses": ["father"], "rank": -10},
        {"id": "H2", "symbols": ["b", "y", "t"], "glosses": ["house"], "rank": -5},
    ]
    m = u.map_lexicon(entries, keys)
    assert m["1"]["id"] == "H1" and m["2"]["id"] == "H2"


TABLE = {
    "b": {"initial": {"p", "b"}, "medial": {"p", "b"}},
    "r": {"initial": {"t"}, "medial": {"r"}},
    "q": {"initial": {"k"}, "medial": {"k"}},
    "’": {"initial": {"w", "’"}, "medial": {"w", "’"}},
    "k": {"initial": {"ø"}, "medial": {"k"}},
}


def test_obeys_follows_the_table_by_position():
    assert u.obeys(["b", "r", "q"], ["p", "r", "k"], TABLE)
    assert not u.obeys(["b", "r", "q"], ["p", "t", "k"], TABLE)  # r is t only initially
    assert u.obeys(["k", "b"], ["p"], TABLE)  # initial k may be lost
    assert u.obeys(["b", "r"], ["p", "r", "s"], TABLE)  # a suffix left over is allowed
    assert u.obeys(["b", "q"], ["C", "N"], TABLE) is False  # q is no nasal
    assert not u.obeys(["b", "r", "q"], ["p", "r"], TABLE)
    assert u.obeys(["b", "r", "q"], ["p", "r"], TABLE, final_loss=True)


def test_ua_symbols_and_ne_symbols():
    assert u.ua_symbols("*kwasïC") == ["kw", "s", "C"]
    assert u.ua_symbols("*papi") == ["p", "p"]  # p and p across a vowel stay two
    assert u.ua_symbols("*koppa") == ["k", "p"]  # a geminate is one
    assert u.ua_symbols("*nïmï / *nïmi") == ["n", "m"]
    assert u.ne_symbols("bšl / baašal") == ["b", "š", "l"]
    assert u.ne_symbols("ђeṣ") == ["ђ", "ṣ"]


def test_codes_and_table_rows():
    stratum, pos = u.codes_of("text [liquid] [p1b,p2r,p3q] [SUA: Tep]")
    assert stratum == "p" and pos == {1: "b", 2: "r", 3: "q"}
    table = {"ʕ": {}, "ђ": {}, "s3": {}, "s1": {}, "b": {}, "y": {}}
    assert u.table_row("’2", table) == "ʕ"
    assert u.table_row("h2", table) == "ђ"
    assert u.table_row("s", table) == "s3"
    assert u.table_row("š", table) == "s1"
    assert u.table_row("bb", table) == "b"
    assert u.table_row("i", table) == "y"
    assert u.table_row("ж", table) is None


def test_reflexes_parse_positions():
    r = u._reflexes("t-, medially -r-/-l-")
    assert r["initial"] == {"t"} and r["medial"] == {"r", "l"}
    r = u._reflexes("ø-, -k-, but Tak ŋ")
    assert r["initial"] == {"ø", "ŋ"} and r["medial"] == {"k", "ŋ"}
    assert u._reflexes("-- (not in Egyptian)") is None
    assert u._reflexes("w/o/u")["medial"] == {"w", "ø"}


def test_subsample_is_seeded_and_bounded():
    ms = [str(i) for i in range(100)]
    a = u.subsample(ms, 30, "x", 1)
    assert a == u.subsample(ms, 30, "x", 1) and len(a) == 30
    assert u.subsample(ms, 300, "x", 1) == ms


# --- step 1 with judged readings (card 2026-11-23; synthetic table, lexicon and answers) ---

_TABLE = {
    "kw": {
        "b": {"initial": {"p"}, "medial": {"kw"}},
        "z": {"initial": {"s"}, "medial": {"s"}},
        "d": {"initial": {"s"}, "medial": {"t"}},
    },
    "p": {"b": {"initial": {"p"}, "medial": {"p"}}, "z": {"initial": {"s"}, "medial": {"s"}}},
    "e": {"n": {"initial": {"n"}, "medial": {"n"}}},
}
_H = {"max_positions": 3, "judged": {"rating_level": {"SAME": 0, "RELATED": 1, "DISTANT": 2}}}


def _ans(sid, reply):
    return {"id": sid, "reply": reply}


def test_parse_answer_reads_ratings_and_json_and_refuses_junk():
    assert u.parse_answer(_ans("gloss-1", " Same.")) == "SAME"
    assert u.parse_answer(_ans("gloss-1", "I am out of usage")) is None
    full = '{"ne_language": "Hebrew", "ne_form": "zb", "ne_gloss": "fly", "ua_form": "*sikwo",'
    full += ' "ua_gloss": "fly", "stratum": "Semitic-kw"}'
    assert u.parse_answer(_ans("set-1", "Here: " + full))["stratum"] == "Semitic-kw"
    assert u.parse_answer(_ans("set-1", '{"ne_form": "zb"}')) is None
    assert u.parse_answer(_ans("set-1", "{not json")) is None


def test_judged_record_uses_rule_stratum_and_tags_first():
    reading = {"ne_form": "zab", "ne_gloss": "fly", "ua_form": "*sikwo", "ua_gloss": "fly",
               "stratum": "Semitic-p"}  # fmt: skip
    rec = {"set": 1, "stratum": "kw", "codes": {}}
    j = u.judged_record(rec, reading, _TABLE, 3)
    assert j["stratum"] == "kw" and j["model_stratum"] == "p"
    assert j["readable"] and j["obeys_table"] and j["obeys_first"]  # z>s initial, b>kw medial
    rec = {"set": 2, "stratum": None, "codes": {"1": "z", "2": "b"}}
    j = u.judged_record(rec, reading, _TABLE, 3)
    assert j["stratum"] == "p" and j["skeleton_from"] == "his tags"
    assert j["obeys_first"] and not j["obeys_table"]  # p column wants medial p, not kw


def test_judged_record_unclear_is_unread_but_checked_beside():
    reading = {"ne_form": "zab", "ne_gloss": "fly", "ua_form": "*sikwo", "ua_gloss": "fly",
               "stratum": "unclear"}  # fmt: skip
    j = u.judged_record({"set": 3, "stratum": None, "codes": {}}, reading, _TABLE, 3)
    assert not j["readable"] and j["unclear_checkable_semitic"]
    assert j["unclear_obeys_either_semitic"]  # obeys under kw, not under p


def test_judged_summary_counts_and_gloss_table():
    rule = {"set": 10, "machine_readable": True, "stratum": "kw", "ne_rows": ["z", "b"],
            "ua_symbols": ["s", "kw"], "ua_gloss": "fly", "meaning_level": 2,
            "obeys_table": True, "obeys_first": True, "alternatives": 1}  # fmt: skip
    unread = {"set": 11, "machine_readable": False, "stratum": None, "codes": {}}
    reading = '{"ne_language": "Egyptian", "ne_form": "nan", "ne_gloss": "water",'
    reading += ' "ua_form": "*nam", "ua_gloss": "water", "stratum": "Egyptian"}'
    answers = [_ans("gloss-10", "SAME"), _ans("set-11", reading)]
    lex = {
        "oshl": [{"symbols": ["z", "b"], "glosses": ["fly"]},  # his own root: skipped
                 {"symbols": ["d", "b", "z"], "glosses": ["stone"]},  # sound passes, meaning not
                 {"symbols": ["d", "b"], "glosses": ["a fly"]}],
        "cdo": [{"symbols": ["n"], "glosses": ["water"]}],
    }  # fmt: skip
    pub, priv = u.judged_summary([rule, unread], answers, _TABLE, lex, {}, {}, _H)
    js = pub["judged_sets"]
    assert js["read"] == 1 and js["obey_every_position"] == 1 and js["meaning_levels"] == {0: 1}
    assert pub["all_readable"]["sets"] == 2 and pub["all_readable"]["obey_every_position"] == 2
    g = pub["gloss_ratings"]
    assert g["counts"]["SAME"] == 1 and g["rule_level_by_rating"]["2"]["SAME"] == 1
    assert g["model_closer_than_rule"] == 1 and g["sets_tightened"] == [10]
    # rule level 2 lets "stone" count; at the model's SAME only a gloss sharing "fly" does
    column = _TABLE["kw"]
    assert (
        u.alternatives(["z", "b"], ["s", "kw"], column, 2, "fly", lex["oshl"], {}, {})["both"] == 2
    )
    assert g["alternatives_with_closer_of_rule_and_model"]["median"] == 1
    assert pub["unparsed"] == [] and priv[0]["set"] == 11
