"""BOM-109: the three-worlds rules count markers, set world values by majority, keep only the
features where the worlds disagree, and side a text with the world it agrees with most."""

from lab import threeworlds as tw
from lab import threeworlds_features as feat
from metadata import config

NE, MS, AM = feat.WORLDS
ST = {"present_min": 3, "present_rate": 0.1, "absent_min_words": 10000, "vig_share": 0.75,
      "vig_min_n": 15, "world_min_stating": 2, "world_majority": 0.6, "known_bar_share": 0.6,
      "known_pass_share": 1.0, "bootstrap": 200, "seed": 1}  # fmt: skip
CFG = {"lab": {"three_worlds": ST}}


def text(counts: dict, words: int = 20000, base20=(0, 0)) -> dict:
    return {"words": words, "counts": counts, "base20": list(base20)}


def test_markers_handle_phrases_hyphens_and_case():
    c = tw.count_segment("Two humming-birds, Indian corn, a Turkey and a turkey in January "
                         "and january, the first month, in 1812, year of our Lord.")  # fmt: skip
    assert c["nw_animals"] == 2  # humming-birds; lower-case turkey only
    assert c["maize"] == 1
    assert c["roman_months"] == 1  # capitalised only
    assert c["ordinal_months"] == 1
    assert c["ad_years"] == 2


def test_state_present_absent_and_not_stated():
    assert tw.state(text({"horses": 5}), "horses", ST) == "present"
    assert tw.state(text({}), "horses", ST) == "absent"
    assert tw.state(text({"horses": 1}), "horses", ST) == "not stated"
    assert tw.state(text({}, words=5000), "horses", ST) == "not stated"  # too short for absence
    assert tw.state(text({}, base20=(16, 2)), "vigesimal", ST) == "present"
    assert tw.state(text({}, base20=(5, 15)), "vigesimal", ST) == "absent"
    assert tw.state(text({}, base20=(3, 2)), "vigesimal", ST) == "not stated"


def test_world_values_majority_unsettled_and_coded():
    counts = {"a": text({"copper": 9}), "b": text({"copper": 9}), "c": text({}),
              "d": text({"copper": 9}), "e": text({}), "f": text({"copper": 1})}  # fmt: skip
    roles = {"a": ("source", NE), "b": ("source", NE), "c": ("source", NE),
             "d": ("source", MS), "e": ("source", MS), "f": ("source", AM),
             "k": ("known", NE)}  # fmt: skip
    counts["k"] = text({"copper": 99})
    v = tw.world_values(counts, roles, CFG)
    assert v["copper"][NE]["value"] == "present"  # 2 of 3
    assert v["copper"][MS]["value"] == "unsettled"  # 1 and 1
    assert v["copper"][AM]["value"] == "unsettled"  # nothing stated
    assert v["copper"][NE]["present"] == 2  # the known text is never a source
    assert v["horses"][MS]["value"] == "absent"  # coded from Clavigero
    assert v["horses"][MS]["kind"] == "held"


def test_discordant_drops_concordant_and_unsettled():
    v = {
        "x": {w: {"value": "present"} for w in feat.WORLDS},
        "y": {NE: {"value": "present"}, MS: {"value": "absent"}, AM: {"value": "unsettled"}},
        "z": {NE: {"value": "present"}, MS: {"value": "absent"}, AM: {"value": "absent"}},
    }
    keep, dropped = tw.discordant(v)
    assert keep == ["z"]
    assert dropped["concordant"] == ["x"] and dropped["unsettled"] == ["y"]


def test_side_counts_agreements_and_the_bar():
    v = {
        "horses": {NE: {"value": "present"}, MS: {"value": "absent"}, AM: {"value": "present"}},
        "copper": {NE: {"value": "absent"}, MS: {"value": "absent"}, AM: {"value": "present"}},
        "coins": {NE: {"value": "absent"}, MS: {"value": "present"}, AM: {"value": "present"}},
    }
    s = tw.side(text({"horses": 9}), list(v), v, CFG)
    assert s["agree"] == {NE: 3, MS: 1, AM: 1}
    assert s["sole"] == {NE: 1, MS: 0, AM: 0}
    assert s["sides_with"] == NE
    assert tw.passes(s, NE, CFG) and not tw.passes(s, MS, CFG)
    assert set(tw.bootstrap(s["features"], CFG)) <= {NE, MS, AM, "tie"}


def test_feature_list_and_citations_are_well_formed():
    assert len(feat.RULE) == 56 and len(feat.READING) == 12
    held_out = set(config.load()["lab"]["three_worlds"]["known_kjv"])
    names = {"1KI": "1 Kings", "2KI": "2 Kings"}
    for spec in feat.READING.values():
        assert set(spec["values"]) == set(feat.WORLDS)
        for _desc, (kind, where, _words) in spec["values"].values():
            assert kind in ("kjv", "held", "memory")
            assert not any(where.startswith(names[b] + " ") for b in held_out)
    for spec in feat.RULE.values():
        assert ("markers" in spec) != ("special" in spec)
        for value, _where, kind, _words in spec.get("coded", {}).values():
            assert value in ("present", "absent") and kind in ("held", "memory")


def test_book_coinages_are_not_markers():
    words = {w for rows in tw.MARKERS.values() for ws, _ in rows for w in ws}
    assert not words & {"senine", "seon", "shum", "limnah", "cureloms", "cumoms", "liberty"}
