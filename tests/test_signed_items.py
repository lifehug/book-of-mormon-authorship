from ingest.signed_items import propose


def test_single_signed_letter_is_proposed_from_its_dateline():
    lines = [
        "MESSENGER AND ADVOCATE.",
        "",
        "Liberty, Mo. Nov. 6, 1834.",
        "LETTER NO. II.",
        "Dear Brother:",
        "The gathering goes on.",
        "W. W. PHELPS.",
        "To Oliver Cowdery, Esq.",
    ]
    [p] = propose("x", lines)
    assert p["signer"] == "W. W. Phelps" and p["admit"]
    assert (p["start"], p["end"]) == (3, 8)


def test_cosigned_and_officer_signatures_are_rejected():
    lines = ["Resolved, that we meet.", "SIDNEY RIGDON,", "OLIVER COWDERY,", "", "minutes", "x"]
    assert not any(p["admit"] for p in propose("x", lines))
    lines = ["The meeting closed.", "", "W. W. PHELPS, Ch'n."]
    [p] = propose("x", lines)
    assert not p["admit"] and "officer" in p["reason"]


def test_only_checked_admitted_items_are_counted(tmp_path, monkeypatch):
    from ingest import candidate_words

    (tmp_path / "run.txt").write_text("head\nDear Brother:\none two three\nW. W. PHELPS.\n")
    monkeypatch.setattr(candidate_words, "PUBLIC_DIR", tmp_path)
    entry = {"id": "run", "pre1830": False}
    item = {"source": "run", "signer": "W. W. Phelps", "start": 2, "end": 4, "admit": True}
    units = candidate_words.signed_units(entry, [{**item, "checked": True}])
    assert [(u["author"], u["words"]) for u in units] == [("W. W. Phelps", 8)]
    assert candidate_words.signed_units(entry, [{**item, "checked": False}]) == []
    assert candidate_words.signed_units(entry, [{**item, "checked": True, "admit": False}]) == []
