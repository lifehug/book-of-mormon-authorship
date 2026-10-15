from ingest.hathitrust import FIELDS, parse_row, wanted, year_of


def _row(**kw):
    base = {f: "" for f in FIELDS}
    base.update(kw)
    return base


def test_parse_row_pads_missing_columns() -> None:
    rec = parse_row("hvd.1\tallow\tpd\n")
    assert rec["htid"] == "hvd.1" and rec["rights"] == "pd" and rec["author"] == ""
    assert len(rec) == len(FIELDS)


def test_wanted_filters_language_rights_and_year() -> None:
    assert wanted(_row(lang="eng", rights="pd", rights_date_used="1816"))
    assert wanted(_row(lang="eng", rights="pdus", rights_date_used="1830"))
    assert not wanted(_row(lang="fre", rights="pd", rights_date_used="1816"))
    assert not wanted(_row(lang="eng", rights="ic", rights_date_used="1816"))
    assert not wanted(_row(lang="eng", rights="pd", rights_date_used="1779"))
    assert not wanted(_row(lang="eng", rights="pd", rights_date_used="9999"))


def test_year_of() -> None:
    assert year_of("1816") == 1816 and year_of("") is None
