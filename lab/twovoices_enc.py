"""BOM-105 follow-up: prophets in two voices, measured by the study's two style encoders.

The function-word run (``lab.twovoices``) found Joseph Smith's gap between his revelations and his
ordinary writing typical of six writers. The study's original split came from its style encoders,
so this measures the same set with them, nothing retrained: BOM-30's encoder and the second
encoder trained for the library search (``lab.two_voices_enc.encoders``). The set and its
1,000-word chunks are ``lab.twovoices``'s own (``build_set``, ``chunks``); each chunk, in the
encoders' word form, is cut to its first ``style_embed.episode_passages`` passages of
``passage_tokens`` tokens (the episode the encoders were trained on) and embedded as one episode by
``sweep.index.episode_vectors``. Per encoder, with distance 1 - cosine: the within-voice
known-answer check, the gap index on equal profiles, cross-voice attribution with the pull control
(all ``lab.twovoices`` functions and the same rules), and an addition: does the encoder group by
voice or by person. The Book of Mormon is not read. Card, written first:
``data/private/lab/owner/2026-11-21-two-voices-encoders/card.md``. The result holds ids and
numbers; the chunk vectors stay in ``data/corpus/lab/two_voices_enc/``.

Usage::

    python -m lab.twovoices_enc embed [--encoder bom30|v2]   # Mac GPU; vectors per encoder
    python -m lab.twovoices_enc run     # -> data/lab/two_voices/result_encoders.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

from lab import twovoices as tv
from lab.paths import FAST, out
from metadata import config

OUT = tv.OUT / "result_encoders.json"
VECS = FAST / "two_voices_enc"
FW_RESULT = tv.OUT / "result.json"
# Training overlap (lesson 10), checked 2026-11-20 against data/style_embed/authors.parquet,
# v2_works.parquet, both passage indexes and data/timelocked_lm/training_set.parquet; the card says
# how. Same for both encoders (the second kept BOM-30's author split; both share the backbone).
TRAINING_OVERLAP = {
    "joseph_smith": "none: no text of his is in the catalog, the backbone's training set or either "
    "encoder's authors (the set uses the study's private candidate samples)",
    "john_wroe": "backbone only: Life and Journal (his ordinary source) is in the backbone "
    "language model's training volumes; not an encoder author",
    "joanna_southcott": "ENCODER TRAINING AUTHOR: both set volumes (firstsecondbooko00sout, "
    "b22042076) gave training passages to both encoders (32 each; 256 each)",
    "anna_trapnel": "none",
    "richard_snowden": "backbone only: two other printings of his History (1806, 1811) are in the "
    "backbone's training volumes; not an encoder author",
    "elias_smith": "ENCODER TRAINING AUTHOR: his ordinary volume (lifecon00smit) gave training "
    "passages to both encoders (32; 256); History of Anti-Christ did not",
}
SETTINGS = ("chunk_words", "profile_chunks", "train_chunks", "resamples", "known_bar",
            "cross_share", "larger_than_any_share", "min_writers", "seed")  # fmt: skip
BOM_SEALED = "the Book of Mormon's library copies are sealed, training none, and gave no passage"


def chunk_ids(ids: list[int], n: int, per: int) -> list[int]:
    """The first ``per`` passages of ``n`` tokens of a chunk (all of it when shorter)."""
    return ids[: n * per]


def embed(cfg: dict, name: str) -> dict:
    """Vectors of every chunk of every writer and voice under one encoder; written to ``VECS``."""
    import torch
    from tokenizers import Tokenizer

    from style_embed.train import load_encoder
    from sweep.index import episode_vectors
    from timelocked_lm.release import TOKENIZER

    t, s = cfg["lab"]["two_voices"], cfg["style_embed"]
    path = Path(cfg["lab"]["two_voices_enc"]["encoders"][name])
    if not path.exists():
        raise OSError(f"encoder weights missing: {path}")
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    vocab, _ = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    _, texts = tv.build_set(cfg, vocab)
    enc = load_encoder(path, cfg).to(dev)
    tok = Tokenizer.from_file(str(TOKENIZER))
    n, per = s["passage_tokens"], s["episode_passages"]
    arrays, short = {}, {}
    for w, by in texts.items():
        for v in tv.VOICES:
            vs, lens = [], []
            for ch in tv.chunks(by[v], t["chunk_words"]):
                ids = chunk_ids(tok.encode(" ".join(ch)).ids, n, per)
                lens.append(len(ids))
                vs.append(episode_vectors(enc, ids, n, per, dev)[0][0])
            arrays[f"{w}|{v}"] = np.stack(vs).astype(np.float32)
            short[f"{w}|{v}"] = sum(x < n * per for x in lens)
    p = out(VECS / f"vectors_{name}.npz")
    np.savez(p, _short=np.array(json.dumps(short)), **arrays)
    print(f"{name}: {sum(len(a) for a in arrays.values())} chunks on {dev} -> {p}; "
          f"chunks under {n * per} tokens: {sum(short.values())}")  # fmt: skip
    return short


def load_vectors(name: str) -> dict:
    """{writer: {voice: (chunks, dim)}} and ``_short``; ``OSError`` when not embedded yet."""
    p = VECS / f"vectors_{name}.npz"
    if not p.exists():
        raise OSError(f"{p} missing: run embed --encoder {name}")
    z = np.load(p)
    res: dict = {}
    for k in z.files:
        if k == "_short":  # chunks shorter than one full episode, per writer|voice
            res.setdefault("_short", json.loads(str(z[k])))
            continue
        w, v = k.split("|")
        res.setdefault(w, {})[v] = z[k].astype(np.float64)
    return res


def gaps(z: dict, cfg: dict, dist) -> dict:
    """``lab.twovoices.gaps`` with ``dist`` in place of Burrows's Delta (that function fixes its
    distance): equal profiles of ``profile_chunks`` chunks, ``resamples`` draws, the same seed."""
    t = cfg["lab"]["two_voices"]
    rng = np.random.default_rng(t["seed"])
    names = sorted(z)
    k = t["profile_chunks"]
    keys = ("self", "index", "closer", "pp", "oo")
    draws = {w: {x: [] for x in keys} for w in names}
    above_all = 0
    for _ in range(t["resamples"]):
        prof = {
            (w, v): z[w][v][rng.choice(len(z[w][v]), size=k, replace=False)].mean(axis=0)
            for w in names
            for v in tv.VOICES
        }
        idx = {}
        for w in names:
            others = [o for o in names if o != w]
            s = dist(prof[(w, "prophetic")], prof[(w, "ordinary")])
            pp = [dist(prof[(w, "prophetic")], prof[(o, "prophetic")]) for o in others]
            oo = [dist(prof[(w, "ordinary")], prof[(o, "ordinary")]) for o in others]
            idx[w] = s / float(np.median(oo))
            d = draws[w]
            d["self"].append(s)
            d["index"].append(idx[w])
            d["closer"].append(sum(s < x for x in pp) / len(pp))
            d["pp"].append(float(np.median(pp)))
            d["oo"].append(float(np.median(oo)))
        if "joseph_smith" in idx:
            above_all += all(idx["joseph_smith"] > v for w, v in idx.items() if w != "joseph_smith")

    def q(xs):
        return [round(float(np.percentile(np.array(xs), p)), 4) for p in (2.5, 50, 97.5)]

    per = {
        w: {
            "self_gap": q(d["self"]),
            "gap_index": q(d["index"]),
            "closer_to_self_share": q(d["closer"]),
            "median_dist_to_other_prophetic": q(d["pp"]),
            "median_dist_to_other_ordinary": q(d["oo"]),
        }
        for w, d in draws.items()
    }
    order = sorted(names, key=lambda w: -per[w]["gap_index"][1])
    res = {"per_writer": per, "order_by_gap_index": order, "writers": len(names)}
    if "joseph_smith" in names:
        res["joseph_smith_rank"] = order.index("joseph_smith") + 1
        res["joseph_smith_above_all_share"] = round(above_all / t["resamples"], 3)
    return res


def voice_or_person(z: dict) -> dict:
    """Addition (see the card): each writer's scripture-voice centroid against the other writers'
    scripture-voice centroids (mean cosine, and the closest one) and against the writer's own
    ordinary centroid; the share of writers whose scripture voice sits nearer the others'."""
    cent = {(w, v): z[w][v].mean(axis=0) for w in z for v in tv.VOICES}
    names = sorted(z)

    def cos(a, b):
        return 1 - tv.cosine_delta(a, b)

    per = {}
    for w in names:
        others = [cos(cent[(w, "prophetic")], cent[(o, "prophetic")]) for o in names if o != w]
        own = cos(cent[(w, "prophetic")], cent[(w, "ordinary")])
        per[w] = {
            "cos_to_own_ordinary": round(own, 4),
            "mean_cos_to_other_prophetic": round(float(np.mean(others)), 4),
            "max_cos_to_other_prophetic": round(float(np.max(others)), 4),
            "by_voice_mean": bool(np.mean(others) > own),
            "by_voice_closest": bool(np.max(others) > own),
        }
    n = len(names)
    return {
        "per_writer": per,
        "share_by_voice_mean": round(sum(p["by_voice_mean"] for p in per.values()) / n, 3),
        "share_by_voice_closest": round(sum(p["by_voice_closest"] for p in per.values()) / n, 3),
    }


def fw_voice_or_person(fw: dict) -> dict:
    """The addition's count from the function-word result: a writer groups by voice when the
    median Delta from his or her prophetic profile to the others' is below the self gap (medians
    of the resamples; median, not mean, over the other writers: that is what result.json holds)."""
    per = fw["gaps"]["per_writer"]
    by = {w: p["median_delta_to_other_prophetic"][1] < p["self_gap"][1] for w, p in per.items()}
    return {"by_voice": by, "share_by_voice": round(sum(by.values()) / len(by), 3)}


def score(z: dict, groups: dict, cfg: dict) -> dict:
    t = cfg["lab"]["two_voices"]
    dist = tv.cosine_delta
    ka = tv.within_voice(z, cfg, dist)
    res: dict = {
        "chunks": {w: {v: len(z[w][v]) for v in tv.VOICES} for w in z},
        "known_answer": {
            "cosine": ka,
            "bar": t["known_bar"],
            "passed": all((ka[v]["macro"] or 0) >= t["known_bar"] for v in tv.VOICES),
        },
    }
    if not res["known_answer"]["passed"]:
        res["stopped"] = "the within-voice check missed its bar; cross-voice and gaps not scored"
        return res
    res["cross_voice"] = tv.cross_voice(z, cfg, dist)
    res["gaps"] = gaps(z, cfg, dist)
    # lab.twovoices.verdicts reads the cross-voice block under "burrows"; here it is cosine.
    res["verdicts"] = tv.verdicts({"cross_voice": {"burrows": res["cross_voice"]},
                                   "gaps": res["gaps"]}, groups, cfg)  # fmt: skip
    res["addition_voice_or_person"] = voice_or_person(z)
    return res


def run(cfg: dict) -> dict:
    t = cfg["lab"]["two_voices"]
    vocab, _ = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    the_set, _ = tv.build_set(cfg, vocab)
    groups = {w: r["group"] for w, r in the_set["writers"].items()}
    s = cfg["style_embed"]
    res: dict = {
        "exploratory": True,
        "writers": groups,
        "settings": {
            **{k: t[k] for k in SETTINGS},
            "passage_tokens": s["passage_tokens"],
            "episode_passages": s["episode_passages"],
            "distance": "1 - cosine",
            "encoders": cfg["lab"]["two_voices_enc"]["encoders"],
        },
        "training_overlap": TRAINING_OVERLAP,
        "book_of_mormon": BOM_SEALED + "; not read or scored here",
        "encoders": {},
        "not_attempted": {},
    }
    for name in cfg["lab"]["two_voices_enc"]["encoders"]:
        try:
            z = load_vectors(name)
        except OSError as e:
            res["not_attempted"][name] = str(e)
            continue
        res["encoders"][name] = score({w: z[w] for w in groups if w in z}, groups, cfg)
        res["encoders"][name]["chunks_under_one_episode"] = z.get("_short")
    try:
        fw = json.loads(FW_RESULT.read_text())
        res["function_words"] = {
            "source": str(FW_RESULT),
            "known_answer_macro": {
                d: {v: fw["known_answer"][d][v]["macro"] for v in tv.VOICES}
                for d in ("burrows", "cosine")
            },
            "gap_index": {w: p["gap_index"] for w, p in fw["gaps"]["per_writer"].items()},
            "joseph_smith_rank": fw["gaps"]["joseph_smith_rank"],
            "verdicts": fw["verdicts"],
            "addition_voice_or_person": fw_voice_or_person(fw),
        }
    except (OSError, KeyError) as e:
        res["not_attempted"]["function_words"] = str(e)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["embed", "run"])
    ap.add_argument("--encoder", help="embed: one encoder name (default: every one in the config)")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "embed":
        for name in [a.encoder] if a.encoder else list(cfg["lab"]["two_voices_enc"]["encoders"]):
            embed(cfg, name)
        return 0
    res = run(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT).write_text(json.dumps(res, indent=1) + "\n")
    for name, r in res["encoders"].items():
        v = r.get("verdicts", {})
        add = r.get("addition_voice_or_person", {})
        print(name, {vv: r["known_answer"]["cosine"][vv]["macro"] for vv in tv.VOICES},
              "rank", r.get("gaps", {}).get("joseph_smith_rank"), v.get("joseph_smith_gap"),
              "crossing", v.get("others_crossing"),
              "by voice", add.get("share_by_voice_mean"))  # fmt: skip
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
