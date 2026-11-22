"""BOM-123: finding the phrase and variants, the referent rules, and the yearly counter's checks."""

from lab.combinations import (
    classify,
    compile_categories,
    count_literals,
    counter_check,
    find_uses,
    normalise,
    period_of,
    settings,
    verdict,
)
from metadata.config import load


def d() -> dict:
    return settings(load())


def test_phrase_finds_exact_and_variant_uses():
    low = normalise("They formed secret\ncombinations; a secret and unlawful combination too.")
    hits = find_uses(low, d())
    assert [h["exact"] for h in hits] == [True, False]
    assert hits[0]["mid"] == "secret combinations"
    assert "they formed" in hits[0]["left"]


def test_phrase_does_not_match_unrelated_text():
    assert find_uses(normalise("a combination of colours, secretly arranged"), d()) == []
    assert find_uses(normalise("secret, one, two, three combinations"), d()) == []


def test_freemasonry_by_window_and_others_by_nearest_term():
    cfg = d()
    cats = compile_categories(cfg)
    assert classify("the lodge of the masons held", "against the government", cats, 10)[0] == (
        "freemasonry"
    )
    assert classify("merchants raising the prices by", "of the party", cats, 10)[0] == "commercial"
    assert classify("the party and a faction of", "to murder and rob", cats, 10)[0] == "political"
    assert classify("nothing here", "at all", cats, 10) == ("other", False)


def test_masonic_term_far_in_the_window_is_not_near():
    cats = compile_categories(d())
    far = "masonry " + " ".join(["word"] * 20)
    label, near = classify(far, "", cats, 10)
    assert label == "freemasonry" and near is False


def test_literal_counts_and_periods():
    assert (
        count_literals(normalise("An Anti-Masonic meeting of the antimasonic"), d())["anti_masonic"]
        == 2
    )
    assert period_of(1828, d()) == "1828" and period_of(1805, d()) == "1800-1819"
    assert period_of(1650, d()) is None


def _scan(anti_before: int, anti_after: int, words: int = 10**8) -> dict:
    ys = {str(y): {"works": 1, "words": words, "all": 0, "exact": 0} for y in range(1780, 1830)}
    years = range(1780, 1830)
    lit = {
        "anti_masonic": {"1800": anti_before, "1828": anti_after},
        "steady_of_the": {str(y): 5 * words // 100 for y in years},
        "steady_in_the_course_of": {str(y): words // 1000 for y in years},
    }
    return {"by_year": {"works": ys}, "literals_by_year": {"works": lit}}


def test_counter_check_passes_on_a_rise_and_fails_when_flat():
    cfg = d()
    assert counter_check(_scan(0, 500), cfg)["passed"] is True
    assert counter_check(_scan(500, 500), cfg)["anti_masonic"]["passed"] is False


def test_verdict_reads_the_late_share():
    cfg = d()

    def t(uses, fm):
        return {"uses": uses, "labels": {"freemasonry": fm}}

    yes = verdict({"1800-1819": t(50, 5), "1827": t(30, 29), "1828": t(30, 30)}, cfg)
    no = verdict({"1800-1819": t(50, 5), "1827": t(30, 5), "1828": t(30, 10)}, cfg)
    few = verdict({"1827": t(3, 3)}, cfg)
    assert yes["answer"].startswith("yes") and no["answer"].startswith("no")
    assert few["answer"].startswith("cannot tell")
