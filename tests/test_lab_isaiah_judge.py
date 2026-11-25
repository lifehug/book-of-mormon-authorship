"""BOM-122 judging step: pure functions."""

from lab.isaiah_judge import (
    check_of,
    decoy_readings,
    fisher_greater,
    parse,
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
