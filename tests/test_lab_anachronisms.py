"""BOM-113: the item counter finds planted and real mentions; the cross-table is honest."""

import json
from pathlib import Path

from lab.anachronisms import compile_forms, count_words, cross_table, keyed_items, plant


def _items():
    return [
        {"id": "horse", "countable": True, "forms": ["horse"], "plural": True, "guard": False},
        {"id": "compass", "countable": True, "forms": ["compass"], "plural": True, "guard": True},
        {"id": "tarshish", "countable": True, "forms": ["ships of tarshish"], "plural": False,
         "guard": False},
        {"id": "doctrine", "countable": False, "forms": [], "plural": False, "guard": False},
    ]  # fmt: skip


def test_counts_plurals_guard_and_phrases():
    f = compile_forms(_items())
    words = "The Horses and a horse ran the compass to compass all ships of Tarshish".split()
    assert count_words(words, f) == {"horse": 2, "compass": 1, "tarshish": 1}


def test_planted_mentions_are_recovered():
    items = _items()
    f = compile_forms(items)
    words = ("and it came to pass that the people went forth " * 50).split()
    base = count_words(words, f)
    planted, n = plant(words, f, items, 4, 7)
    got = count_words(planted, f)
    assert n == {"horse": 4, "compass": 4, "tarshish": 4}
    assert all(got.get(k, 0) - base.get(k, 0) == 4 for k in n)


def test_keyed_items_have_no_invented_roper_status():
    items = keyed_items()
    assert items and all(it["roper_status"] is None for it in items)
    compile_forms(items)  # no form claimed by two items


def test_cross_table_not_attempted_without_statuses_and_runs_with_them():
    empty = cross_table([{"roper_status": None, "bible_item": True}], "bible_item", 0.05)
    assert "not_attempted" in empty
    rows = [{"roper_status": "confirmed", "bible_item": True}] * 9
    rows += [{"roper_status": "unconfirmed", "bible_item": False}] * 9
    res = cross_table(rows, "bible_item", 0.05)
    assert res["table"] == [[9, 0], [0, 9]]
    assert res["verdict"] == "yes" and res["fisher_p"] < 0.001


def test_roper_things_are_defined_and_do_not_collide():
    from lab import anachronisms_roper as r
    from lab.anachronisms import roper_things

    assert set(r.ITEM_THING.values()) <= set(r.THINGS)
    compile_forms(roper_things())


def test_roper_heading_parser_reads_status_era_page_and_years():
    from lab.anachronisms_roper import kind_from_wording, parse_chapter

    text = "\n".join([
        "Pages 9-50", "12 • Interpreter 65 (2025)", "4. Pre-Columbian Horses (in Book of",
        "Mormon Times)", "Status: Confirmed Bison Loan Shift (1966–2024)",
        "Critics' Claim: one writer in 1910 and another in 1857 said so.", "Response: no.",
        "5. Silver Money", "Status: Unconfirmed",
    ])  # fmt: skip
    rows = parse_chapter(1, text)
    assert [r["printed_number"] for r in rows] == [4, 5]
    assert rows[0]["label"] == "Pre-Columbian Horses (in Book of Mormon Times)"
    assert rows[0]["page"] == 12 and rows[0]["era_confirmed"] == "1966-2024"
    assert rows[0]["loan_shift"] == "Bison" and rows[0]["years_named_in_claim"] == [1910, 1857]
    assert rows[1]["status"] == "unconfirmed" and rows[1]["era_confirmed"] is None
    assert kind_from_wording("Steel Swords (OW)", "Confirmed (1966–2024)") == "old_world"
    assert kind_from_wording("Cows", "Confirmed Bison Loan Shift (1845–1965)") == (
        "linguistic_reading"
    )
    assert kind_from_wording(rows[0]["label"], "Partially Confirmed") == "new_world_in_period"
    assert kind_from_wording("Lawyers", "Confirmed") == "not_stated"


def test_kind_tables_test_each_kind_against_the_rest():
    from lab.anachronisms import kind_tables

    rows = [{"roper_status": "confirmed", "roper_confirmation_kind": "old_world"}] * 6
    rows += [{"roper_status": "unconfirmed", "roper_confirmation_kind": "not_stated"}] * 6
    res = kind_tables(rows, 0.05)
    assert res["old_world"]["table"] == [[6, 0], [0, 6]]
    assert res["old_world"]["verdict"] == "yes"


# ------------------------------------------------------------------------------ judged answers


def _w(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def _ans(code, loose):
    return json.dumps({"code": code, "loose_confirmed": loose, "basis": "x"})


def test_parse_judged_reads_json_and_refuses_the_rest():
    from lab.anachronisms import parse_judged

    assert parse_judged(_ans("old_world_only", "yes")) == {"code": "old_world_only", "loose": True}
    fenced = "```json\n" + _ans("not_attested", "No") + "\n```"
    assert parse_judged(fenced) == {"code": "not_attested", "loose": False}
    assert parse_judged("You've hit your usage limit") is None
    assert parse_judged(_ans("somewhere", "yes")) is None
    assert parse_judged(_ans("not_attested", "maybe")) is None
    assert parse_judged('{"code": ') is None


def _setup(tmp_path, monkeypatch, n_control_answered=2):
    from lab import anachronisms as an

    monkeypatch.setattr(an, "PRIVATE", tmp_path)
    monkeypatch.setattr(an, "out", lambda p: tmp_path / Path(p).name)
    _w(tmp_path / "jobs_known.jsonl", [{"id": f"known|{k}"} for k in an.KNOWN_JUDGE])
    known = [{"id": f"known|{k}", "reply": _ans(v, "yes")} for k, v in an.KNOWN_JUDGE.items()]
    _w(tmp_path / "answers_known.jsonl", known)
    items = [  # four confirmed (two kept strictly, all four loosely), one unconfirmed
        {"id": f"r{i}", "roper_status": "confirmed" if i < 4 else "unconfirmed",
         "era_first_raised": "1830-1844", "category": "animal", "thing": "horse" if i else None}
        for i in range(5)
    ]  # fmt: skip
    codes = ["mesoamerica_in_period"] * 2 + ["old_world_only"] * 2 + ["not_attested"]
    loose = ["yes"] * 4 + ["no"]
    _w(tmp_path / "jobs_bom.jsonl", [{"id": f"bom|{it['id']}"} for it in items])
    _w(tmp_path / "answers_bom.jsonl",
       [{"id": f"bom|{it['id']}", "reply": _ans(c, lo)}
        for it, c, lo in zip(items, codes, loose, strict=True)])  # fmt: skip
    ctl = ["control|ss-manuscript-story-1885|horse", "control|ss-manuscript-story-1885|sword"]
    _w(tmp_path / "jobs_control.jsonl", [{"id": i} for i in ctl])
    _w(
        tmp_path / "answers_control.jsonl",
        [{"id": i, "reply": _ans("old_world_only", "yes")} for i in ctl[:n_control_answered]],
    )
    result = {"book_of_mormon": {"all_text": {"present": ["r1", "r2", "r3", "r4"]},
                                 "without_quoted_chapters": {"present": ["r1", "r2", "r3"]}},
              "controls": {"all_items": {"books": {
                  "ss-manuscript-story-1885": {"group": "antiquity_story"}}}}}  # fmt: skip
    return an, items, result


def test_judged_refuses_while_answers_are_open_or_unreadable(tmp_path, monkeypatch):
    from metadata import config

    an, items, result = _setup(tmp_path, monkeypatch, n_control_answered=1)
    got = an.score_judged(config.load(), items, result)
    assert "refused" in got and got["answers"]["control"]["open"] == 1
    with (tmp_path / "answers_control.jsonl").open("a") as fh:
        fh.write(json.dumps({"id": "control|ss-manuscript-story-1885|sword",
                             "reply": "API Error: overloaded"}) + "\n")  # fmt: skip
    got = an.score_judged(config.load(), items, result)
    assert got["answers"]["control"]["unreadable"] == ["control|ss-manuscript-story-1885|sword"]
    assert (tmp_path / "anachronisms_unparsed_control.jsonl").exists()


def test_judged_scores_hand_made_answers(tmp_path, monkeypatch):
    from metadata import config

    an, items, result = _setup(tmp_path, monkeypatch)
    got = an.score_judged(config.load(), items, result)
    b = got["book_of_mormon"]["all_items"]
    assert got["known"]["passed"] and got["known"]["matched"] == 12
    assert b["roper_confirmed"]["strict_confirmed"] == 2 and b["roper_confirmed"]["n"] == 4
    assert b["roper_confirmed"]["loose_share"] == 1.0
    assert b["verdict"] == "holds only under the loose rule"  # 0.5 strict, 1.0 loose; bar 0.75
    w = got["book_of_mormon"]["without_items_only_in_quoted_chapters"]
    assert w["all"]["n"] == 4  # r4 occurs only in the quotation chapters
    c = got["controls"]["ss-manuscript-story-1885"]
    assert c["n"] == 2 and c["loose_share"] == 1.0 and c["strict_confirmed"] == 0
    assert c["loose_vs_book"]["book"] == [3, 4]  # the book's countable items r1..r4
    assert got["named_control_verdict"].startswith("the control shows the same")
    assert "basis" not in json.dumps(got)  # the judge's words are not kept
