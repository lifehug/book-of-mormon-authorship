"""Authorial language models on the validation benchmark (BOM-28; pre-registration 5.2,
Amendment 22, ``docs/alm-plan.md``).

One copy of the time-locked base model (BOM-27) is fine-tuned per benchmark author and scored on
the benchmark's three tasks. A test sample's score for a candidate is the mean, over fixed
``alm.score_window``-token windows, of the candidate model's mean token log-loss minus the base
model's (the log-perplexity ratio). Closed set: the lowest score. Verification: minus the score;
the threshold and open-set false-positive rate are General Imposters' (6.1). Passes as 7.

The texts are the benchmark's works as original words (King James spans masked where the benchmark
masks them). Federalist and imitation-scripture authors are tested on a held-out tail of their own
text; the dictated task tests Scott's dictated volumes. Fine-tuned weights are not kept: each
author's model scores every test of its task as soon as it is trained, and the scores are saved
per author, so a rerun resumes at the next author.

Usage::

    python -m alm.benchmark <size> [--variant v1]   # size pilot|base|mid|large -> alm_<size>[_v1]
    python -m alm.benchmark <size> --variant v1 --lr 3e-5 --tag <size>_v1_lrsel --save-weights
    python -m alm.benchmark <size> --part2          # BOM-75: all seven tasks -> alm_<size>_p2
    python -m alm.benchmark bundle --ext            # Amendment 56: new tasks packed
    python -m alm.benchmark <size> --ext            # Amendment 56 -> alm_<size>_p3
    python -m alm.benchmark bundle --pool           # Amendment 58: the 55 tested authors packed
    python -m alm.benchmark <size> --pool           # Amendment 58 -> alm_<size>_pool

``--save-weights`` keeps every fine-tuned copy (``<work>/weights/<task>__<author>.pt``) for
publication (owner, 2026-11-09: no trained model is discarded).
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch
import torch.nn.functional as F

from eval.benchmark import TASKS, calibrate_gi
from eval.power import BLOCK, FEDERALIST, PSEUDO, SPANS
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config
from timelocked_lm.release import EOT, RUNS, TOKENIZER
from timelocked_lm.train import GPT

OUT = Path("data/benchmark")
WORK = Path("data/corpus/alm/benchmark")


def _device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    return "mps" if torch.backends.mps.is_available() else "cpu"


def _words(work_ids: list[str], spans_files: list[Path]) -> dict[str, list[str]]:
    """Original words of each work, King James spans masked where a mask exists."""
    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    want = set(work_ids)
    spans: dict[str, list] = {}
    for path in spans_files:
        if not path.exists():
            path = path.with_suffix(".jsonl.gz")
        text = gzip.open(path, "rt").read() if path.suffix == ".gz" else path.read_text()
        for ln in text.splitlines():
            r = json.loads(ln)
            if r["id"] in want:
                spans[r["id"]] = r["spans"]
    cols = ["work_id", "source", "text_path"]
    rows = {r["work_id"]: r for r in pq.read_table("data/catalog/catalog.parquet", columns=cols)
            .to_pylist() if r["work_id"] in want}  # fmt: skip
    return {w: original_words(norm_path(rows[w]).read_text(encoding="utf-8", errors="replace"),
                              spans.get(w, [])) for w in work_ids}  # fmt: skip


def texts(part2: bool = False, ext: bool = False) -> dict[str, dict]:
    """{task: {"works": {author: [word lists]}, "tests": {work_id: words} (dictated only)}};
    ``part2`` adds Amendment 48's four corpus-author tasks (``eval.part2_benchmark``); ``ext`` gives
    only Amendment 56's eight new tasks."""
    from segment.build import original_words

    if ext:
        from eval.part2_benchmark import corpus_works

        return {t: {"works": by} for t, by in corpus_works(load_config(), ext=True).items()}

    fed: dict[str, list[list[str]]] = {}
    for ln in FEDERALIST.read_text().splitlines():
        r = json.loads(ln)
        fed.setdefault(r["author"], []).append(original_words(r["text"], []))
    spec = json.loads(PSEUDO.read_text())["authors"]
    ids = [w for a in spec.values() for w in a["works"]]
    got = _words(ids, [SPANS])
    pb = {a: [got[w] for w in s["works"]] for a, s in spec.items()}
    d = json.loads(TASKS.read_text())["dictated"]
    ref_ids = [w for ws in d["reference"].values() for w in ws]
    masks = [Path("data/kjv_mask/controls/spans.jsonl"),
             Path("data/kjv_mask/known_answer/spans.jsonl")]  # fmt: skip
    got = _words(ref_ids + d["tests"], masks)
    dic = {a: [got[w] for w in ws] for a, ws in d["reference"].items()}
    out = {"federalist": {"works": fed}, "pseudo_biblical": {"works": pb},
           "dictated": {"works": dic, "tests": {w: got[w] for w in d["tests"]},
                        "author": d["author"]}}  # fmt: skip
    if part2:
        from eval.part2_benchmark import corpus_works

        out.update({t: {"works": by} for t, by in corpus_works(load_config()).items()})
    return out


BUNDLE = WORK / "p3_plan.json.gz"  # Amendment 56's plan as words (licensed text: never in git)


def plan(cfg: dict, part2: bool = False, ext: bool = False) -> dict[str, dict]:
    """Per task: each author's training words (works kept apart) and the test samples. With
    ``ext`` and no corpus at hand (a rented GPU), the plan is read from ``BUNDLE``."""
    if ext and BUNDLE.exists() and not Path("data/corpus/internet_archive").exists():
        with gzip.open(BUNDLE, "rt") as fh:
            return json.load(fh)
    bm, a = cfg["benchmark"], cfg["alm"]
    k = bm["test_words"] // BLOCK
    out: dict[str, dict] = {}
    for task, t in texts(part2, ext).items():
        train, tests = {}, []
        for author, works in sorted(t["works"].items()):
            if task == "dictated":
                train[author] = works
                continue
            flat = [w for ws in works for w in ws]
            n = len(flat) // BLOCK
            if n < k + bm["min_reference_blocks"]:
                train[author] = works  # too short to test; still a candidate
                continue
            h = max(k, math.ceil(n * a["holdout_share"]))
            cut = (n - h) * BLOCK
            kept, used = [], 0
            for ws in works:  # the first ``cut`` words, work boundaries kept
                if used >= cut:
                    break
                kept.append(ws[: cut - used])
                used += len(kept[-1])
            train[author] = kept
            starts = list(range(n - h, n - k + 1))
            if len(starts) > a["max_tests"]:
                rng = random.Random(derive_seed(f"{a['test_seed']}:{task}:{author}", cfg))
                starts = sorted(rng.sample(starts, a["max_tests"]))
            tests += [{"author": author, "words": flat[s * BLOCK : (s + k) * BLOCK],
                       "where": f"blocks {s}-{s + k - 1} of {n}"} for s in starts]  # fmt: skip
        if task == "dictated":
            rng = random.Random(derive_seed(f"{a['test_seed']}:dictated", cfg))
            for w, words in t["tests"].items():
                nb = len(words) // BLOCK
                for _ in range(bm["trials"]):
                    s = rng.randrange(nb - k + 1)
                    sample = words[s * BLOCK : (s + k) * BLOCK]
                    tests.append({"author": t["author"], "words": sample,
                                  "where": f"{w} blocks {s}-{s + k - 1}"})  # fmt: skip
        out[task] = {"train": train, "tests": tests}
    return out


def _encode(tok, words: list[str]) -> list[int]:
    return tok.encode(" ".join(words)).ids


def _base(size: str, cfg: dict) -> GPT:
    t = cfg["timelocked_lm"]
    sh = t[f"{size}_shape"]
    m = GPT(t["vocab_size"], t["context_length"], sh["layers"], sh["width"], sh["heads"],
            sh.get("qk_norm", False))  # fmt: skip
    m.load_state_dict(torch.load(RUNS / size / "model.pt", map_location="cpu"))
    return m


def finetune(model: GPT, ids: np.ndarray, cfg: dict, seed: int, micro: int, dev: str,
             lr: float) -> dict:  # fmt: skip
    """3 epochs over non-overlapping ``alm.seq``-token sequences, batches of ``alm.batch``
    (accumulated from micro-batches of ``micro``; the same update)."""
    a, t = cfg["alm"], cfg["timelocked_lm"]
    seqs = torch.from_numpy(ids[: len(ids) // a["seq"] * a["seq"]].reshape(-1, a["seq"]))
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=tuple(t["adam_betas"]),
                            weight_decay=t["weight_decay"])  # fmt: skip
    rng = np.random.default_rng(seed)
    model.train()
    steps, t0 = 0, time.time()
    for _ in range(t["finetune_epochs"]):
        order = rng.permutation(len(seqs))
        for i in range(0, len(order), a["batch"]):
            batch = order[i : i + a["batch"]]
            for j in range(0, len(batch), micro):
                xy = seqs[batch[j : j + micro]].long().to(dev)
                loss = model(xy[:, :-1], xy[:, 1:]) * (len(batch[j : j + micro]) / len(batch))
                loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), t["grad_clip"])
            opt.step()
            opt.zero_grad(set_to_none=True)
            steps += 1
    model.eval()
    return {"sequences": len(seqs), "steps": steps, "sec": round(time.time() - t0, 1)}


@torch.no_grad()
def window_loss(model: GPT, ids: list[int], window: int, dev: str) -> list[float]:
    """Mean token log-loss of each non-overlapping ``window``-token window; a last partial
    window is dropped."""
    n = len(ids) // window
    x = torch.tensor(ids[: n * window], dtype=torch.long, device=dev).view(n, window)
    logits = model(x[:, :-1])
    nll = F.cross_entropy(logits.flatten(0, 1).float(), x[:, 1:].flatten(), reduction="none")
    return nll.view(n, window - 1).mean(dim=1).tolist()


@torch.no_grad()
def window_losses(model: GPT, tests: list[list[int]], window: int, dev: str,
                  rows: int = 64) -> list[list[float]]:  # fmt: skip
    """``window_loss`` for many tests, their windows run ``rows`` at a time (same numbers, the
    GPU kept busy)."""
    wins, owner = [], []
    for k, ids in enumerate(tests):
        n = len(ids) // window
        wins += [ids[i * window : (i + 1) * window] for i in range(n)]
        owner += [k] * n
    out: list[list[float]] = [[] for _ in tests]
    for s in range(0, len(wins), rows):
        x = torch.tensor(wins[s : s + rows], dtype=torch.long, device=dev)
        logits = model(x[:, :-1])
        nll = F.cross_entropy(logits.flatten(0, 1).float(), x[:, 1:].flatten(), reduction="none")
        for k, v in zip(owner[s : s + rows], nll.view(len(x), window - 1).mean(dim=1).tolist(),
                        strict=True):  # fmt: skip
            out[k].append(v)
    return out


POOL_BUNDLE = WORK / "pool_plan.json.gz"  # Amendment 58 (licensed text: never in git)


def pool_plan(cfg: dict) -> dict:
    """Amendment 58: the 55 tested authors' training words (with their registered task, which
    fixes their seed) and all 1,070 tests in benchmark order."""
    if POOL_BUNDLE.exists() and not Path("data/corpus/internet_archive").exists():
        with gzip.open(POOL_BUNDLE, "rt") as fh:
            return json.load(fh)
    from eval.list_size import merged_plan, tested_authors

    p = merged_plan(cfg)
    who = tested_authors(p)
    return {"train": {a: {"task": t, "works": p[t]["train"][a]} for a, t in sorted(who.items())},
            "tests": [{**x, "task": t} for t, tp in p.items() for x in tp["tests"]]}  # fmt: skip


def run_pool(size: str, micro: int) -> int:
    """Amendment 58: every tested author's model, trained as registered, scores every test."""
    from tokenizers import Tokenizer

    cfg = load_config()
    a = cfg["alm"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    lr = cfg["timelocked_lm"]["finetune_lr"]
    work = WORK / f"{size}_pool"
    work.mkdir(parents=True, exist_ok=True)
    p = pool_plan(cfg)
    tests = p["tests"]
    for x in tests:
        x["ids"] = _encode(tok, x["words"])
    base = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}
    bpath = work / "base.json"
    if not bpath.exists():
        bpath.write_text(json.dumps(window_losses(base, [x["ids"] for x in tests],
                                                  a["score_window"], dev)))  # fmt: skip
    print(f"pool: {len(p['train'])} authors, {len(tests)} tests", flush=True)
    for author, info in p["train"].items():
        path = work / f"{author.replace('/', '_')}.json"
        if path.exists():
            continue
        ids = np.array([i for ws in info["works"] for i in [*_encode(tok, ws), eot]],
                       dtype=np.int32)  # fmt: skip
        base.load_state_dict(state)
        seed = derive_seed(f"{a['train_seed']}:{info['task']}:{author}", cfg)  # as registered
        torch.manual_seed(seed)
        t0 = time.time()
        info_t = finetune(base, ids, cfg, seed, micro, dev, lr)
        losses = window_losses(base, [x["ids"] for x in tests], a["score_window"], dev)
        path.write_text(json.dumps({"train_tokens": len(ids), **info_t, "lr": lr, "seed": seed,
                                    "losses": losses}))  # fmt: skip
        print(f"  {size} pool {author}: {len(ids):,} tokens, {info_t['steps']} steps, "
              f"{(time.time() - t0) / 60:.1f} min", flush=True)  # fmt: skip
    bl = json.loads(bpath.read_text())
    got = {b: json.loads((work / f"{b.replace('/', '_')}.json").read_text())["losses"]
           for b in p["train"]}  # fmt: skip
    recs = [{"author": x["author"], "task": x["task"], "where": x["where"],
             "scores": {b: float(np.mean(np.array(g[i]) - np.array(bl[i])))
                        for b, g in got.items()}}
            for i, x in enumerate(tests)]  # fmt: skip
    out = OUT / f"alm_{size}_pool.json"
    out.write_text(json.dumps({**stamp(), "run": f"{size}_pool", "authors": len(got),
                               "tests": len(recs), "records": recs}, indent=1) + "\n")  # fmt: skip
    print(f"{len(recs)} tests x {len(got)} authors -> {out}", flush=True)
    return 0


def run(size: str, micro: int, variant: str = "", lr: float | None = None,
        tag: str | None = None, save: bool = False, part2: bool = False,
        ext: bool = False) -> int:  # fmt: skip
    """Amendment 22's ALMs; ``variant`` "v1" is Amendment 23's V1 (learning rate
    ``alm.v1_finetune_lr``), or ``lr`` where given (Amendment 41's selected rate)."""
    from tokenizers import Tokenizer

    cfg = load_config()
    a = cfg["alm"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    if lr is None:
        lr = a["v1_finetune_lr"] if variant == "v1" else cfg["timelocked_lm"]["finetune_lr"]
    tag = tag or (f"{size}_{variant}" if variant else size) + (
        "_p3" if ext else "_p2" if part2 else ""
    )
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)
    p = plan(cfg, part2, ext)
    base = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}
    for task, tp in p.items():
        for x in tp["tests"]:
            x["ids"] = _encode(tok, x["words"])
        path = work / f"{task}__base.json"
        if not path.exists():
            path.write_text(json.dumps([window_loss(base, x["ids"], a["score_window"], dev)
                                        for x in tp["tests"]]))  # fmt: skip
        print(f"{task}: {len(tp['train'])} authors, {len(tp['tests'])} tests", flush=True)
    for task, tp in p.items():
        for author, works in tp["train"].items():
            path = work / f"{task}__{author}.json"
            if path.exists():
                continue
            ids = np.array([i for ws in works for i in [*_encode(tok, ws), eot]], dtype=np.int32)
            base.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:{task}:{author}", cfg)
            torch.manual_seed(seed)
            info = finetune(base, ids, cfg, seed, micro, dev, lr)
            losses = [window_loss(base, x["ids"], a["score_window"], dev) for x in tp["tests"]]
            if save:
                (work / "weights").mkdir(exist_ok=True)
                torch.save(base.state_dict(), work / "weights" / f"{task}__{author}.pt")
            path.write_text(json.dumps({"train_tokens": len(ids), **info, "lr": lr,
                                        "seed": seed, "losses": losses}))  # fmt: skip
            print(f"  {tag} {task} {author}: {len(ids):,} tokens, {info['steps']} steps, "
                  f"{info['sec'] / 60:.1f} min", flush=True)  # fmt: skip
    return score(tag, p, cfg)


def score(tag: str, p: dict, cfg: dict) -> int:
    work = WORK / tag
    recs_by, training = {}, {}
    for task, tp in p.items():
        base = json.loads((work / f"{task}__base.json").read_text())
        got = {b: json.loads((work / f"{task}__{b}.json").read_text()) for b in tp["train"]}
        training[task] = {b: {k: v for k, v in g.items() if k != "losses"} for b, g in got.items()}
        recs = []
        for i, x in enumerate(tp["tests"]):
            r = {b: float(np.mean(np.array(g["losses"][i]) - np.array(base[i])))
                 for b, g in got.items()}  # fmt: skip
            others = [b for b in r if b != x["author"]]
            recs.append({"author": x["author"], "where": x["where"], "windows": len(base[i]),
                         "scores": r, "predicted": min(r, key=lambda b: (r[b], b)),
                         "positive": -r[x["author"]],
                         "open_negative": max(-r[b] for b in others)})  # fmt: skip
        recs_by[task] = recs
    return write(tag, recs_by, cfg, {"training": training})


def decide(recs_by: dict[str, list[dict]], cfg: dict) -> dict:
    """Closed-set accuracy, General Imposters' threshold and held-out open-set FPR, verdict."""
    a, bm = cfg["alm"], cfg["benchmark"]
    allrecs = [r for rs in recs_by.values() for r in rs]
    closed = {t: sum(r["predicted"] == r["author"] for r in rs) / len(rs)
              for t, rs in recs_by.items()}  # fmt: skip
    overall = sum(r["predicted"] == r["author"] for r in allrecs) / len(allrecs)
    from eval.open_set import verdict as open_set_verdict

    pos = [r["positive"] for r in allrecs]
    neg = [r["open_negative"] for r in allrecs]
    th = calibrate_gi(pos, neg, bm["max_open_set_fpr"])
    # Amendment 25 (post hoc): threshold from the positives; the original rate reported beside
    verdict = open_set_verdict(overall, pos, neg, cfg, derive_seed(a["fold_seed"], cfg))
    return {"closed_set_by_task": closed, "verdict": verdict, "thresholds": th}


def write(tag: str, recs_by: dict[str, list[dict]], cfg: dict, extra: dict) -> int:
    d = decide(recs_by, cfg)
    out = OUT / f"alm_{tag}.json"
    out.write_text(json.dumps({**stamp(), "run": tag, **d, **extra, "records": recs_by},
                              indent=1) + "\n")  # fmt: skip
    v = d["verdict"]
    print(f"{tag}: closed set {v['closed_set']:.3f} {d['closed_set_by_task']}; open-set FPR "
          f"{v['open_set_fpr']:.3f}; passes {v['passes']} -> {out}", flush=True)  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("size", choices=["pilot", "base", "mid", "large", "bundle"])
    ap.add_argument("--variant", choices=["v1"], default="", help="Amendment 23's V1")
    ap.add_argument("--micro-batch", type=int, default=2, help="memory only; same update")
    ap.add_argument("--lr", type=float, help="Amendment 41: a selected learning rate")
    ap.add_argument("--tag", help="result name (alm_<tag>.json); default <size>[_<variant>]")
    ap.add_argument("--save-weights", action="store_true", help="keep every fine-tuned copy")
    ap.add_argument("--part2", action="store_true", help="Amendment 48: add the four corpus tasks")
    ap.add_argument("--ext", action="store_true", help="Amendment 56: only the eight new tasks")
    ap.add_argument("--pool", action="store_true", help="Amendment 58: 55 authors x 1,070 tests")
    a = ap.parse_args(argv)
    if a.pool:
        if a.size != "bundle":
            return run_pool(a.size, a.micro_batch)
        pp = pool_plan(load_config())
        POOL_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(POOL_BUNDLE, "wt") as fh:
            json.dump(pp, fh)
        print(f"{len(pp['train'])} authors, {len(pp['tests'])} tests -> {POOL_BUNDLE} "
              f"({POOL_BUNDLE.stat().st_size / 1e6:.1f} MB)")  # fmt: skip
        return 0
    if a.size == "bundle":
        p = plan(load_config(), ext=True)
        BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(BUNDLE, "wt") as fh:
            json.dump(p, fh)
        print(f"{len(p)} tasks, {sum(len(t['tests']) for t in p.values())} tests -> {BUNDLE} "
              f"({BUNDLE.stat().st_size / 1e6:.1f} MB)")  # fmt: skip
        return 0
    return run(a.size, a.micro_batch, a.variant, a.lr, a.tag, a.save_weights, a.part2, a.ext)


if __name__ == "__main__":
    sys.exit(main())
