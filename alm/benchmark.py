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

    python -m alm.benchmark pilot|base [--variant v1]   # -> data/benchmark/alm_<size>[_v1].json
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


def texts() -> dict[str, dict]:
    """{task: {"works": {author: [word lists]}, "tests": {work_id: words} (dictated only)}}."""
    from segment.build import original_words

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
    return {"federalist": {"works": fed}, "pseudo_biblical": {"works": pb},
            "dictated": {"works": dic, "tests": {w: got[w] for w in d["tests"]},
                         "author": d["author"]}}  # fmt: skip


def plan(cfg: dict) -> dict[str, dict]:
    """Per task: each author's training words (works kept apart) and the test samples."""
    bm, a = cfg["benchmark"], cfg["alm"]
    k = bm["test_words"] // BLOCK
    out: dict[str, dict] = {}
    for task, t in texts().items():
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
    m = GPT(t["vocab_size"], t["context_length"], sh["layers"], sh["width"], sh["heads"])
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


def run(size: str, micro: int, variant: str = "") -> int:
    """Amendment 22's ALMs; ``variant`` "v1" is Amendment 23's V1 (learning rate
    ``alm.v1_finetune_lr``)."""
    from tokenizers import Tokenizer

    cfg = load_config()
    a = cfg["alm"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    lr = a["v1_finetune_lr"] if variant == "v1" else cfg["timelocked_lm"]["finetune_lr"]
    tag = f"{size}_{variant}" if variant else size
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)
    p = plan(cfg)
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
            path.write_text(json.dumps({"train_tokens": len(ids), **info, "losses": losses}))
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
    rate = bm["max_open_set_fpr"]
    pos = [r["positive"] for r in allrecs]
    neg = [r["open_negative"] for r in allrecs]
    th = calibrate_gi(pos, neg, rate)
    idx = list(range(len(neg)))
    random.Random(derive_seed(a["fold_seed"], cfg)).shuffle(idx)
    half = len(idx) // 2
    fprs = []
    for cal, ev in ((idx[:half], idx[half:]), (idx[half:], idx[:half])):
        t = np.quantile([neg[i] for i in cal], 1 - rate)
        fprs.append(float(np.mean([neg[i] > t for i in ev])))
    fpr = float(np.mean(fprs))
    verdict = {"closed_set": overall, "open_set_fpr": fpr,
               "passes": overall >= bm["pass_closed_set"] and fpr <= rate}  # fmt: skip
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
    ap.add_argument("size", choices=["pilot", "base"])
    ap.add_argument("--variant", choices=["v1"], default="", help="Amendment 23's V1")
    ap.add_argument("--micro-batch", type=int, default=2, help="memory only; same update")
    a = ap.parse_args(argv)
    return run(a.size, a.micro_batch, a.variant)


if __name__ == "__main__":
    sys.exit(main())
