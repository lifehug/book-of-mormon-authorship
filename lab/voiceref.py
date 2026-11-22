"""BOM-100: author models scored against a scripture-voice reference instead of the base model.

The study scores an author model on a text by its loss there minus the untuned base model's. On
scripture-voice text the base model is a poor reference, so "sounds like scripture" counts as a
gain. This tunes *voice-reference* models on scripture-voice text by other hands, at the same dose
as the author models, and asks on BOM-99's six writers (``lab.twovoices_alm``'s author models,
held-out chunks and doses, reused from disk) whether a writer's ordinary-prose model then finds
the same writer's scripture-voice chunks, at both doses and better than the base-referenced rule.

References: R_out (primary), one per dose, equal token shares from Bible-style books before 1827
by outside hands (``lab.voice_reference.outside_books``); R_loo (secondary), one per writer per
dose, the outside books plus the *other* writers' scripture-voice training slices, a chunk of
writer w scored against R_loo(-w). Scorings: raw loss, minus base, minus R_out, minus R_loo,
and R_out with a per-chunk z across candidates; unscaled (where a per-chunk reference cannot
change the lowest score: checked and recorded) and on the per-model scale
(``eval.library_pool.scaled``), which decides. Plus an open-set placebo. King James 5-grams are
dropped everywhere, as in the masked runs. The Book of Mormon is not read, trained on or scored
here: a second pass is allowed only if the result's verdict is "works".

Card, written first: ``data/private/lab/owner/2026-11-21-voice-reference/card.md``; settings
``lab.voice_reference``. Weights and losses in ``data/corpus/lab/voice_reference/`` (not git); the
result holds ids and numbers only.

Usage::

    python -m lab.voiceref plan                       # reference training shares (CPU, ~1 min)
    python -m lab.voiceref train [--run R] [--limit N]  # Mac GPU; resumes per model
    python -m lab.voiceref run    # -> data/lab/two_voices/result_voice_reference.json (seconds)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from lab import twovoices as tv
from lab import twovoices_alm as alm2
from lab.paths import FAST, out
from metadata import config

OUT = tv.OUT / "result_voice_reference.json"
WORK = FAST / "voice_reference"
ALM_WORK = alm2.WORK
BOM = ("the Book of Mormon is not read, trained on or scored by this run; a second pass is "
       "allowed only on the verdict 'works' (lesson 11)")  # fmt: skip
OUTSIDE = "out"


# ------------------------------------------------------------------------------ references


def shares(sources: list[list[int]], total: int) -> list[tuple[int, int]]:
    """Equal shares of ``total`` tokens from ``sources`` (the first ``total % k`` get one more),
    each taken from the middle of its source: (start, length) per source. ``ValueError`` if a
    source is shorter than its share."""
    k = len(sources)
    res = []
    for i, s in enumerate(sources):
        n = total // k + (1 if i < total % k else 0)
        if len(s) < n:
            raise ValueError(f"source {i} has {len(s)} tokens, needs {n}")
        res.append(((len(s) - n) // 2, n))
    return res


def take(sources: list[list[int]], total: int) -> list[int]:
    return [
        t for s, (a, n) in zip(sources, shares(sources, total), strict=True) for t in s[a : a + n]
    ]


def outside_ids(cfg: dict, tok, vocab: set[str], grams: set[str]) -> dict[str, list[int]]:
    """{book file name: token ids} of the outside books, King James 5-grams dropped."""
    vr, n = cfg["lab"]["voice_reference"], cfg["lab"]["two_voices"]["kjv_ngram"]
    res = {}
    for name in vr["outside_books"]:
        text, _ = tv.read_source(("file", str(Path(vr["outside_dir"]) / name)), cfg)
        words = tv.drop_kjv(tv.tokens(text, vocab)[0], grams, n)
        res[name] = tok.encode(" ".join(words)).ids
    return res


def reference_plan(cfg: dict, p: dict | None = None) -> dict:
    """Per run: the author-model plan (``lab.twovoices_alm.plan``) and the training ids of every
    reference: ``out`` and, if ``loo``, ``loo__<writer>``."""
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    vr, seq = cfg["lab"]["voice_reference"], cfg["alm"]["seq"]
    p = p or alm2.plan(cfg)
    tok = Tokenizer.from_file(str(TOKENIZER))
    vocab, grams = tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
    books = outside_ids(cfg, tok, vocab, grams)
    res: dict = {"outside_tokens": {b: len(x) for b, x in books.items()}, "runs": {}}
    for run in vr["runs"]:
        rp = p["runs"][run]
        total = rp["sequences"] * seq
        writers = sorted({k.split("|")[0] for k in rp["units"]})
        refs = {OUTSIDE: {"sources": list(books), "ids": take(list(books.values()), total)}}
        if vr["loo"]:
            for w in writers:
                others = [o for o in writers if o != w and f"{o}|prophetic" in rp["units"]]
                srcs = list(books.values()) + [rp["units"][f"{o}|prophetic"]["train"]
                                               for o in others]  # fmt: skip
                refs[f"loo__{w}"] = {"sources": list(books) + [f"{o}|prophetic train slice"
                                                               for o in others],
                                     "left_out": w, "ids": take(srcs, total)}  # fmt: skip
        res["runs"][run] = {"rp": rp, "writers": writers, "train_tokens": total, "refs": refs}
    return res


def plan_summary(rpl: dict) -> dict:
    return {
        "outside_tokens": rpl["outside_tokens"],
        "runs": {
            run: {
                "train_tokens": r["train_tokens"],
                "writers": r["writers"],
                "refs": {
                    k: {
                        "sources": v["sources"],
                        "tokens": len(v["ids"]),
                        **({"left_out": v["left_out"]} if "left_out" in v else {}),
                    }
                    for k, v in r["refs"].items()
                },  # fmt: skip
            }
            for run, r in rpl["runs"].items()
        },
    }


def train(cfg: dict, only: str | None, limit: int | None) -> int:
    import torch

    from alm.benchmark import _base, _device, finetune, window_losses

    a, vr, ta = cfg["alm"], cfg["lab"]["voice_reference"], cfg["lab"]["two_voices_alm"]
    lr = cfg["timelocked_lm"]["finetune_lr"]
    rpl = reference_plan(cfg)
    out(WORK / "plan.json").write_text(json.dumps(plan_summary(rpl), indent=1))
    dev = _device()
    model = _base(ta["size"], cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    done, t0 = 0, time.time()
    for run, r in rpl["runs"].items():
        if only and run != only:
            continue
        tests = [x[3] for x in alm2.tests_of(r["rp"]["units"])]
        n_base = len(np.load(ALM_WORK / run / "base.npy"))
        if n_base != len(tests):
            raise RuntimeError(f"{run}: {len(tests)} chunks planned, {n_base} in base.npy")
        work = WORK / run
        print(f"{run}: {len(r['refs'])} references, {r['train_tokens']} tokens each, "
              f"{len(tests)} chunks", flush=True)  # fmt: skip
        for name, ref in r["refs"].items():
            if (work / f"{name}.json").exists():
                continue
            if limit is not None and done >= limit:
                print(f"stopped after {done} models (--limit)", flush=True)
                return 0
            t1 = time.time()
            model.load_state_dict(state)
            seed = config.derive_seed(f"{a['train_seed']}:{vr['seed']}:{run}:{name}", cfg)
            torch.manual_seed(seed)
            ids = np.array(ref["ids"], dtype=np.int32)
            info = finetune(model, ids, cfg, seed, alm2.MICRO, dev, lr)
            alm2.free(dev)
            wpath = work / f"{name}.pt"
            torch.save({x: v.cpu() for x, v in model.state_dict().items()},
                       out(work / f"{name}.pt.tmp"))  # fmt: skip
            (work / f"{name}.pt.tmp").replace(wpath)
            got = window_losses(model, tests, a["score_window"], dev, rows=alm2.SCORE_ROWS)
            losses = np.array([np.mean(w) for w in got], dtype=np.float64)
            np.save(out(work / f"{name}.tmp.npy"), losses)
            (work / f"{name}.tmp.npy").replace(work / f"{name}.npy")
            rec = {"train_tokens": len(ids), **info, "lr": lr, "seed": seed,
                   "weights_sha256": alm2._sha(wpath), "sources": ref["sources"],
                   "score_sec": round(time.time() - t1, 1)}  # fmt: skip
            out(work / f"{name}.json").write_text(json.dumps(rec))  # written last: the done mark
            done += 1
            print(f"  {run} {name}: {len(ids):,} tokens, {info['steps']} steps, "
                  f"{time.time() - t1:.0f} s (total {(time.time() - t0) / 60:.1f} min)",
                  flush=True)  # fmt: skip
    print(f"trained {done} reference models in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


# ------------------------------------------------------------------------------ analysis


def predict(M: np.ndarray, rows: np.ndarray, cols: list[int]) -> np.ndarray:
    """Index into ``cols`` of the lowest score per row (ties: the first, i.e. by name)."""
    return np.argmin(M[np.ix_(rows, cols)], axis=1)


def chunk_z(X: np.ndarray) -> np.ndarray:
    """Each row z-scored across its columns."""
    sd = X.std(axis=1, keepdims=True)
    return (X - X.mean(axis=1, keepdims=True)) / np.where(sd > 0, sd, 1.0)


def weighted_quantile(values: list[np.ndarray], q: float) -> float:
    """The ``q`` quantile of the pooled values, each group weighted equally."""
    v = np.concatenate(values)
    w = np.concatenate([np.full(len(x), 1.0 / len(x)) for x in values])
    o = np.argsort(v)
    cum = np.cumsum(w[o]) / w.sum()
    return float(v[o][np.searchsorted(cum, q)])


def task(M, meta, writers, test_voice: str, model_voice: str, col_ix: dict,
         transform=None) -> dict:  # fmt: skip
    """Per writer: correct (bool per chunk) and the predicted writer, for ``test_voice`` chunks
    attributed among the ``model_voice`` models. ``transform`` (e.g. ``chunk_z``) applies to the
    candidate submatrix first."""
    cols = [col_ix[f"{w}|{model_voice}"] for w in writers]
    res = {}
    for w in writers:
        rows = np.array([i for i, m in enumerate(meta) if m[0] == w and m[1] == test_voice])
        if not len(rows):
            continue
        sub = M[np.ix_(rows, cols)]
        if transform is not None:
            sub = transform(sub)
        pred = np.argmin(sub, axis=1)
        res[w] = {"correct": pred == writers.index(w), "pred": [writers[j] for j in pred]}
    return res


def summarise(t: dict, writers: list[str]) -> dict:
    per = {w: round(float(x["correct"].mean()), 3) for w, x in t.items()}
    pull = {}
    for o in writers:
        n = sum(len(x["pred"]) for w, x in t.items() if w != o)
        k = sum(x["pred"].count(o) for w, x in t.items() if w != o)
        pull[o] = round(k / n, 3) if n else None
    tot = sum(len(x["correct"]) for x in t.values())
    return {
        "macro": round(float(np.mean(list(per.values()))), 3),
        "micro": round(sum(int(x["correct"].sum()) for x in t.values()) / tot, 3),
        "per_writer": per,
        "chunks": {w: len(x["correct"]) for w, x in t.items()},
        "pull": pull,
    }


def boot_macro(tasks: dict[str, dict], B: int, seed: int) -> dict[str, np.ndarray]:
    """``B`` macro accuracies per scoring, chunks resampled within writer, the same draws for
    every scoring (so differences are paired)."""
    rng = np.random.default_rng(seed)
    first = next(iter(tasks.values()))
    draws = {w: rng.integers(0, len(x["correct"]), size=(B, len(x["correct"])))
             for w, x in first.items()}  # fmt: skip
    return {
        name: np.mean([t[w]["correct"][draws[w]].mean(axis=1) for w in draws], axis=0)
        for name, t in tasks.items()
    }


def ci(x: np.ndarray, level: float) -> list[float]:
    a = (1 - level) / 2
    return [round(float(np.quantile(x, a)), 3), round(float(np.quantile(x, 1 - a)), 3)]


def placebo(M, meta, writers, col_ix, tar: float, transform=None) -> dict:
    """Open set, cross-voice: threshold = the ``tar`` quantile of true-writer scores (writers
    weighted equally, closed set); for each writer, the share of their scripture-voice chunks
    whose best score among the *other* writers' ordinary models is at or below it."""
    true, best = [], {}
    for w in writers:
        rows = np.array([i for i, m in enumerate(meta) if m[0] == w and m[1] == "prophetic"])
        cols = [col_ix[f"{o}|ordinary"] for o in writers]
        sub = M[np.ix_(rows, cols)]
        closed = transform(sub) if transform is not None else sub
        true.append(closed[:, writers.index(w)])
        rest = np.delete(sub, writers.index(w), axis=1)
        opened = transform(rest) if transform is not None else rest
        best[w] = opened.min(axis=1)
    tau = weighted_quantile(true, tar)
    per = {w: round(float(np.mean(b <= tau)), 3) for w, b in best.items()}
    return {"threshold": round(tau, 4), "confident_share": per,
            "macro": round(float(np.mean(list(per.values()))), 3)}  # fmt: skip


def scorings(L: np.ndarray, base: np.ndarray, ref_out: np.ndarray,
             ref_loo: np.ndarray | None) -> dict[str, np.ndarray]:  # fmt: skip
    """``L``: chunks x models (raw losses); references: one loss per chunk (R_loo: the chunk's
    own writer left out)."""
    s = {"raw": L, "base": L - base[:, None], "voice_out": L - ref_out[:, None]}
    if ref_loo is not None:
        s["voice_loo"] = L - ref_loo[:, None]
    return s


def analyse(L, base, ref_out, ref_loo, meta, writers, cfg) -> dict:
    """Every scoring's cross-voice and same-voice accuracy with intervals, the paired
    difference from the base-referenced rule, the placebo, and the unscaled-identity check."""
    from eval.library_pool import scaled

    vr = cfg["lab"]["voice_reference"]
    names = [f"{w}|{v}" for w in writers for v in tv.VOICES]
    col_ix = {n: i for i, n in enumerate(names)}
    half = np.array([m[2] % 2 == 1 for m in meta])
    raw = scorings(L, base, ref_out, ref_loo)
    mats: dict[str, tuple[np.ndarray, object]] = {}
    for k, M in raw.items():
        mats[f"{k}_unscaled"] = (M, None)
    mats["voice_out_chunkz_unscaled"] = (raw["voice_out"], chunk_z)
    for k, M in raw.items():
        mats[f"{k}_scaled"] = (scaled(M, half), None)
    mats["voice_out_chunkz_scaled"] = (mats["voice_out_scaled"][0], chunk_z)
    seed = config.derive_seed(f"{vr['seed']}:boot", cfg)
    res: dict = {"chance": round(1 / len(writers), 3), "scorings": {}}
    kinds = {
        "cross_voice": ("prophetic", "ordinary"),
        "same_voice_ordinary": ("ordinary", "ordinary"),
        "same_voice_scripture": ("prophetic", "prophetic"),
    }
    for kind, (tv_, mv) in kinds.items():
        tasks = {n: task(M, meta, writers, tv_, mv, col_ix, tr) for n, (M, tr) in mats.items()}
        boots = boot_macro(tasks, vr["resamples"], seed)
        for n, t in tasks.items():
            s = summarise(t, writers)
            s["macro_ci"] = ci(boots[n], vr["interval"])
            if n.endswith("_scaled") and n != "base_scaled":
                s["minus_base_scaled"] = round(s["macro"] - float(np.mean(
                    [tasks["base_scaled"][w]["correct"].mean() for w in t])), 3)  # fmt: skip
                s["minus_base_scaled_ci"] = ci(boots[n] - boots["base_scaled"], vr["interval"])
            res["scorings"].setdefault(n, {})[kind] = s
        unscaled = [n for n in tasks if n.endswith("_unscaled")]
        res.setdefault("unscaled_identical", {})[kind] = all(
            all(tasks[n][w]["pred"] == tasks[unscaled[0]][w]["pred"] for w in tasks[n])
            for n in unscaled
        )
    for n, (M, tr) in mats.items():
        if n.endswith("_scaled"):
            res["scorings"][n]["placebo"] = placebo(M, meta, writers, col_ix, vr["tar"], tr)
    return res


def judge(r: dict, cfg: dict) -> dict:
    """W1-W3 for one run, on scaled R_out against scaled base."""
    tol = cfg["lab"]["voice_reference"]["same_voice_tolerance"]
    v = r["scorings"]["voice_out_scaled"]
    b = r["scorings"]["base_scaled"]
    return {
        "W1_above_chance": v["cross_voice"]["macro_ci"][0] > r["chance"],
        "W2_above_base": v["cross_voice"]["minus_base_scaled_ci"][0] > 0,
        "W3_same_voice_kept": v["same_voice_ordinary"]["macro"]
        >= b["same_voice_ordinary"]["macro"] - tol,
    }


def verdict(per_run: dict[str, dict]) -> str:
    if len(per_run) < 2:
        return "cannot tell (a dose is not attempted)"
    if all(all(j.values()) for j in per_run.values()):
        return "works"
    if any(j["W1_above_chance"] and j["W2_above_base"] for j in per_run.values()):
        return "does not work reliably"
    return "does not work"


def load_run(run: str, rp: dict, loo: bool):
    """(L, base, ref_out, ref_loo, meta, writers); ``OSError`` when a file is missing."""
    writers = sorted({k.split("|")[0] for k in rp["units"]})
    meta = [(w, v, i) for w, v, i, _ in alm2.tests_of(rp["units"])]
    base = np.load(ALM_WORK / run / "base.npy")
    cols = []
    for w in writers:
        for v in tv.VOICES:
            if not (ALM_WORK / run / f"{w}__{v}.json").exists():
                raise OSError(f"author model {run}/{w}__{v} not trained")
            cols.append(np.load(ALM_WORK / run / f"{w}__{v}.npy"))
    if not (WORK / run / f"{OUTSIDE}.json").exists():
        raise OSError(f"reference {run}/{OUTSIDE} not trained: run train --run {run}")
    ref_out = np.load(WORK / run / f"{OUTSIDE}.npy")
    ref_loo = None
    if loo:
        per = {}
        for w in writers:
            if not (WORK / run / f"loo__{w}.json").exists():
                raise OSError(f"reference {run}/loo__{w} not trained: run train --run {run}")
            per[w] = np.load(WORK / run / f"loo__{w}.npy")
        ref_loo = np.array([per[m[0]][i] for i, m in enumerate(meta)])
    return np.stack(cols, axis=1), base, ref_out, ref_loo, meta, writers


def run_all(cfg: dict) -> dict:
    vr = cfg["lab"]["voice_reference"]
    p = alm2.plan(cfg)
    res: dict = {
        "exploratory": True,
        "base_model": f"timelocked_lm {cfg['lab']['two_voices_alm']['size']} (125M)",
        "author_models": "lab.twovoices_alm runs, losses reused from data/corpus/lab/"
                         "two_voices_alm/ (not retrained)",
        "settings": vr,
        "book_of_mormon": BOM,
        "runs": {},
        "not_attempted": {},
    }  # fmt: skip
    judged = {}
    for run in vr["runs"]:
        rp = p["runs"][run]
        try:
            L, base, ref_out, ref_loo, meta, writers = load_run(run, rp, vr["loo"])
        except OSError as e:
            res["not_attempted"][run] = str(e)
            continue
        refs = {}
        for f in sorted((WORK / run).glob("*.json")):
            j = json.loads(f.read_text())
            refs[f.stem] = {k: j[k] for k in ("train_tokens", "sequences", "steps", "seed",
                                              "weights_sha256", "sources")}  # fmt: skip
        r = analyse(L, base, ref_out, ref_loo, meta, writers, cfg)
        r.update({"sequences": rp["sequences"], "writers": writers, "references": refs,
                  "mean_loss": {"base": round(float(base.mean()), 4),
                                "voice_out": round(float(ref_out.mean()), 4)}})  # fmt: skip
        r["criteria"] = judged[run] = judge(r, cfg)
        res["runs"][run] = r
    res["verdict"] = verdict(judged)
    return res


def table(res: dict) -> str:
    lines = []
    for run, r in res["runs"].items():
        lines.append(f"{run} (chance {r['chance']}):")
        for n, s in r["scorings"].items():
            cv, so = s["cross_voice"], s["same_voice_ordinary"]
            lines.append(f"  {n:28s} cross {cv['macro']:.3f} {cv['macro_ci']}  same-ord "
                         f"{so['macro']:.3f} {so['macro_ci']}  placebo "
                         f"{s.get('placebo', {}).get('macro', '-')}")  # fmt: skip
        lines.append(f"  unscaled identical: {r['unscaled_identical']}; {r['criteria']}")
    lines.append(f"verdict: {res['verdict']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "train", "run"])
    ap.add_argument("--run", help="train: one run of lab.voice_reference.runs")
    ap.add_argument("--limit", type=int, help="train: stop after this many new models")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plan":
        print(json.dumps(plan_summary(reference_plan(cfg)), indent=1))
        return 0
    if a.cmd == "train":
        return train(cfg, a.run, a.limit)
    res = run_all(cfg)
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    out(OUT).write_text(json.dumps(res, indent=1) + "\n")
    print(table(res))
    print("not attempted:", res["not_attempted"] or "none")
    print("->", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
