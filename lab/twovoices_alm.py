"""BOM-105 follow-up: prophets in two voices, measured by the study's author language models.

Function words (``lab.twovoices``) and both style encoders (``lab.twovoices_enc``) found Joseph
Smith's gap between his revelations and his ordinary writing typical of six writers. The study's
original finding also came from author models, so this fine-tunes one copy of the 125M time-locked
base model per writer per voice and asks: does a writer's ordinary-voice model recognise the same
writer's scripture voice (and the reverse), and is Joseph Smith different from the other five?

Reused, not edited: ``alm.benchmark._base``, ``finetune`` (the recipe: 3 epochs, 1,024-token
sequences, batches of 8, learning rate ``timelocked_lm.finetune_lr``), ``window_losses`` (the
5.2 score: mean 512-token window loss minus the base model's), ``eval.library_pool.small_tokens``
(Amendment 45's equal dose) and ``eval.library_pool.scaled`` (each model on its own scale). The
set is ``lab.twovoices.build_set``; King James 5-grams are dropped (``drop_kjv``) in the masked
runs. Every model gets the same number of training tokens from the start of its writer's voice;
everything after is held out in 1,000-word chunks and scored by every model of the run and by the
base model. Steps: within-voice known-answer check (bar ``lab.two_voices.known_bar``), cross-voice
attribution both ways with the pull control, voice or person. The Book of Mormon is not read.
Card, written first: ``data/private/lab/owner/2026-11-21-two-voices-author-models/card.md``;
settings ``lab.two_voices_alm``. Weights and per-model losses stay in
``data/corpus/lab/two_voices_alm/`` (not git); the result holds ids and numbers.

Usage::

    python -m lab.twovoices_alm plan              # doses, held-out chunks per run (seconds, CPU)
    python -m lab.twovoices_alm train [--run R] [--limit N]   # Mac GPU; resumes per model
    python -m lab.twovoices_alm run               # -> data/lab/two_voices/result_author_models.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import time

import numpy as np

from lab import twovoices as tv
from lab.paths import FAST, out
from metadata import config

OUT = tv.OUT / "result_author_models.json"
WORK = FAST / "two_voices_alm"
ENC_RESULT = tv.OUT / "result_encoders.json"
FW_RESULT = tv.OUT / "result.json"
JS = "joseph_smith"
# Lesson 10, checked 2026-11-20 against data/timelocked_lm/training_set.parquet and the catalog:
# what of each writer the 125M base model read in pretraining (the card says how it can bias).
TRAINING_OVERLAP = {
    "joseph_smith": "none: no text of his is in the catalog or the base model's training set",
    "john_wroe": "ordinary source in base training: Life and Journal (1829, "
    "institutional_books:32044081829434, split train); scripture source (1846) in nothing",
    "joanna_southcott": "both set volumes in base training (firstsecondbooko00sout, b22042076), "
    "with about 25 other Southcott volumes",
    "anna_trapnel": "none (TCP texts are not in the training set)",
    "richard_snowden": "ordinary source (historynorthand00snowgoog) not, but two other printings "
    "of the same History are (historynorthand01snowgoog 1806, historyofnorthso00snow_0 1811); "
    "no printing of the American Revolution is",
    "elias_smith": "ordinary volume in base training (lifecon00smit), with about ten other works "
    "of his; History of Anti-Christ (scripture voice) is not in the library",
}
BIAS = ("where the base model already read a text its loss there is already low, so a fine-tune "
        "has less to gain and every copy shares the memory: own-writer recognition is expected "
        "to be weaker, not stronger, on those chunks")  # fmt: skip
# Memory only, same numbers (``window_losses``'s own note): windows scored at a time. 64 windows
# of logits are about 4 GB, which after a fine-tune pushed a 16 GB Mac into swap (669 s a model).
SCORE_ROWS = 16
MICRO = 2  # sequences per micro-batch: memory only, the same update (8 ran out of memory)
BOM = "the Book of Mormon is not read, trained on or scored (lesson 11)"


# ------------------------------------------------------------------------------ the plan


def split(words: list[str], ids: list[int], offsets: list[tuple[int, int]], n: int,
          size: int) -> tuple[list[int], int, list[list[str]]]:  # fmt: skip
    """(training ids, words touched by them, held-out chunks). The first ``n`` token ids train;
    every word from the first one no training token touches is held out, cut into ``size``-word
    chunks (a last partial chunk dropped). ``offsets`` are the tokens' character spans in
    ``" ".join(words)``. Text shorter than ``n`` tokens gives no training ids."""
    if len(ids) < n:
        return [], 0, []
    end = offsets[n - 1][1]
    used = len(" ".join(words)[:end].split())
    return ids[:n], used, tv.chunks(words[used:], size)


def larger_sequences(
    heldout_words: dict[str, int],
    seq: int,
    most: int,
    small: int,
    need_chunks: int,
    size: int,
    tokens_per_word: dict[str, float],
) -> int:
    """The most sequences s (small < s <= ``most``) leaving at least ``need_chunks`` held-out
    chunks in every writer-voice: words left after s*seq tokens, at its tokens-per-word rate.
    0 when no dose above the small one fits."""
    for s in range(most, small, -1):
        if all(
            (w - math.ceil(s * seq / tokens_per_word[k])) // size >= need_chunks
            for k, w in heldout_words.items()
        ):
            return s
    return 0


def plan(cfg: dict) -> dict:
    """Per run: the dose in sequences and, per writer|voice, the training ids and held-out chunk
    ids (token ids only; licensed text in another form, so kept under ``WORK``)."""
    from tokenizers import Tokenizer

    from eval.library_pool import small_tokens
    from timelocked_lm.release import TOKENIZER

    t, ta, seq = cfg["lab"]["two_voices"], cfg["lab"]["two_voices_alm"], cfg["alm"]["seq"]
    tok = Tokenizer.from_file(str(TOKENIZER))
    vocab, grams = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    the_set, texts = tv.build_set(cfg, vocab)
    small_tok = small_tokens()
    small = small_tok // seq
    res: dict = {"small_dose": {"amendment45_tokens": small_tok, "sequences": small},
                 "set_not_attempted": the_set["not_attempted"], "runs": {}}  # fmt: skip
    for run, spec in ta["runs"].items():
        writers = [w for w in texts if w not in spec["drop"]]
        words, enc = {}, {}
        for w in writers:
            for v in tv.VOICES:
                ws = texts[w][v]
                if spec["kjv_dropped"]:
                    ws = tv.drop_kjv(ws, grams, t["kjv_ngram"])
                words[f"{w}|{v}"] = ws
                enc[f"{w}|{v}"] = tok.encode(" ".join(ws))
        if spec["dose"] == "small":
            s = small
        else:
            s = larger_sequences(
                {k: len(x) for k, x in words.items()}, seq,
                cfg["library_pool"]["large_sequences"], small, ta["larger_min_heldout_chunks"],
                t["chunk_words"], {k: len(enc[k].ids) / max(1, len(words[k])) for k in words},
            )  # fmt: skip
        units, short = {}, {}
        for k, ws in words.items():
            ids, used, held = split(ws, enc[k].ids, enc[k].offsets, s * seq, t["chunk_words"])
            if not ids or len(held) < ta["min_heldout_chunks"]:
                short[k] = {"words": len(ws), "tokens": len(enc[k].ids), "heldout": len(held)}
                continue
            units[k] = {"train": ids, "train_words": used, "words": len(ws),
                        "tokens": len(enc[k].ids),
                        "heldout": [tok.encode(" ".join(c)).ids for c in held]}  # fmt: skip
        res["runs"][run] = {"spec": spec, "sequences": s, "train_tokens": s * seq,
                            "units": units, "not_attempted": short}  # fmt: skip
    return res


def plan_summary(p: dict) -> dict:
    return {
        "small_dose": p["small_dose"],
        "runs": {
            r: {
                "sequences": x["sequences"],
                "train_tokens": x["train_tokens"],
                "spec": x["spec"],
                "not_attempted": x["not_attempted"],
                "units": {
                    k: {
                        "words": u["words"],
                        "tokens": u["tokens"],
                        "train_words": u["train_words"],
                        "heldout_chunks": len(u["heldout"]),
                    }
                    for k, u in x["units"].items()
                },
            }  # fmt: skip
            for r, x in p["runs"].items()
        },
    }


# ------------------------------------------------------------------------------ training


def _sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def free(dev: str) -> None:
    import gc

    import torch

    gc.collect()
    if dev == "mps":
        torch.mps.empty_cache()


def tests_of(units: dict) -> list[tuple[str, str, int, list[int]]]:
    """(writer, voice, chunk index, ids) of every held-out chunk, in a fixed order."""
    res = []
    for k in sorted(units):
        w, v = k.split("|")
        res += [(w, v, i, ids) for i, ids in enumerate(units[k]["heldout"])]
    return res


def train(cfg: dict, only: str | None, limit: int | None) -> int:
    import torch

    from alm.benchmark import _base, _device, finetune, window_losses

    a, ta = cfg["alm"], cfg["lab"]["two_voices_alm"]
    lr = cfg["timelocked_lm"]["finetune_lr"]
    p = plan(cfg)
    dev = _device()
    model = _base(ta["size"], cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    done, t0 = 0, time.time()
    for run, rp in p["runs"].items():
        if only and run != only:
            continue
        work = WORK / run
        out(work / "plan.json").write_text(json.dumps(plan_summary({"small_dose": p["small_dose"],
                                                    "runs": {run: rp}})["runs"][run]))  # fmt: skip
        tests = [x[3] for x in tests_of(rp["units"])]

        def score(tests=tests):
            got = window_losses(model, tests, a["score_window"], dev, rows=SCORE_ROWS)
            return np.array([np.mean(w) for w in got], dtype=np.float64)

        if not (work / "base.npy").exists():
            model.load_state_dict(state)
            np.save(out(work / "base.tmp.npy"), score())
            (work / "base.tmp.npy").replace(work / "base.npy")
        print(f"{run}: {rp['sequences']} sequences a model, {len(rp['units'])} models, "
              f"{len(tests)} held-out chunks", flush=True)  # fmt: skip
        # ordinary-voice models first (the card's order if time ran short)
        keys = sorted(rp["units"], key=lambda k: (k.split("|")[1] != "ordinary", k))
        for k in keys:
            name = k.replace("|", "__")
            if (work / f"{name}.json").exists():
                continue
            if limit is not None and done >= limit:
                print(f"stopped after {done} models (--limit)", flush=True)
                return 0
            t1 = time.time()
            model.load_state_dict(state)
            seed = config.derive_seed(f"{a['train_seed']}:{ta['seed']}:{run}:{k}", cfg)
            torch.manual_seed(seed)
            ids = np.array(rp["units"][k]["train"], dtype=np.int32)
            info = finetune(model, ids, cfg, seed, MICRO, dev, lr)
            free(dev)  # the optimizer's memory, before scoring (16 GB Mac: swap otherwise)
            wpath = work / f"{name}.pt"
            torch.save({x: v.cpu() for x, v in model.state_dict().items()},
                       out(work / f"{name}.pt.tmp"))  # fmt: skip
            (work / f"{name}.pt.tmp").replace(wpath)
            losses = score()
            np.save(out(work / f"{name}.tmp.npy"), losses)
            (work / f"{name}.tmp.npy").replace(work / f"{name}.npy")
            rec = {"train_tokens": len(ids), **info, "lr": lr, "seed": seed,
                   "weights_sha256": _sha(wpath),
                   "score_sec": round(time.time() - t1, 1)}  # fmt: skip
            out(work / f"{name}.json").write_text(json.dumps(rec))  # written last: the done mark
            done += 1
            print(f"  {run} {k}: {len(ids):,} tokens, {info['steps']} steps, "
                  f"{time.time() - t1:.0f} s (total {(time.time() - t0) / 60:.1f} min)",
                  flush=True)  # fmt: skip
    print(f"trained {done} models in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


# ------------------------------------------------------------------------------ analysis


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def attribute(S: np.ndarray, rows: list[int], cols: list[str], col_ix: dict[str, int]) -> list:
    """For each test row, the model (among ``cols``) with the lowest score, ties by name, and the
    rank of every model (1 = lowest)."""
    res = []
    for r in rows:
        sc = {c: S[r, col_ix[c]] for c in cols}
        order = sorted(cols, key=lambda c: (sc[c], c))
        res.append((order[0], {c: order.index(c) + 1 for c in cols}))
    return res


def attribution(S, meta, col_ix, writers, test_voice: str, model_voice: str) -> dict:
    """Per writer: own-writer rate (with a Wilson interval), mean own rank, where chunks went;
    and the pull of every model (share of the other writers' chunks drawn to it)."""
    cols = [f"{w}|{model_voice}" for w in writers]
    per, pull_n, pull_k = {}, dict.fromkeys(writers, 0), dict.fromkeys(writers, 0)
    for w in writers:
        rows = [i for i, m in enumerate(meta) if m[0] == w and m[1] == test_voice]
        got = attribute(S, rows, cols, col_ix)
        went: dict[str, int] = {}
        for best, _ in got:
            went[best.split("|")[0]] = went.get(best.split("|")[0], 0) + 1
        own = went.get(w, 0)
        per[w] = {"chunks": len(rows), "own": own,
                  "rate": round(own / len(rows), 3) if rows else None,
                  "rate_95": wilson(own, len(rows)),
                  "mean_own_rank": round(float(np.mean([r[f"{w}|{model_voice}"] for _, r in got])),
                                         3) if got else None,
                  "went_to": went}  # fmt: skip
        for o in writers:
            if o != w:
                pull_n[o] += len(rows)
                pull_k[o] += went.get(o, 0)
    rates = [p["rate"] for p in per.values() if p["rate"] is not None]
    return {
        "per_writer": per,
        "macro": round(sum(rates) / len(rates), 3) if rates else None,
        "chance": round(1 / len(writers), 3),
        "pull": {o: round(pull_k[o] / pull_n[o], 3) if pull_n[o] else None for o in writers},
    }


def place(js: float | None, rest: list[float], higher: str, lower: str) -> str:
    """The earlier cards' rule: typical if inside the others' range (ends included)."""
    if js is None or not rest:
        return "not attempted"
    if min(rest) <= js <= max(rest):
        return "typical"
    return higher if js > max(rest) else lower


def voice_or_person(S, meta, col_ix, writers) -> dict:
    """Per writer: share of held-out scripture-voice chunks scoring lower under another writer's
    scripture-voice model (the best one; the median of them) than under their own ordinary one."""
    per = {}
    for w in writers:
        rows = [i for i, m in enumerate(meta) if m[0] == w and m[1] == "prophetic"]
        others = [col_ix[f"{o}|prophetic"] for o in writers if o != w]
        own = S[rows, col_ix[f"{w}|ordinary"]]
        best = S[np.ix_(rows, others)].min(axis=1)
        med = np.median(S[np.ix_(rows, others)], axis=1)
        per[w] = {
            "chunks": len(rows),
            "any_other_beats_own_ordinary": round(float(np.mean(best < own)), 3),
            "typical_other_beats_own_ordinary": round(float(np.mean(med < own)), 3),
        }
    return per


def analyse(S: np.ndarray, meta: list, writers: list[str], cfg: dict) -> dict:
    """``S``: tests x models scores (lower = closer); ``meta``: (writer, voice, chunk) per row;
    model columns named ``writer|voice`` in ``col_ix`` order (``models_of``)."""
    t = cfg["lab"]["two_voices"]
    names = [f"{w}|{v}" for w in writers for v in tv.VOICES]
    col_ix = {n: i for i, n in enumerate(names)}
    ka = {v: attribution(S, meta, col_ix, writers, v, v) for v in tv.VOICES}
    res: dict = {
        "known_answer": {
            **ka,
            "bar": t["known_bar"],
            "passed": all((ka[v]["macro"] or 0) >= t["known_bar"] for v in tv.VOICES),
        }
    }
    if not res["known_answer"]["passed"]:
        res["stopped"] = "the within-voice check missed its bar; cross-voice not scored"
        return res
    cv = {
        "ordinary_models_on_scripture_chunks": attribution(S, meta, col_ix, writers,
                                                           "prophetic", "ordinary"),
        "scripture_models_on_ordinary_chunks": attribution(S, meta, col_ix, writers,
                                                           "ordinary", "prophetic"),
    }  # fmt: skip
    res["cross_voice"] = cv
    others = [w for w in writers if w != JS]
    crosses = {
        w: any((d["per_writer"][w]["rate"] or 0) >= t["cross_share"] for d in cv.values())
        for w in writers
    }
    n_cross = sum(crosses[w] for w in others)
    js: dict = {}
    if JS in writers and len(others) >= t["min_writers"]:
        for d, x in cv.items():
            pw = x["per_writer"]
            js[d] = {
                "rate": place(pw[JS]["rate"], [pw[o]["rate"] for o in others],
                              "above every other writer", "below every other writer"),
                "mean_own_rank": place(pw[JS]["mean_own_rank"],
                                       [pw[o]["mean_own_rank"] for o in others],
                                       "worse than every other writer",
                                       "better than every other writer"),
                "others_rate_range": [min(pw[o]["rate"] for o in others),
                                      max(pw[o]["rate"] for o in others)],
            }  # fmt: skip
    else:
        js = {"verdict": "cannot tell (group too small)" if JS in writers else "not in this run"}
    vp = voice_or_person(S, meta, col_ix, writers)
    res["voice_or_person"] = {"per_writer": vp, "macro_any_other": round(float(np.mean(
        [p["any_other_beats_own_ordinary"] for p in vp.values()])), 3),
        "macro_typical_other": round(float(np.mean(
            [p["typical_other_beats_own_ordinary"] for p in vp.values()])), 3)}  # fmt: skip
    if JS in writers and len(others) >= t["min_writers"]:
        res["voice_or_person"]["joseph_smith_place_any_other"] = place(
            vp[JS]["any_other_beats_own_ordinary"],
            [vp[o]["any_other_beats_own_ordinary"] for o in others],
            "above all",
            "below all",
        )
    res["verdicts"] = {"crosses": crosses, "others_crossing": n_cross, "others": len(others),
                       "genre_effect": n_cross < len(others) / 2, "joseph_smith": js}  # fmt: skip
    return res


def load_run(run: str, rp: dict) -> tuple[np.ndarray, list, list[str]]:
    """Scores (held-out chunks x models, model loss minus base), row meta, writers; ``OSError``
    when a model of the run has not been trained yet."""
    work = WORK / run
    writers = sorted({k.split("|")[0] for k in rp["units"]})
    meta = [(w, v, i) for w, v, i, _ in tests_of(rp["units"])]
    base = np.load(work / "base.npy")
    cols = []
    for w in writers:
        for v in tv.VOICES:
            f = work / f"{w}__{v}.npy"
            if not (work / f"{w}__{v}.json").exists():
                raise OSError(f"{f} missing: run train --run {run}")
            cols.append(np.load(f) - base)
    return np.stack(cols, axis=1), meta, writers


def run_all(cfg: dict) -> dict:
    from eval.library_pool import scaled

    p = plan(cfg)
    ta = cfg["lab"]["two_voices_alm"]
    a = cfg["alm"]
    res: dict = {
        "exploratory": True,
        "base_model": f"timelocked_lm {ta['size']} (data/corpus/timelocked_lm/runs/"
        f"{ta['size']}/model.pt)",
        "recipe": {"epochs": cfg["timelocked_lm"]["finetune_epochs"],
                   "lr": cfg["timelocked_lm"]["finetune_lr"], "seq": a["seq"],
                   "batch": a["batch"], "score_window": a["score_window"],
                   "adam_betas": cfg["timelocked_lm"]["adam_betas"],
                   "weight_decay": cfg["timelocked_lm"]["weight_decay"],
                   "grad_clip": cfg["timelocked_lm"]["grad_clip"], "precision": a["precision"],
                   "source": "alm.benchmark.finetune and window_losses, unchanged"},
        "settings": {**ta, "chunk_words": cfg["lab"]["two_voices"]["chunk_words"],
                     "known_bar": cfg["lab"]["two_voices"]["known_bar"],
                     "cross_share": cfg["lab"]["two_voices"]["cross_share"],
                     "min_writers": cfg["lab"]["two_voices"]["min_writers"]},
        "plan": plan_summary(p),
        "training_overlap": TRAINING_OVERLAP,
        "training_overlap_bias": BIAS,
        "book_of_mormon": BOM,
        "runs": {},
        "not_attempted": {},
    }  # fmt: skip
    for run, rp in p["runs"].items():
        try:
            S, meta, writers = load_run(run, rp)
        except OSError as e:
            res["not_attempted"][run] = str(e)
            continue
        info = {}
        for w in writers:
            for v in tv.VOICES:
                j = json.loads((WORK / run / f"{w}__{v}.json").read_text())
                info[f"{w}|{v}"] = {k: j[k] for k in ("train_tokens", "sequences", "steps",
                                                      "seed", "weights_sha256")}  # fmt: skip
        half = np.array([m[2] % 2 == 1 for m in meta])
        res["runs"][run] = {
            "models": info,
            "raw": analyse(S, meta, writers, cfg),
            "scaled": analyse(scaled(S, half), meta, writers, cfg),
            "mean_score_by_model": {
                f"{w}|{v}": round(float(S[:, i * 2 + j].mean()), 4)
                for i, w in enumerate(writers)
                for j, v in enumerate(tv.VOICES)
            },  # fmt: skip
        }
    res["side_by_side"] = side_by_side(res)
    return res


def side_by_side(res: dict) -> dict:
    """The three measures' headline numbers, read from the earlier results where present."""
    sb: dict = {}
    try:
        fw = json.loads(FW_RESULT.read_text())
        cv = fw["cross_voice"]["burrows"]
        sb["function_words"] = {
            "known_answer": {v: fw["known_answer"]["burrows"][v]["macro"] for v in tv.VOICES},
            "js_ordinary_to_scripture": cv["ordinary_to_prophetic"][JS]["rate"],
            "js_scripture_to_ordinary": cv["prophetic_to_ordinary"][JS]["rate"],
            "others_crossing": fw["verdicts"]["others_crossing"],
            "js_gap": fw["verdicts"]["joseph_smith_gap"],
        }
    except (OSError, KeyError) as e:
        sb["function_words"] = f"not attempted: {e}"
    try:
        enc = json.loads(ENC_RESULT.read_text())["encoders"]
        for name, r in enc.items():
            cv = r["cross_voice"]
            sb[f"encoder_{name}"] = {
                "known_answer": {v: r["known_answer"]["cosine"][v]["macro"] for v in tv.VOICES},
                "js_ordinary_to_scripture": cv["ordinary_to_prophetic"][JS]["rate"],
                "js_scripture_to_ordinary": cv["prophetic_to_ordinary"][JS]["rate"],
                "others_crossing": r["verdicts"]["others_crossing"],
                "js_gap": r["verdicts"]["joseph_smith_gap"],
            }
    except (OSError, KeyError) as e:
        sb["encoders"] = f"not attempted: {e}"
    for run, r in res["runs"].items():
        x = r["raw"]
        if "cross_voice" not in x:
            sb[f"author_models_{run}"] = {
                "known_answer": {v: x["known_answer"][v]["macro"] for v in tv.VOICES},
                "stopped": True,
            }
            continue
        cv = x["cross_voice"]
        pw_o = cv["ordinary_models_on_scripture_chunks"]["per_writer"]
        pw_s = cv["scripture_models_on_ordinary_chunks"]["per_writer"]
        sb[f"author_models_{run}"] = {
            "known_answer": {v: x["known_answer"][v]["macro"] for v in tv.VOICES},
            "js_ordinary_to_scripture": pw_o.get(JS, {}).get("rate"),
            "js_scripture_to_ordinary": pw_s.get(JS, {}).get("rate"),
            "others_crossing": x["verdicts"]["others_crossing"],
            "js": x["verdicts"]["joseph_smith"],
        }  # fmt: skip
    return sb


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "train", "run"])
    ap.add_argument("--run", help="train: one run of lab.two_voices_alm.runs")
    ap.add_argument("--limit", type=int, help="train: stop after this many new models")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plan":
        print(json.dumps(plan_summary(plan(cfg)), indent=1))
        return 0
    if a.cmd == "train":
        return train(cfg, a.run, a.limit)
    res = run_all(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT).write_text(json.dumps(res, indent=1) + "\n")
    for run, r in res["runs"].items():
        for kind in ("raw", "scaled"):
            x = r[kind]
            print(run, kind, {v: x["known_answer"][v]["macro"] for v in tv.VOICES},
                  x.get("verdicts", {}).get("others_crossing"),
                  x.get("verdicts", {}).get("joseph_smith"))  # fmt: skip
    print("not attempted:", res["not_attempted"] or "none")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
