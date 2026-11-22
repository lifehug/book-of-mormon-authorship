"""BOM-102 second design: the English rules, Hebrew rules, rates and step-1 helpers behave as the
card says."""

from lab import translation2 as T

S = {"doubled_gap": 3, "if_and_max_words": 40}


def hits(feature: str, text: str) -> int:
    return len(T.find(feature, T.tokens(text), S))


def test_doubled_verb_finds_both_orders_and_old_spelling():
    assert hits("doubled_verb", "for in the day thou eatest of it , dying thou shalt dye .") == 1
    assert hits("doubled_verb", "multiplying i will multiply thy seed") == 1
    assert hits("doubled_verb", "hear ye hearing , but understand not") == 1
    assert hits("doubled_verb", "giuing thou shalt giue") == 1
    assert hits("doubled_verb", "spake unto them , saying , say unto the people") == 0
    assert hits("doubled_verb", "the king was dying and the king died") == 0


def test_same_verb_stems():
    assert T.same_verb("cutting", "cut") and T.same_verb("dying", "dieth")
    assert not T.same_verb("thing", "thin") and not T.same_verb("dying", "dying")


def test_if_and_needs_and_before_the_result_clause():
    assert hits("if_and", "if ye shall ask with real intent , and he will manifest it .") == 1
    assert hits("if_and", "if he saith unto the earth , move , and it is moved .") == 1
    assert hits("if_and", "if ye do this , ye shall live , and ye shall prosper .") == 0
    assert hits("if_and", "if ye hearken , and ye will keep it , then ye shall live .") == 0
    assert hits("if_and", "if it rain we shall stay , and they will come .") == 0
    assert hits("if_and", "if ye repent ; and he will hear .") == 0


def test_possessive_infinitive():
    assert hits("possessive_infinitive", "in the day of thine eating of it") == 1
    assert hits("possessive_infinitive", "at his coming the gates opened") == 1
    assert hits("possessive_infinitive", "in his understanding he was wise") == 0


def test_planted_examples_pass_on_a_plain_host():
    host = "the day was fair . the men walked to the town . they bought bread . " * 300
    assert all(T.plant_check(host, S, 3).values())


def test_hebrew_rules_on_made_up_morphology():
    inf_abs = [("4191", "HVqa"), ("4191", "HVqi2ms")]
    assert T.hebrew_instances(inf_abs).get("doubled_verb") == 1
    cond = [("c/518", "HC/Tc"), ("4672", "HVqi1cs"), ("c/5375", "HC/Vqq1cs")]
    assert T.hebrew_instances(cond).get("if_and") == 1
    inf = [("b/398", "HR/Vqc/Sp2ms")]
    assert T.hebrew_instances(inf).get("possessive_infinitive") == 1
    assert T.hebrew_instances([("398", "HVqc")]) == {}


def test_parse_word_reads_prefixes_and_verbs():
    w = T.parse_word("c/1961", "HC/Vqw3ms")
    assert w["main"] == "1961" and w["verb"] == "Vqw3ms" and w["conj"] and "c" in w["prefixes"]
    assert T.parse_word("b/3027", "HR/Ncfsc")["noun_construct"]


def test_poisson_interval_contains_the_rate_and_zero_has_a_ceiling():
    lo, hi = T.poisson_ci(10, 100000)
    assert lo < 1.0 < hi
    assert T.poisson_ci(0, 10000) == (0.0, round(T.poisson_ci(0, 10000)[1], 4))
    assert T.poisson_ci(0, 10000)[1] > 3.6


def test_composite_scales_by_the_old_testament_rate_with_a_floor():
    m = {"words": 10000, "doubled_verb": 2, "possessive_infinitive": 0}
    ot = {"doubled_verb": 1.0, "possessive_infinitive": 0.0}
    assert T.composite(m, ["doubled_verb", "possessive_infinitive"], ot, 0.05) == 1.0
    assert T.composite(m, [], ot, 0.05) is None


def test_auc_and_units():
    assert T.auc([3, 4], [1, 2]) == 1.0 and T.auc([1], [1]) == 0.5
    toks = ("w " * 25).split() + ["."]
    assert [len([t for t in u if t != "."]) for u in T.units(toks, 10)] == [10, 10]


def test_locate_finds_a_verse_and_contains():
    text = "a b c d e f g h i j k l m n o p".split()
    idx = T.grams(text, 4)
    score, a, b = T.locate("e f g h i j".split(), idx, 4)
    assert score == 1.0 and text[a:b] == "e f g h i j".split()
    assert T.contains(text, ["c", "d"]) and not T.contains(text, ["d", "c"])


def test_parse_ref_and_if_then():
    assert T.parse_ref("Helaman 12:13-15") == ("Helaman", 12, [13, 14, 15])
    assert T.parse_ref("1 Nephi 3:7") == ("1 Nephi", 3, [7])
    assert T.if_then_count("if ye do so then it is well if not".split(), 25) == 1


def test_judge_check_and_reply_parsing():
    assert T.parse_reply(" yes.") == "YES" and T.parse_reply("maybe") is None
    key = {f"check:{f}:{i}": ("YES" if i < 1 else "NO") for f in T.TESTED for i in range(2)}
    answers = dict(key)
    res = T.judge_check(answers, key, 0.9)
    assert all(v["passes"] for v in res.values())
    answers[next(iter(key))] = "NO"
    assert not all(v["passes"] for v in T.judge_check(answers, key, 0.9).values())


def test_judge_known_answer_items_are_balanced():
    for f in T.TESTED:
        pos, neg = T.JUDGE_CHECK[f]
        assert len(pos) == len(neg) == 10
        assert all("[[" in x and "]]" in x for x in pos + neg)
