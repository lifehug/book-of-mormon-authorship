"""BOM-111: the inventory lists compile, the matching rules hold, a planted world is found."""

import numpy as np

from lab import inventory as inv
from metadata import config


def found(text: str) -> list[str]:
    return [lm for _, lm in inv.occurrences(inv.words_of(text))]


def test_lists_compile_without_collisions_and_every_item_has_a_category():
    assert inv.LEX["collisions"] == []
    assert len(inv.LEMMAS) > 1500
    assert {v["category"] for v in inv.LEX["items"].values()} == set(inv.CATEGORIES)
    assert "corn" not in inv.INDEX  # counted apart
    assert all(lm in inv.LEX["items"] for lm in ("maize", "horse", "iron", "jade", "turkey"))


def test_matching_rules():
    assert found("They ate Indian corn and maize, and the corn of the field") == [
        "maize", "maize", "corn"]  # fmt: skip
    assert found("they bow down before him") == []  # a verb
    assert found("he took his bow and many arrows") == ["bow", "arrow"]
    assert found("Turkey is far; a turkey ran") == ["turkey"]  # capitalised homonym ignored
    assert found("the sweet potato and horses") == ["sweet potato", "horse"]
    assert found("a watch in the fort") == []  # removed before counting


def test_long_s_and_line_end_hyphens_are_read():
    inv.set_vocab(["the soldiers drew their swords and the sword was steel " * 3])
    try:
        assert inv.words_of("the foldiers drew fwords") == ["the", "soldiers", "drew", "swords"]
        assert inv.words_of("the vali-\nant sword") == ["the", "valiant", "sword"]
    finally:
        inv.set_vocab([])


def test_counts_cut_into_chunks():
    text = "horse " * 10 + "the " * 90 + "sword " * 5 + "the " * 95
    res = inv.count_text(text, 100)
    assert res["words"] == 200
    assert res["whole"] == {"horse": 10, "sword": 5}
    assert res["chunks"] == [{"horse": 10}, {"sword": 5}]


def test_rarity_weight_is_higher_for_rarer_items():
    sample = [{"whole": {"house": 3}}] * 4 + [{"whole": {"ox": 1}}] * 5 + [{"whole": {"jaguar": 2}}]
    w, df = inv.rarity_weights(sample)
    assert w[inv.INDEX["jaguar"]] > w[inv.INDEX["house"]] > 0
    assert df[inv.INDEX["house"]] == 4


def planted(cfg: dict) -> dict[str, dict]:
    words = {
        "near_east": ("ox", "camel", "temple"),
        "mesoamerica": ("jaguar", "maize", "jade"),
        "american": ("beaver", "musket", "wigwam"),
        "background": ("table", "hat", "school"),
    }
    texts = {}
    for world, items in words.items():
        for k in range(4):
            whole = {items[0]: 20 + k, items[1]: 10, items[2]: 5, "house": 30}
            texts[f"{world}{k}"] = {
                "world": world,
                "register": "x",
                "words": 20000,
                "whole": whole,
                "chunks": [whole, whole],
            }
    return texts


def test_a_planted_world_is_found_and_resampling_agrees():
    cfg = config.load()
    texts = planted(cfg)
    sample = [{"whole": {"house": 1}}] * 10 + [{"whole": {"house": 1, "ox": 1}}]
    w, _ = inv.rarity_weights(sample)
    sp = inv.Space(texts, w, np.ones(len(inv.LEMMAS)), cfg)
    ho = inv.held_out(sp, cfg)
    assert ho["whole"]["pooled"] == 1.0
    probe = {"whole": {"jaguar": 7, "maize": 3, "house": 20}, "words": 20000}
    prof = sp.profiles(inv.members(texts))
    x = sp.vector(probe["whole"], probe["words"])
    assert inv.best(inv.cosines(x, prof)) == "mesoamerica"
    boot = inv.resample(sp, x, prof, cfg)
    assert abs(sum(boot["closest_share"].values()) - 1) < 1e-9


def test_the_allowance_mask_drops_the_allowance_items_only():
    m = inv.allowance_mask()
    assert m[inv.INDEX["tiger"]] == 0 and m[inv.INDEX["horse"]] == 0
    assert m[inv.INDEX["jade"]] == 1


def test_gloss_counts_find_a_glossed_old_world_word_beside_a_new_world_item():
    cfg = config.load()
    words = ("they have a beast they call a tiger near the maize " + "the " * 30).split()
    res = inv.gloss_counts(words, cfg)
    assert res["uses"] == 1 and res["glossed"] == 1 and res["near_new_world_item"] == 1
