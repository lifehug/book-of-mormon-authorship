"""BOM-122 judging step: pure functions."""

from lab.isaiah_judge import (
    check_of,
    decoy_readings,
    fisher_greater,
    gap_jobs,
    locate,
    parse,
    score_gap,
    shingle_index,
    townsend_examples,
    verbatim,
)

Q = "X. The 1830 Book of Mormon reads 'shall be in the' (y).\n\n"
D = {"bar_decoy_no": 0.9, "bar_verbatim_yes": 0.8}


def test_reply_is_read_from_its_first_word():
    assert parse("YES\nit prints it") == "YES"
    assert parse("**no** - nothing") == "NO"
    assert parse("Unclear.") == "UNCLEAR"
    assert parse("Maybe") is None


def test_verbatim_needs_the_whole_reading():
    assert verbatim(Q + "their works shall be in the dark")
    assert not verbatim(Q + "their works are in the dark")


def test_check_needs_every_answer_and_both_bars():
    prompts = {"decoy|w|1": Q + "nothing here", "w|2": Q + "it shall be in the dark"}
    assert not check_of({"decoy|w|1": "NO"}, prompts, D)["attempted"]
    assert check_of({"decoy|w|1": "NO", "w|2": "YES"}, prompts, D)["passed"]
    assert not check_of({"decoy|w|1": "YES", "w|2": "YES"}, prompts, D)["passed"]


def test_fisher_is_one_sided():
    assert fisher_greater(5, 0, 0, 5) < 0.01
    assert fisher_greater(0, 5, 5, 0) == 1.0


def test_a_decoy_is_undone_to_its_king_james_form():
    src = [{"rid": 0, "kjv": "but", "new": "yet they swear", "kind": "changed"}]
    dec = [
        {"rid": 0, "ref": "51:8", "reading": "like wool yet they swear my".split(), "context": 3}
    ]
    (r,) = decoy_readings(dec, src)
    assert r["kjv_form"] == "like wool but my".split()
    assert r["rid"] == 0 and r["ref"] == "51:8"


def test_townsend_examples_are_classed_from_existing_answers():
    detail = [
        {"rid": 0, "ref": "9:3", "kjv": "not", "new": "", "in_clarke": False, "works": 0},
        {"rid": 1, "ref": "14:32", "kjv": "nation", "new": "nations", "in_clarke": False,
         "works": 16},
        {"rid": 2, "ref": "14:32", "kjv": "one", "new": "", "in_clarke": False, "works": 0},
        {"rid": 3, "ref": "5:6", "kjv": "briers", "new": "briars", "in_clarke": True, "works": 45},
    ]  # fmt: skip
    variants = [{"ref": r["ref"], "kjv": r["kjv"], "new": r["new"], "long": False} for r in detail]
    variants.append({"ref": "11:4", "kjv": "", "new": "x " * 40, "long": True})
    items = [
        {"n": 1, "isaiah": "9:3", "book_of_mormon": "a", "townsend_pages": "1",
         "changes": [["9:3", "not", ""]]},
        {"n": 2, "isaiah": "14:32", "book_of_mormon": "b", "townsend_pages": "2", "primary": 0,
         "changes": [["14:32", "nation", "nations"], ["14:32", "one", ""]]},
        {"n": 3, "isaiah": "11:4", "book_of_mormon": "c", "townsend_pages": "3",
         "changes": [["11:4", "", "LONG"]]},
        {"n": 4, "isaiah": "5:6", "book_of_mormon": "d", "townsend_pages": "4",
         "changes": [["5:6", "briers", "briars"]]},
        {"n": 5, "isaiah": "2:16", "book_of_mormon": "e", "townsend_pages": "5",
         "tied_to_clarke": False, "changes": [["2:15", "", "LONG"]]},
        {"n": 6, "isaiah": "1:1", "book_of_mormon": "f", "townsend_pages": "6",
         "changes": [["1:1", "a", "b"]]},
    ]  # fmt: skip
    asked = {"C|0", "W|0", "C|2", "W|1", "W|2", "C|3"}
    ans = {"C|0": "YES", "W|0": "NO", "C|2": "NO", "W|1": "YES", "W|2": "NO", "C|3": "NO"}
    res = townsend_examples(items, detail, variants, ans, asked, "C", {0: True, 1: False})
    by = {r["n"]: r for r in res["rows"]}
    assert by[1]["class"] == "clarke_by_note"
    # the minor neighbour was asked and said no; the change Townsend names was never asked
    assert by[2]["class"] == "not_supported"
    assert by[2]["primary_class"] == "not_asked_of_clarke"
    assert by[2]["changes"][0]["others_yes"] == 1
    assert by[2]["changes"][0]["kjv_form_in_clarke_ocr"] is False
    assert by[3]["class"] == "outside_variant_set"
    assert by[3]["changes"][0]["in_variant_list"] is True
    assert by[4]["class"] == "clarke_by_wording"
    assert by[5]["class"] == "townsend_credits_other_works"
    assert by[6]["changes"][0]["in_variant_list"] is False
    assert res["clarke_yes"] == 1 and res["others_yes"] == 1
    assert res["named_changes_in_strict_set"] == 4 and res["clarke_asked"] == 3


G = {"shingle": 3, "min_share": 0.5, "min_shingles": 3, "span_factor": 1.5, "check_decoys": 1}
VERSE = "and it shall come to pass in the day that the lord shall give thee rest".split()


def test_a_verse_is_located_through_a_damaged_word_and_margin_text():
    bad = "and it shall come to pass in the day that the lorp shall give thee rest".split()
    text = "x y z".split() * 50 + bad[:8] + ["ann", "mundi"] + bad[8:] + "q r".split() * 50
    loc = locate(VERSE, shingle_index(text, 3), G)
    assert loc is not None and loc["share"] >= 0.5
    assert 150 <= loc["start"] <= 160


def test_a_verse_below_the_match_quality_is_not_located():
    text = "and it shall come to pass xx yy zz ww".split()
    assert locate(VERSE, shingle_index(text, 3), G) is None
    assert locate(["too", "short"], shingle_index(text, 3), G) is None


def test_gap_jobs_ask_the_same_question_at_located_verses_only():
    verses = {(1, 1): "in the beginning was isaiah son of amoz".split(), (14, 3): VERSE,
              (66, 24): "and they shall go forth and look upon the carcases".split(),
              (14, 4): "that thou shalt take up this proverb against the king".split()}  # fmt: skip
    text = verses[(1, 1)] + ["n"] * 30 + VERSE + ["n"] * 30 + verses[(66, 24)]
    r = {"rid": 7, "ref": "14:3", "kjv_form": "in the day that the".split(),
         "reading": "in that day that the".split(), "kjv": "the", "new": "that",
         "kind": "changed"}  # fmt: skip
    lost = dict(r, rid=8, ref="14:4")
    dec = dict(r, rid=0, reading="in the day which the".split())
    d = {"clarke_gap": G, "clarke_isaiah": "C", "judge_window": 5}
    res = gap_jobs([r, lost], [dec], verses, text, d, 1)
    assert [j["id"] for j in res["jobs"]] == ["decoy|C|0", "C|7"]
    assert res["not_located"] == [8] and res["located"][0]["rid"] == 7
    assert "Isaiah 14:3 in the King James Bible" in res["jobs"][1]["prompt"]


def test_gap_score_keeps_the_main_result_and_needs_its_own_check():
    main = {"clarke": {"asked": 10, "yes": 0, "rate": 0.0, "rank_among_works": 3,
                       "p_above_others": 1.0, "others_asked": 100, "others_yes": 2,
                       "others_rate": 0.02},
            "verdict": "Clarke does not stand out among the commentaries",
            "works": {"C": {"real_asked": 10, "real_yes": 0},
                      "W": {"real_asked": 100, "real_yes": 2}}}  # fmt: skip
    located = {"gap": 3, "located": [{"rid": 1}, {"rid": 2}], "not_located": [3]}
    jobs = [{"id": "decoy|C|0"}, {"id": "C|1"}, {"id": "C|2"}]
    detail = [{"rid": i, "ref": "1:1", "kind": "changed", "kjv": "a", "new": "b"} for i in range(4)]
    d = {"bar_decoy_no": 0.9, "model": "m", "clarke_isaiah": "C", "alpha": 0.05}
    half = score_gap(main, located, jobs, {"decoy|C|0": "NO"}, detail, [1], d)
    assert "stopped" in half and half["located"]["not_located"] == 1
    ans = {"decoy|C|0": "NO", "C|1": "YES", "C|2": "NO"}
    res = score_gap(main, located, jobs, ans, detail, [1], d)
    assert res["main_result_unchanged"]["asked"] == 10
    assert res["clarke_all_located"]["asked"] == 12 and res["clarke_all_located"]["yes"] == 1
    assert res["clarke_all_located"]["rank_among_works"] == 1
    assert res["townsend"][0]["clarke_answer"] == "YES"
    assert not score_gap(main, located, jobs, ans | {"decoy|C|0": "YES"}, detail, [1], d)["check"][
        "passed"
    ]
