"""BOM-118 full run: frames catch their cited verses, round-robin draws, older-author flag."""

from lab.archaic_full import _round_robin, cited, decade, died, items, parse_hand
from metadata.config import load


def test_every_frame_matches_its_cited_1830_verse():
    cfg = load()
    its, cit = items(cfg), cited(cfg)
    assert len(its) == 48
    for name, it in its.items():
        assert cit[name]["found"], name
        if it["frame"]:
            assert cit[name]["frame_matches"], name
        else:
            assert it["reason"], name


def test_round_robin_takes_one_hit_per_work_first():
    works = [{"work_id": f"w{i}", "hits": {"x": [1, 2, 3]}} for i in range(4)]
    picked = _round_robin(works, "x", 6, "seed")
    assert len(picked) == 6
    assert len({w for w, _ in picked[:4]}) == 4
    assert _round_robin(works, "x", 100, "seed") and len(_round_robin(works, "x", 100, "s")) == 12


def test_died_reads_the_catalogued_author():
    assert died("Bunyan, John, 1628-1688.") == 1688
    assert died("Smith, John, d. 1701") == 1701
    assert died("Anonymous") is None


def test_1830_counts_with_the_1820s():
    cfg = load()
    assert decade(1830, cfg) == 1820 and decade(1745, cfg) == 1740


def test_second_reading_reply_is_read_from_its_first_word():
    assert parse_hand("OWN\nthe writer's own sentence") == "own_words"
    assert parse_hand("**QUOTE** - Isaiah") == "quotation_or_reprint"
    assert parse_hand("NOT\nordinary sense") == "not_claimed"
    assert parse_hand("Possibly own words") is None
