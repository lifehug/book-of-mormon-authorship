"""BOM-101: the pair rules keep real cross-register pairs and drop reprints; the draws put one
register on each side of a batch; the card's rule reads the numbers as written."""

from collections import Counter

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from lab import voiceenc as ve
from lab import voiceenc_eval as vee


def _cfg(**over):
    v = {"held_out_writers": ["southcott, joanna", "smith, elias"],
         "exclude_genres": ["uncertain", "PARSE_FAIL", "other"],
         "religious_genres": ["sermon_devotional"], "title_jaccard_max": 0.5, "ngram": 10,
         "ngram_share_max": 0.05, "spot_sample": 5, "min_train_authors": 1,
         "max_text_flag_share": 0.05, "cross_step_share": 1.0, "religious_step_share": 0.5,
         "seed": "t", "steps": 100, "warmup_steps": 10, "min_lr_share": 0.1,
         "resamples": 50, "within_voice_tolerance": 0.03, **over}  # fmt: skip
    return {"seed": 1, "lab": {"voice_encoder": v, "two_voices": {"train_chunks": 20,
                                                                   "known_bar": 0.8}},
            "style_embed": {"episode_passages": 2, "passage_tokens": 16}}  # fmt: skip


def test_held_out_writers_match_every_name_form():
    p = ["southcott, joanna", "smith, elias"]
    assert ve.held_out("southcott, joanna n 81055374", p)
    assert ve.held_out("smith, elias", p)
    assert not ve.held_out("smith, eli", p) and not ve.held_out("burroughs, stephen", p)


def test_title_rule_catches_a_retitled_reprint_only():
    assert ve.title_alike("new paris guide", "galignani s new paris guide", 0.5)
    assert ve.title_alike("sermons on several occasions", "sermons on several occasions vol", 0.5)
    assert not ve.title_alike("a journal of the life", "sermons preached at bristol", 0.5)


def test_text_check_flags_shared_text_and_passes_different_text():
    rng = np.random.default_rng(0)
    a = rng.integers(0, 30000, size=(20, 64))
    b = rng.integers(0, 30000, size=(20, 64))
    same = np.concatenate([a[:10], b[:10]])  # half of its passages are A's
    ha = ve.gram_hashes(a, 10)
    assert ve.shared_share(ha, ve.gram_hashes(same, 10)) >= 0.5
    assert ve.shared_share(ha, ve.gram_hashes(b, 10)) == 0.0


def test_author_pairs_apply_the_three_rules_in_order():
    rng = np.random.default_rng(1)
    data = rng.integers(0, 30000, size=(40, 16)).astype(np.uint16)
    data[30:40] = data[0:10]  # work d is a reprint of work a under another title

    def w(name, genre, rows, groups=()):
        return {
            "author": "x",
            "work": name,
            "split": "train",
            "genre": genre,
            "decade": 1800,
            "groups": list(groups),
            "rows": list(rows),
        }

    works = [w("journal of my life", "history_chronicle", range(0, 10), ["g1"]),
             w("sermons at bristol", "sermon_devotional", range(10, 20)),
             w("journal of my life and travels", "fiction_narrative", range(20, 30)),
             w("collected letters", "legal_political", range(30, 40), ["g1"])]  # fmt: skip
    pairs, n = ve.author_pairs(works, data, _cfg(ngram=4))
    rule = {(p["w1"], p["w2"]): p["rule"] for p in pairs}
    assert rule["journal of my life", "collected letters"] == "registry_duplicate_group"
    assert rule["journal of my life", "journal of my life and travels"] == "title"
    assert rule["journal of my life", "sermons at bristol"] == "kept"
    assert n["cross:kept"] >= 3


def _draws(tmp_path):
    works, pairs = [], []
    for i in range(12):
        a = f"author{i:02d}"
        for k in range(2):
            works.append(
                {
                    "author": a,
                    "work": f"w{k}",
                    "rows": list(range(8 * i + 4 * k, 8 * i + 4 * k + 4)),
                }
            )
        pairs.append({"author": a, "split": "train" if i < 8 else "heldout", "w1": "w0",
                      "w2": "w1", "g1": "sermon_devotional", "g2": "history_chronicle",
                      "d1": 1800, "d2": 1810, "cross": True, "rule": "kept"})  # fmt: skip
    pq.write_table(pa.Table.from_pylist(works), tmp_path / "works.parquet")
    pq.write_table(pa.Table.from_pylist(pairs), tmp_path / "pairs.parquet")
    data = np.arange(96 * 16, dtype=np.uint16)
    return ve.Draws(_cfg(), data=data, d=tmp_path)


def test_cross_steps_put_one_register_on_each_side(tmp_path):
    dr = _draws(tmp_path)
    kind, picks = dr.plan(3, 4)
    assert kind.startswith("cross")
    assert len({a for a, _, _ in picks}) == 4
    firsts = {w1 for _, w1, _ in picks}
    assert len(firsts) == 1  # the same register for every author on the first side
    assert dr.plan(3, 4) == (kind, picks)  # a pure function of the step
    _, x = dr.draw(3, 4)
    assert tuple(x.shape) == (8, 2, 16)


def test_verification_set_draws_negatives_from_the_partner_register(tmp_path):
    dr = _draws(tmp_path)
    vs = dr.verification_set("heldout", 4, 2, "test")
    assert len(vs["items"]) == 4 and vs["a"].shape == (4, 2, 16)
    for i, js in enumerate(vs["neg"]):
        assert i not in js and len(js) == 2


def test_auc_and_schedule():
    assert ve.auc(np.array([3.0, 4.0]), np.array([1.0, 2.0])) == 1.0
    assert ve.auc(np.array([1.0]), np.array([1.0])) == 0.5
    v = _cfg()["lab"]["voice_encoder"]
    assert ve.lr_scale(0, v) == 0.1 and abs(ve.lr_scale(10, v) - 1.0) < 1e-9
    assert abs(ve.lr_scale(100, v) - 0.1) < 1e-9


def test_cross_macro_finds_writers_who_keep_their_direction():
    rng = np.random.default_rng(2)
    base = {w: rng.normal(size=8) for w in "abc"}
    z = {w: {v: base[w] + 0.1 * rng.normal(size=(5, 8)) for v in ("prophetic", "ordinary")}
         for w in "abc"}  # fmt: skip
    m, rates = ve_m = vee.cross_macro(z, 20, np.random.default_rng(0))
    assert m == 1.0 and len(rates) == 6 and ve_m[0] == m


def _six(new_macro, diff_lo, ka_new=0.95):
    enc = {}
    for e, m, ka in (("bom30", 0.70, 0.98), ("v2", 0.75, 0.93), ("voice", new_macro, ka_new)):
        enc[e] = {
            "cross_voice_macro": m,
            "known_answer": {"cosine": {v: {"macro": ka} for v in ("prophetic", "ordinary")}},
        }
    diff = {"voice-bom30": [diff_lo, 0.1, 0.2], "voice-v2": [diff_lo, 0.05, 0.1]}
    return {"encoders": enc, "paired": {"difference": diff}}


def test_verdict_follows_the_card():
    held = {"encoders": {"v2": {"all": {"auc": 0.8}}, "voice": {"all": {"auc": 0.82}}}}
    cfg = _cfg()
    assert vee.verdict(_six(0.85, 0.01), held, cfg)["answer"] == "yes"
    assert vee.verdict(_six(0.85, -0.02), held, cfg)["answer"] == "cannot tell"
    assert vee.verdict(_six(0.72, -0.05), held, cfg)["answer"] == "no"
    assert vee.verdict(_six(0.85, 0.01, ka_new=0.90), held, cfg)["answer"] == "no"
    low = {"encoders": {"v2": {"all": {"auc": 0.8}}, "voice": {"all": {"auc": 0.79}}}}
    assert vee.verdict(_six(0.85, 0.01), low, cfg)["answer"] == "no"


def test_summary_counts_the_check():
    pairs = [
        {
            "author": f"a{i}",
            "split": "train",
            "w1": "x",
            "w2": "y",
            "g1": "sermon_devotional",
            "g2": "history_chronicle",
            "cross": True,
            "rule": "kept",
        }
        for i in range(30)
    ]
    pairs.append({"author": "b", "split": "train", "w1": "x", "w2": "z", "g1": "history_chronicle",
                  "g2": "fiction_narrative", "cross": True, "rule": "text_check"})  # fmt: skip
    s = ve.summarise(pairs, Counter(), _cfg())
    assert s["per_split"]["train"]["religious_pairs"] == 30
    assert s["text_check_share_after_registry_and_title"] == round(1 / 31, 4)
    assert s["check"]["passed"] is True and len(s["spot_sample"]) == 5
