"""BOM-118 pilot: patterns catch the cited forms, replies parse strictly, windows mark the hit."""

import re

from lab.archaic import decade, items, parse, window
from metadata.config import load


def test_reply_parses_only_the_fixed_form():
    assert parse("SENSE=A SOURCE=O") == ("A", "O")
    assert parse("  SENSE = B  SOURCE = Q. ") == ("B", "Q")
    assert parse("SENSE=A") is None
    assert parse("I think SENSE=A SOURCE=O") is None
    assert parse("SENSE=X SOURCE=O") is None
    assert parse("SENSE=A", 2) == ("A", "-")
    assert parse("SENSE=A SOURCE=O", 2) is None


def test_marked_shows_the_whole_text():
    from lab.archaic import marked

    s = "no monster  could break them, neither"
    i = s.index("break")
    assert marked(s, i, i + len("break them")) == ("no monster could [[break them]], neither")


def test_window_marks_the_hit():
    text = " ".join(f"w{i}" for i in range(100)) + " could break them neither " + "x " * 50
    m = re.search(r"break them", text)
    w = window(text, m.start(), m.end(), 10)
    assert "[[break them]]" in w
    assert len(w.split()) <= 10 + 2


def test_1830_counts_with_the_1820s():
    cfg = load()
    assert decade(1830, cfg) == 1820
    assert decade(1829, cfg) == 1820
    assert decade(1741, cfg) == 1740


def test_patterns_take_the_claimed_frame_and_leave_the_plain_one():
    its = items(load())
    hit = {
        "break": "no monster of the sea could break them",
        "belove": "among those who they so dearly beloved",
        "counsel": "counsel the Lord in all thy doings",
        "desirous": "it was desirous above all other fruit",
        "arrive_to": "they arrived to the land of Zarahemla",
        "be_aware": "let him be aware lest he",
        "begin_to": "he began to the creation of the world",
        "belief_on": "their belief on the words of Alma",
    }
    miss = {
        "break": "the bridge was broken",
        "belove": "his beloved daughter",
        "desirous": "he was desirous of peace",
        "arrive_to": "he arrived to sit for a picture",
        "be_aware": "we must be aware that it is so",
        "begin_to": "it began to rain",
    }
    for name, s in hit.items():
        assert its[name]["pattern"].search(s), name
    for name, s in miss.items():
        assert not its[name]["pattern"].search(s), name
