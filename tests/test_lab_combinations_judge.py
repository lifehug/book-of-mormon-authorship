"""BOM-123, second design: reply parsing, the dedup rule, the check's arithmetic, score refusing."""

import pytest

from lab.combinations import normalise, settings
from lab.combinations_judge import (
    agrees,
    check_from,
    dedup_key,
    group_passages,
    overlap,
    parse_reply,
    passage_label,
    prompt,
    score,
    tally,
    v2,
    vogel,
    wide_uses,
)
from metadata.config import load


def s() -> dict:
    return v2(load())


def test_parse_reply_takes_a_label_and_nothing_else():
    assert parse_reply("freemasonry") == "freemasonry"
    assert parse_reply("  Freemasonry.\n") == "freemasonry"
    assert parse_reply("**political**") == "political"
    assert parse_reply("other society") == "other_society"
    assert parse_reply("other_society") == "other_society"
    assert parse_reply("Label: trade") == "trade"
    assert parse_reply("crime. The passage describes robbers.") == "crime"
    assert parse_reply("The phrase refers to freemasonry") is None
    assert parse_reply("masonic") is None
    assert parse_reply("") is None
    assert parse_reply(None) is None


def test_prompt_has_no_title_or_year_and_marks_the_phrase():
    p = prompt("the lodge met", "secret combination", "against them")
    assert "[secret combination]" in p
    assert "about 18" not in p
    assert "Reply with the label only." in p


def test_wide_uses_agree_with_the_scan_window():
    d = settings(load())
    text = normalise(" ".join(f"w{i}" for i in range(400)) + " a secret combination " + "x " * 300)
    wide = wide_uses(text, d, 150)
    assert len(wide) == 1 and len(wide[0]["left"].split()) == 150
    short = {"mid": "secret combination", "left": " ".join(wide[0]["left"].split()[-30:]),
             "right": " ".join(wide[0]["right"].split()[:30])}  # fmt: skip
    assert agrees(wide[0], short)
    assert not agrees(wide[0], {**short, "left": "something else entirely"})


def test_dedup_key_reads_long_s_and_ignores_punctuation():
    a = dedup_key("the fecret, defigns of a", "fitted to attract", 3)
    b = dedup_key("the secret designs of a", "fitted to attract!", 3)
    assert a == b == ["designs", "os", "a", "sitted", "to", "attract"]


def test_near_identical_passages_group_once():
    k = [f"w{i}" for i in range(20)]
    near = k[:17] + ["x", "y", "z"]  # 17 of 20 shared
    far = k[:10] + [f"z{i}" for i in range(10)]
    assert overlap(k, near) == 0.85
    groups = group_passages([("a|1", k), ("b|2", near), ("c|3", far)], 0.8)
    assert groups == [["a|1", "b|2"], ["c|3"]]


def test_passage_label_majority_then_smallest_id():
    labs = {"a": "political", "b": "freemasonry", "c": "freemasonry", "d": None}
    assert passage_label(["a", "b", "c", "d"], labs) == "freemasonry"
    assert passage_label(["b", "a"], {"a": "political", "b": "freemasonry"}) == "political"
    assert passage_label(["d"], labs) is None


def _classes(n_mason: int, n_trade: int, n_pol: int) -> dict:
    def uses(name: str, n: int) -> list[dict]:
        return [{"id": f"{name}|{i}", "key": [name, str(i)] * 10} for i in range(n)]

    return {"masonic": uses("m", n_mason), "trade": uses("t", n_trade),
            "politics": uses("p", n_pol)}  # fmt: skip


def test_check_passes_and_misses_on_made_up_answers():
    cl = _classes(30, 20, 40)
    ans = {u["id"]: "freemasonry" for u in cl["masonic"][:24]}  # 24/30 = 0.80
    ans |= {u["id"]: "unclear" for u in cl["masonic"][24:]}
    ans |= {u["id"]: "trade" for u in cl["trade"]}
    ans |= {u["id"]: "political" for u in cl["politics"][:37]}
    ans |= {u["id"]: "freemasonry" for u in cl["politics"][37:]}  # 57/60 not Masonic = 0.95
    r = check_from(cl, ans, s())
    assert r["attempted"] and r["passed"]
    assert r["measures_dedup"]["masonic_titled_labelled_freemasonry"] == 0.8
    assert r["measures_dedup"]["trade_politics_titled_not_freemasonry"] == 0.95
    ans |= {u["id"]: "unclear" for u in cl["masonic"][20:24]}  # 20/30: unclear is a miss
    r = check_from(cl, ans, s())
    assert r["attempted"] and not r["passed"]
    assert r["met"]["masonic_titled_labelled_freemasonry"] is False


def test_check_counts_reprints_once():
    cl = _classes(30, 20, 40)
    same = ["one"] * 20
    for u in cl["masonic"][:10]:
        u["key"] = same  # ten copies of one passage
    ans = {u["id"]: "freemasonry" for hs in cl.values() for u in hs}
    ans |= {u["id"]: "trade" for u in cl["trade"]} | {u["id"]: "political" for u in cl["politics"]}
    r = check_from(cl, ans, s())
    assert r["classes"]["masonic"]["uses"] == 30 and r["classes"]["masonic"]["passages"] == 21


def test_check_not_attempted_when_unanswered_unparsed_or_small():
    cl = _classes(30, 20, 40)
    full = {u["id"]: "freemasonry" for u in cl["masonic"]}
    full |= {u["id"]: "trade" for u in cl["trade"]} | {u["id"]: "political" for u in cl["politics"]}
    part = dict(list(full.items())[:-1])
    assert check_from(cl, part, s())["attempted"] is False
    bad = {k: ("I think so" if i < 10 else v) for i, (k, v) in enumerate(full.items())}
    r = check_from(cl, bad, s())
    assert r["attempted"] is False and r["unparsed"] == 10
    small = _classes(10, 5, 10)
    ans = {u["id"]: "freemasonry" for hs in small.values() for u in hs}
    assert check_from(small, ans, s())["attempted"] is False


def test_score_refuses_unless_the_check_passed():
    with pytest.raises(SystemExit):
        score(load(), chk={"passed": False, "reason": "bars missed"})
    with pytest.raises(SystemExit):
        score(load(), chk={"attempted": False, "passed": False})


def test_tally_weights_and_vogel_thresholds():
    t = tally([("freemasonry", 3.0), ("political", 1.0)])
    assert t["share_freemasonry"] == 0.5 and t["weighted_share_freemasonry"] == 0.75
    sv = s()
    late = tally([("freemasonry", 1.0)] * 19 + [("political", 1.0)])
    mid = tally([("political", 1.0)] * 20)
    assert vogel({"1827-1830": late, "1800-1825": mid}, sv)["answer"].startswith("yes")
    low = tally([("freemasonry", 1.0)] * 5 + [("trade", 1.0)] * 20)
    assert vogel({"1827-1830": low, "1800-1825": mid}, sv)["answer"].startswith("no")
    assert vogel({"1827-1830": tally([("freemasonry", 1.0)])}, sv)["answer"].startswith("cannot")
