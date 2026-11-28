"""BOM-134: passages are equal and seeded, replies are read strictly, the check gates the score."""

import json

import pytest

from lab import anachronisms as a113
from lab import ancient_anachronisms as aa


def _cfg():
    return {"lab": {"ancient_anachronisms": {
        "seed": 1, "passage_words": 5, "passages_per_text": 3, "code_model": "sonnet",
        "list_model": "sonnet", "second_coder_model": "opus", "agreement_items": 2,
        "kappa_bar": 0.6, "bar_planted": 0.9, "bar_textbook": 1, "reader_bar": 0.9,
        "bootstrap": 50, "max_items_public": 4,
        "planted": {"per_kind": 1, "kinds": {"clock": {"sentence": "A clock struck.",
                                                       "match": ["clock"]}}},
        "textbook": {"camels": {"passages": ["kjv:GEN 12:16"], "match": ["camel"],
                                "text": "t1"}},
        "pseudo_ancient": ["d1"],
        "texts": {"t1": {"group": "genuine", "kind": "kjv", "setting": "S1"},
                  "d1": {"group": "decoy", "kind": "kjv", "setting": "S2"}},
    }}}  # fmt: skip


def test_cut_keeps_segments_between_markers():
    text = "front\nBOOK A\npoem one\nNOTES x\nBOOK B\npoem two\nNOTES y\n"
    got = aa.cut(text, ["(?m)^BOOK", "(?m)^NOTES"])
    assert "poem one" in got and "poem two" in got
    assert "front" not in got and "x" not in got.split() and "y" not in got.split()
    assert aa.cut("a BOOK b", ["BOOK", None]) == "BOOK b"


def test_clean_reads_long_s_and_joins_line_end_hyphens():
    assert aa.clean("ſword and pro-\n  phet") == "sword and prophet"


def test_sample_is_seeded_equal_and_in_order():
    cfg = _cfg()
    text = " ".join(f"w{i}" for i in range(52))  # 10 windows of 5, tail of 2 dropped
    a, b = aa.sample("t1", text, cfg), aa.sample("t1", text, cfg)
    assert a == b and len(a) == 3
    assert all(len(p.split()) == 5 for _, p in a)
    assert [i for i, _ in a] == sorted(i for i, _ in a)


def test_plant_goes_in_at_a_sentence_end():
    got = aa.plant("one two. three four five. six seven", "A clock struck.")
    assert got == "one two. three four five. A clock struck. six seven"


def test_kjv_passage_is_centred_on_the_verse():
    rows = [{"book": "GEN", "chapter": 12, "verse": v, "text": f"v{v}a v{v}b"}
            for v in range(1, 21)]  # fmt: skip
    p = aa.kjv_passage("GEN 12:10", 6, rows)
    assert p.split() == ["v8b", "v9a", "v9b", "v10a", "v10b", "v11a"]
    assert aa.kjv_passage("GEN 13:1", 6, rows) is None


def test_parse_list_and_code_are_strict():
    assert aa.parse_list('{"own_text": "yes", "items": ["Camels", "camels", "gold"]}') == {
        "own_text": True,
        "items": ["Camels", "gold"],
    }
    assert aa.parse_list('{"items": ["x"]}') is None
    assert aa.parse_list("no json here") is None
    ok = ('{"codes": [{"n": 1, "code": "attested", "kind": null}, {"n": 2, "code": '
          '"NOT_ATTESTED_THERE_THEN", "kind": "IN_THE_STORY"}]}')  # fmt: skip
    assert aa.parse_code(ok, 2) == [
        {"code": "ATTESTED", "kind": None},
        {"code": "NOT_ATTESTED_THERE_THEN", "kind": "IN_THE_STORY"},
    ]
    assert aa.parse_code(ok, 3) is None  # an item left uncoded: unreadable, never counted
    bad = '{"codes": [{"n": 1, "code": "NOT_ATTESTED_THERE_THEN", "kind": null}]}'
    assert aa.parse_code(bad, 1) is None  # an anachronism needs its kind


def test_kappa_and_matching():
    assert aa.kappa(["A", "B", "A", "B"], ["A", "B", "A", "B"]) == 1.0
    assert aa.kappa(["A", "A", "B", "B"], ["A", "B", "A", "B"]) == 0.0
    assert aa._matches("the city of Dan", ["dan"], exact=True)
    assert not aa._matches("Jordan", ["dan"], exact=True)
    codes = [{"code": "NOT_ATTESTED_THERE_THEN", "kind": "TRANSLATION_WORD"}]
    assert aa.found(["bow of steel"], codes, ["steel"], "TRANSLATION_WORD")
    assert not aa.found(["bow of steel"], codes, ["steel"], "IN_THE_STORY")


def _write(folder, name, rows):
    (folder / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


def _reply(items_codes):
    return json.dumps({"codes": [{"n": i + 1, "code": c, "kind": k}
                                 for i, (c, k) in enumerate(items_codes)]})  # fmt: skip


@pytest.fixture
def card(tmp_path, monkeypatch):
    monkeypatch.setattr(aa, "CARD", tmp_path)
    monkeypatch.setattr(aa, "LOGS", tmp_path / "logs")
    monkeypatch.setattr(aa, "out", lambda p: p.parent.mkdir(parents=True, exist_ok=True) or p)
    return tmp_path


def _check_files(card, plant_found=True, opus_code="ATTESTED"):
    known = [{"id": f"known|{k}", "prompt": "q"} for k in a113.KNOWN_JUDGE]
    _write(card, "jobs_reader.jsonl", known)
    _write(card, "answers_reader.jsonl", [
        {"id": f"known|{k}", "reply": json.dumps({"code": v, "loose_confirmed": "no"})}
        for k, v in a113.KNOWN_JUDGE.items()])  # fmt: skip
    lists = [
        {"id": "plant|clock|t1|0", "text": "t1", "passage": "p", "prompt": "q"},
        {"id": "case|camels|GEN 12:16", "text": "t1", "passage": "p", "prompt": "q"},
    ]
    _write(card, "jobs_check_list.jsonl", lists)
    _write(
        card,
        "answers_check_list.jsonl",
        [
            {"id": "plant|clock|t1|0", "reply": '{"own_text": "yes", "items": ["clock", "gold"]}'},
            {"id": "case|camels|GEN 12:16", "reply": '{"own_text": "yes", "items": ["camels"]}'},
        ],
    )
    code = [
        {"id": "plant|clock|t1|0", "text": "t1", "items": ["clock", "gold"], "prompt": "q"},
        {"id": "case|camels|GEN 12:16", "text": "t1", "items": ["camels"], "prompt": "q"},
    ]
    _write(card, "jobs_check_code.jsonl", code)
    clock = ("NOT_ATTESTED_THERE_THEN", "IN_THE_STORY") if plant_found else ("ATTESTED", None)
    _write(card, "answers_check_code.jsonl", [
        {"id": "plant|clock|t1|0", "reply": _reply([clock, ("ATTESTED", None)])},
        {"id": "case|camels|GEN 12:16",
         "reply": _reply([("NOT_ATTESTED_THERE_THEN", "IN_THE_STORY")])}])  # fmt: skip
    _write(card, "jobs_agree.jsonl", code[:1])
    _write(
        card,
        "answers_agree.jsonl",
        [{"id": "plant|clock|t1|0", "reply": _reply([clock, (opus_code, None)])}],
    )


def test_check_passes_and_misses_on_the_answers(card):
    _check_files(card)
    res = aa.run_check(_cfg())
    assert res["passed"], res
    assert res["a_planted"]["found"] == 1 and res["b_textbook"]["caught"] == 1
    assert res["c_agreement"]["kappa"] == 1.0 and res["d_reader"]["matched"] == 12
    _check_files(card, plant_found=False)
    assert not aa.run_check(_cfg())["passed"]


def test_check_refuses_while_open_or_unreadable(card):
    _check_files(card)
    (card / "answers_agree.jsonl").write_text(
        json.dumps({"id": "plant|clock|t1|0", "reply": "garbled"}) + "\n"
    )
    res = aa.run_check(_cfg())
    assert "refused" in res and res["answers"]["agree"]["unreadable"] == 1
    assert (card / "logs" / "ancient_anachronisms_unparsed_agree.jsonl").exists()


def test_score_rates_and_gate(card, monkeypatch):
    cfg = _cfg()
    monkeypatch.setattr(aa, "bom113", lambda: {})
    _check_files(card, plant_found=False)
    assert "refused" in aa.score(cfg)  # the check missed: nothing scored
    _check_files(card)
    lists = [
        {"id": "main|t1|0", "text": "t1", "passage": "p", "prompt": "q"},
        {"id": "main|t1|1", "text": "t1", "passage": "p", "prompt": "q"},
        {"id": "main|d1|0", "text": "d1", "passage": "p", "prompt": "q"},
        {"id": "main|d1|1", "text": "d1", "passage": "p", "prompt": "q"},
    ]
    _write(card, "jobs_list.jsonl", lists)
    _write(
        card,
        "answers_list.jsonl",
        [
            {"id": "main|t1|0", "reply": '{"own_text": "yes", "items": ["gold"]}'},
            {"id": "main|t1|1", "reply": '{"own_text": "no", "items": []}'},
            {"id": "main|d1|0", "reply": '{"own_text": "yes", "items": ["steel", "bow"]}'},
            {"id": "main|d1|1", "reply": '{"own_text": "yes", "items": []}'},
        ],
    )
    _write(
        card,
        "jobs_code.jsonl",
        [
            {"id": "main|t1|0", "text": "t1", "items": ["gold"], "prompt": "q"},
            {"id": "main|d1|0", "text": "d1", "items": ["steel", "bow"], "prompt": "q"},
        ],
    )
    assert "refused" in aa.score(cfg)  # code answers still open
    _write(
        card,
        "answers_code.jsonl",
        [
            {"id": "main|t1|0", "reply": _reply([("ATTESTED", None)])},
            {
                "id": "main|d1|0",
                "reply": _reply(
                    [
                        ("NOT_ATTESTED_THERE_THEN", "IN_THE_STORY"),
                        ("NOT_ATTESTED_THERE_THEN", "TRANSLATION_WORD"),
                    ]
                ),
            },
        ],
    )
    res = aa.score(cfg)
    t1, d1 = res["texts"]["t1"], res["texts"]["d1"]
    assert t1["passages_not_own_text"] == 1 and t1["words_scored"] == 5
    assert t1["per_10k"]["all"] == 0.0
    assert d1["words_scored"] == 10 and d1["anachronisms"] == {
        "in_the_story": 1,
        "translation_word": 1,
        "all": 2,
    }
    assert d1["per_10k"]["all"] == 2000.0
    assert res["comparison"]["all"]["decoys_vs_genuine"].startswith("the decoys stand apart")
