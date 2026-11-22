"""BOM-122 judging step: pure functions."""

from lab.isaiah_judge import check_of, decoy_readings, fisher_greater, parse, verbatim

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
