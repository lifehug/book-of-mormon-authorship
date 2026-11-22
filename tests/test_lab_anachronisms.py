"""BOM-113: the item counter finds planted and real mentions; the cross-table is honest."""

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
