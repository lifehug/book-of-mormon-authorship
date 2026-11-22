"""BOM-106 (lab.spoken): the marks, the reading rules and the check, on made-up text."""

import random
import xml.etree.ElementTree as ET

import pytest

from lab import spoken

T = {
    "recent_window": 100,
    "formula_min": 3,
    "mattr_window": 10,
    "window_words": 50,
    "max_windows_target": 10,
    "trim_head": 0.0,
    "trim_tail": 0.0,
    "folds": 3,
    "c": 1.0,
    "seed": 7,
    "bar_auc_all": 0.85,
    "bar_auc_sermons": 0.75,
    "min_spoken_groups": 2,
}


def test_words_drops_punctuation_and_reads_ampersand():
    w = spoken.words("Don't go, & see&c. THE end!", set())
    assert w == ["dont", "go", "and", "see", "etc", "the", "end"]


def test_marks_counts_by_rule():
    w = ("and he said i i mean or rather that is to say i say " * 5).split()
    m = spoken.marks(w, T)
    n = len(w)
    assert m["and_rate"] == pytest.approx(5 * 1000 / n)
    assert m["and_clause"] == pytest.approx(5 * 1000 / n)  # "and he"
    assert m["repeat_word"] == pytest.approx(5 * 1000 / n)  # "i i"
    assert m["repair"] == pytest.approx(15 * 1000 / n)  # i mean, or rather, that is to say
    assert m["i_say"] == pytest.approx(5 * 1000 / n)
    assert m["recent_3gram"] > 0.5  # the same phrase again and again
    assert m["formula_4gram"] == pytest.approx(1.0)
    assert set(m) == set(spoken.FEATURES)


def test_passive_skips_common_non_participles():
    m = spoken.marks("it was then that they were taken and there were children".split(), T)
    assert m["passive"] == pytest.approx(1000 / 11)  # "were taken" only


def test_utterance_text_drops_reporters_actions():
    xml = '<u role="Witness">I found <activity>(producing it)</activity> this shirt.</u>'
    u = ET.fromstring(xml)
    assert spoken._utter_text(u) == "I found this shirt."


def test_group_key_merges_coauthor_spellings_and_untitled_volumes():
    a = spoken.group_key({"author_norm": "savery, william dillwyn george", "work_id": "x"})
    b = spoken.group_key({"author_norm": "savery, william", "work_id": "y"})
    assert a == b
    v1 = {"author_norm": "", "title": "The trial of Thomas Hardy for high treason, vol. 1"}
    v2 = {"author_norm": None, "title": "The trial of Thomas Hardy for high treason. Vol. II"}
    assert spoken.group_key({**v1, "work_id": "1"}) == spoken.group_key({**v2, "work_id": "2"})


def test_cap_groups_keeps_evenly_spaced_windows():
    rows = [{"group": "a", "i": i} for i in range(10)] + [{"group": "b", "i": 0}]
    kept = spoken.cap_groups(rows, 3)
    assert [r["i"] for r in kept if r["group"] == "a"] == [0, 4, 9] or [
        r["i"] for r in kept if r["group"] == "a"
    ] == [0, 5, 9]
    assert sum(r["group"] == "b" for r in kept) == 1


def test_place_position_scale():
    cen = {"written_median": -2.0, "spoken_median": 2.0, "sermons_printed_median": -1.0,
           "sermons_shorthand_median": 1.0}  # fmt: skip
    p = spoken.place([0.0, 0.0, 2.0], cen, 0.5)
    assert p["p"] == pytest.approx(0.5)
    assert p["p_sermons"] == pytest.approx(0.5)
    assert p["share_scored_spoken"] == pytest.approx(1 / 3, abs=1e-3)
    assert spoken.place([], cen, 0.0)["n"] == 0


def _rows(seed: int, gap: float) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for label, sets in ((1, ("S1_oldbailey", "S2_shorthand_sermons")),
                        (0, ("W1_printed_sermons", "W2_written_prose"))):  # fmt: skip
        for s in sets:
            for g in range(6):
                for _ in range(5):
                    r = {f: rng.gauss(0, 1) for f in spoken.FEATURES}
                    r["first_sg"] += gap * label
                    rows.append({"set": s, "label": label, "group": f"{s}{g}", "unit": "u", **r})
    return rows


def test_check_passes_when_separable_and_misses_when_not():
    pytest.importorskip("sklearn")  # the model extra; CI installs only the base packages
    good = spoken.check(_rows(1, 4.0), spoken.FEATURES, T)["result"]
    assert good["passed"] and good["auc_all"] > 0.95
    bad = spoken.check(_rows(2, 0.0), spoken.FEATURES, T)["result"]
    assert not bad["passes"]["A_all"]


def test_contributions_sum_to_total():
    pytest.importorskip("sklearn")  # the model extra; CI installs only the base packages
    rows = _rows(3, 3.0)
    ck = spoken.check(rows, spoken.FEATURES, T)
    spk = [r for r in rows if r["label"] == 1]
    wr = [r for r in rows if r["label"] == 0]
    c = spoken.contributions(ck["full"], spoken.FEATURES, spk, wr)
    assert sum(c["by_mark"].values()) == pytest.approx(c["total"], abs=0.05)
    assert next(iter(c["by_mark"])) == "first_sg"


def test_windows_equal_size_and_too_short():
    w = [str(i) for i in range(130)]
    ws = spoken.windows(w, T, 10, False)
    assert len(ws) == 2 and all(len(x) == 50 for x in ws)
    assert spoken.target_marks(w[:10], T) == "too short (10 words)"
    assert spoken.target_marks(None, T).startswith("not attempted")
