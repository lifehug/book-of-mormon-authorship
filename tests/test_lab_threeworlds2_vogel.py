"""BOM-109 second design, card amendment 1: Vogel's motifs (our coding of his prose) and the
Manchester library sensitivity. Hand-made cases only; no corpus text is needed."""

import copy

import pytest

from lab import threeworlds2 as tw
from lab import threeworlds2_manchester as mc
from lab import threeworlds2_vogel as vg
from metadata import config


@pytest.fixture(scope="module")
def cfg():
    return copy.deepcopy(config.load())


def test_amendment_values_are_in_the_config(cfg):
    s = tw.settings(cfg)
    assert s["vogel_year_max"] == 1829 and s["vogel_book_sample"] == s["sample_per_feature"]
    assert s["vogel_source_max"] == 20 and s["vogel_min_yes"] == 1
    assert s["manchester_accession_max"] == 275 and s["manchester_year_max"] == 1830


def test_motifs_are_labelled_and_cite_known_sources():
    assert "not his list" in vg.LABEL
    for mid, (claim, markers, ch, notes, _refs, sources) in vg.MOTIFS.items():
        assert claim and markers.split(), mid
        assert ch in (1, 2, 3, 4) and notes, mid
        assert sources and all(s in vg.SOURCES for s in sources), mid
    assert not set(vg.EXCLUDED) & set(vg.MOTIFS)
    for sid, (_sur, title, year, kind, _text) in vg.SOURCES.items():
        assert title and kind in ("book", "periodical", "newspaper", "manuscript"), sid
        assert kind == "manuscript" or year < 1830, sid


def test_markers_find_phrases_and_words():
    text = tw.clean("They went where there never had man been, and the Great Spirit spoke.")
    _spans, hits = vg.find(text)
    got = {m for m, _a, _b in hits}
    assert "land_never_inhabited" in got and "christian_beliefs" in got


def _reg_cat(rows):
    reg = [{"work_id": w, "kind": "work", "year": y} for w, _a, _t, y in rows]
    cat = {w: {"author_norm": a, "author": a, "title": t, "text_path": "x"}
           for w, a, t, _y in rows}  # fmt: skip
    return reg, cat


def test_match_works_states_years_and_one_person():
    reg, cat = _reg_cat([
        ("w1", "kames, henry home lord", "Sketches of the history of man", 1774),
        ("w2", "home, henry lord kames", "Sketches of the history of man vol 2", 1788),
        ("w3", "kames, henry home lord", "Sketches of the history of man", 1840),
        ("w4", "smith, a", "The life of Napoleon", 1815),
        ("w5", "jones, b", "Life of Napoleon Bonaparte", 1816),
    ])  # fmt: skip
    m = vg.match_works("home|kames", r"sketches of the history of man", 1829, reg, cat)
    assert m["state"] == "matched" and m["earliest"] == 1774
    assert sorted(w for c in m["clusters"].values() for w in c) == ["w1", "w2"]  # 1840 too late
    assert vg.match_works(None, r"life of napoleon", 1830, reg, cat)["state"] == "ambiguous"
    assert vg.match_works("adair", r"indians", 1829, reg, cat)["state"] == "unmatched"


def test_verdict_found_open_and_miss(cfg):
    s = tw.settings(cfg)
    ids = ["a", "b", "c"]
    assert vg.verdict(ids, {"a": "N", "b": "Y"}, s)[0] == "found"
    assert vg.verdict(ids, {"a": "N", "b": "N"}, s)[0] == "open"
    assert vg.verdict(ids, {"a": "N", "b": "N", "c": "N"}, s)[0] == vg.MISS
    assert vg.verdict(ids, {"a": "N", "b": "N", "c": "maybe"}, s)[0] == "open"  # never a "no"
    assert vg.verdict([], {}, s)[0] == "no passage to judge"


def test_report_keeps_the_manuscript_apart(cfg, monkeypatch, tmp_path):
    monkeypatch.setattr(tw, "PARSE_LOG", tmp_path / "parse.jsonl")
    mid = "old_world_beasts"
    meta = {"book": {m: {"hits": 0, "asked": []} for m in vg.MOTIFS},
            "sources": {m: {"hits": {}, "asked": []} for m in vg.MOTIFS}}  # fmt: skip
    meta["book"][mid] = {"hits": 3, "asked": [{"id": "b0", "ref": "Ether IV para 1"}]}
    meta["sources"][mid]["asked"] = [
        {"id": "s0", "source": "rees_cyclopaedia", "unit": "w", "year": 1805},
        {"id": "s1", "source": "spalding_ms", "unit": "spalding", "year": 1812},
    ]
    res = vg.report(meta, {"b0": "Y", "s0": "N", "s1": "Y"}, cfg)["motifs"][mid]
    assert res["in_1830_text"]["state"] == "found"
    assert res["in_print_before_1830"]["state"] == vg.MISS  # Spalding was not in print
    assert res["in_spalding_manuscript"] == "found"
    assert vg.report(meta, {}, cfg)["motifs"]["honey_bee"]["in_print_before_1830"]["state"] == (
        "no named printed source held"
    )


def test_manchester_entries_cover_paul_to_1830():
    seen = []
    for acc, sur, title, _year in mc.ENTRIES:
        a, _, b = acc.partition("-")
        seen += list(range(int(a), int(b or a) + 1))
        assert title is not None or sur is None
    assert len(seen) == len(set(seen))
    assert sorted(seen) == [n for n in range(1, 276) if n != 265]
    assert mc.NAMED == {"seaver_jemison_1826": "192"}


def test_manchester_picks_the_longest_copy():
    match = {"matches": {"1": {"state": "matched", "clusters": {"k": ["a", "b"]}},
                         "2": {"state": "ambiguous", "clusters": {"k": ["c"]}}}}  # fmt: skip
    reg = [{"work_id": "a", "words": 10}, {"work_id": "b", "words": 99},
           {"work_id": "c", "words": 5}]  # fmt: skip
    assert mc.picks(match, reg) == {"1": "b"}


def test_sensitivity_waits_for_the_main_checks(cfg, monkeypatch, tmp_path):
    monkeypatch.setattr(tw, "collect", lambda c: ([], {}))
    monkeypatch.setattr(tw, "all_answers", lambda: {})
    monkeypatch.setattr(tw, "load_answers", lambda paths: {})
    monkeypatch.setattr(tw, "evaluate", lambda *a, **k: {"passed": False})
    monkeypatch.setattr(mc, "CARD", tmp_path)
    (tmp_path / "jobs_meta.json").write_text("{}")
    res = mc.cmd_sensitivity(cfg)
    assert res["state"].startswith("not scored")


def test_amendment_jobs_stay_out_of_the_main_run():
    for k in ("vogel", "manchester", "manchester_subject"):
        assert k not in tw.JOB_FILES
