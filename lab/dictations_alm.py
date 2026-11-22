"""BOM-104: the author-model measure for ``lab.dictations`` (125M, Mac GPU).

One copy of the 125M time-locked base model per candidate (Smith, Rigdon, Cowdery, Phelps, Pratt),
fine-tuned on the first tokens of that candidate's masked stream at two equal doses (``lab.
dictations.doses``: 2 and 8 sequences of ``alm.seq`` tokens, the doses of ``lab.twovoices_alm``),
with the recipe unchanged (``alm.benchmark.finetune``). Every other unit of the run (held-out
candidate chunks, lecture pieces and whole lectures, the dictated texts' chunks, the Book of
Mormon's chunks) is scored by every model and the base model (``alm.benchmark.window_losses``;
score = model loss minus base loss, lower = closer). The Book of Mormon is scored only: it is never
trained or tuned on. Joseph Smith's models are the two-voices run's cached ones
(``data/corpus/lab/two_voices_alm/masked_{small,larger}/joseph_smith__ordinary.pt``) when the dose
matches, since his stream and slice are built by the same code. The 125M models were unstable
across dose in the two-voices run, so an item where the two doses disagree gets "no answer".
Weights and losses stay in ``data/corpus/lab/dictations/alm/`` (not git).

Usage::

    python -m lab.dictations_alm train [--dose small|larger]   # Mac GPU; resumes per model
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time

import numpy as np

from lab import dictations as dc
from lab.paths import FAST, out
from metadata import config

WORK = dc.WORK / "alm"
CACHE = FAST / "two_voices_alm"
CACHE_RUN = {"small": "masked_small", "larger": "masked_larger"}
SCORE_ROWS = 16  # windows scored at a time: memory only, same numbers (lab.twovoices_alm)
MICRO = 2  # sequences per micro-batch: memory only, the same update


def scored_keys(b: dict) -> list[str]:
    """Every scored unit: all items except the candidates' training chunks, and whole lectures."""
    return sorted([k for k in b["items"] if "|train|" not in k] + list(b["whole"]))


def plan(cfg: dict, b: dict) -> dict:
    """Training ids per dose and candidate (inside the training part), and test ids."""
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    t, seq = cfg["lab"]["dictations"], cfg["alm"]["seq"]
    size = cfg["lab"]["two_voices"]["chunk_words"]
    tok = Tokenizer.from_file(str(TOKENIZER))
    train, short = {}, {}
    for c, words in b["train_tokens_stream"].items():
        enc = tok.encode(" ".join(words))
        limit = len(" ".join(words[: t["train_chunks"] * size]))
        for dose, s in t["doses"].items():
            n = s * seq
            if len(enc.ids) < n or enc.offsets[n - 1][1] > limit:
                short[f"{dose}|{c}"] = "training slice longer than the training part"
                continue
            train[f"{dose}|{c}"] = enc.ids[:n]
    keys = scored_keys(b)
    allw = {**b["items"], **b["whole"]}
    tests = [tok.encode(" ".join(allw[k])).ids for k in keys]
    digest = hashlib.sha256(json.dumps([keys, tests]).encode()).hexdigest()
    return {"train": train, "not_attempted": short, "keys": keys, "tests": tests,
            "digest": digest}  # fmt: skip


def _sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _cached(dose: str, cfg: dict) -> tuple | None:
    """The two-voices run's Joseph Smith ordinary-voice model for this dose, if it fits."""
    d = CACHE / CACHE_RUN[dose]
    j, w = d / "joseph_smith__ordinary.json", d / "joseph_smith__ordinary.pt"
    if not (j.exists() and w.exists()):
        return None
    rec = json.loads(j.read_text())
    if rec.get("train_tokens") != cfg["lab"]["dictations"]["doses"][dose] * cfg["alm"]["seq"]:
        return None
    if rec.get("weights_sha256") and rec["weights_sha256"] != _sha(w):
        return None
    return w, rec


def train(cfg: dict, only: str | None) -> int:
    import torch

    from alm.benchmark import _base, _device, finetune, window_losses
    from lab.twovoices_alm import free

    a, t = cfg["alm"], cfg["lab"]["dictations"]
    lr = cfg["timelocked_lm"]["finetune_lr"]
    b = dc.build(cfg)
    p = plan(cfg, b)
    dev = _device()
    model = _base(t["size"], cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    meta = {"keys": p["keys"], "digest": p["digest"], "not_attempted": p["not_attempted"]}
    old = WORK / "items.json"
    if old.exists() and json.loads(old.read_text())["digest"] != p["digest"]:
        raise SystemExit(f"{old}: the scored units changed since the last run; move the folder "
                         "aside (never delete) and start again")  # fmt: skip
    out(WORK / "items.json").write_text(json.dumps(meta))

    def score():
        got = window_losses(model, p["tests"], a["score_window"], dev, rows=SCORE_ROWS)
        return np.array([np.mean(w) if w else np.nan for w in got], dtype=np.float64)

    t0 = time.time()
    if not (WORK / "base.npy").exists():
        model.load_state_dict(state)
        np.save(out(WORK / "base.tmp.npy"), score())
        (WORK / "base.tmp.npy").replace(WORK / "base.npy")
        print(f"base scored: {len(p['keys'])} units, {time.time() - t0:.0f} s", flush=True)
    for key, ids in sorted(p["train"].items()):
        dose, c = key.split("|")
        if only and dose != only:
            continue
        name = f"{dose}__{c}"
        if (WORK / f"{name}.json").exists():
            continue
        t1 = time.time()
        model.load_state_dict(state)
        cached = _cached(dose, cfg) if c == "joseph_smith" else None
        if cached:
            model.load_state_dict(torch.load(cached[0], map_location="cpu"))
            info = {"reused": str(cached[0]), "steps": cached[1].get("steps"),
                    "seed": cached[1].get("seed")}  # fmt: skip
        else:
            seed = config.derive_seed(f"{a['train_seed']}:{t['seed']}:{key}", cfg)
            torch.manual_seed(seed)
            info = finetune(model, np.array(ids, dtype=np.int32), cfg, seed, MICRO, dev, lr)
            info["seed"] = seed
        free(dev)
        losses = score()
        np.save(out(WORK / f"{name}.tmp.npy"), losses)
        (WORK / f"{name}.tmp.npy").replace(WORK / f"{name}.npy")
        rec = {"train_tokens": len(ids), **info, "lr": lr, "digest": p["digest"],
               "sec": round(time.time() - t1, 1)}  # fmt: skip
        out(WORK / f"{name}.json").write_text(json.dumps(rec))  # written last: the done mark
        print(f"  {name}: {len(ids):,} tokens, {time.time() - t1:.0f} s "
              f"(total {(time.time() - t0) / 60:.1f} min)", flush=True)  # fmt: skip
    return 0


def load(dose: str, cands: list[str], digest: str) -> tuple[dict, dict]:
    """({unit: {candidate: score}}, model records); ``OSError`` if a model is missing or was
    scored on other units."""
    base = np.load(WORK / "base.npy")
    keys = json.loads((WORK / "items.json").read_text())["keys"]
    cols, recs = {}, {}
    for c in cands:
        j = WORK / f"{dose}__{c}.json"
        if not j.exists():
            raise OSError(f"{j} missing: run python -m lab.dictations_alm train --dose {dose}")
        recs[c] = json.loads(j.read_text())
        if recs[c]["digest"] != digest:
            raise OSError(f"{j} was scored on other units")
        cols[c] = np.load(WORK / f"{dose}__{c}.npy") - base
    scores = {k: {c: float(cols[c][i]) for c in cands} for i, k in enumerate(keys)}
    return {k: v for k, v in scores.items() if not any(np.isnan(x) for x in v.values())}, recs


def analyse(cfg: dict, b: dict, check_only: bool) -> dict:
    t = cfg["lab"]["dictations"]
    cands = b["cands"]
    groups = list(b["meta"]["groups"])
    if not (WORK / "items.json").exists():
        raise OSError(f"{WORK / 'items.json'} missing: run python -m lab.dictations_alm train")
    p = plan(cfg, b)
    res: dict = {"doses": {}, "recipe": "alm.benchmark.finetune and window_losses, unchanged",
                 "base_model": f"timelocked_lm {t['size']}"}  # fmt: skip
    loaded = {}
    for dose in t["doses"]:
        scores, recs = load(dose, cands, p["digest"])
        loaded[dose] = scores
        ka = dc.known_answer({k: v for k, v in scores.items() if "|test|" in k}, cands, t)
        res["doses"][dose] = {
            "train_tokens": t["doses"][dose] * cfg["alm"]["seq"],
            "known_answer": ka,
            "models": {
                c: {k: recs[c].get(k) for k in ("train_tokens", "steps", "seed", "reused")}
                for c in cands
            },
        }
    passed = [d for d, r in res["doses"].items() if r["known_answer"]["passed"]]
    res["passed_both"] = len(passed) == len(t["doses"])
    res["known_answer"] = {"passed": res["passed_both"], "passed_doses": passed}
    if check_only:
        return res
    if not res["passed_both"]:
        # The scoring pass scores every unit in one go; when the check misses at either dose the
        # target units' scores (lectures, dictated texts, the Book of Mormon) are not read.
        res["stopped"] = "missed the known-answer bar at a dose: not used for either question"
        return res
    for dose, scores in loaded.items():
        r = res["doses"][dose]
        r["lectures"] = dc.lecture_table(scores, cands, scores.keys())
        r["chunk_nearest_candidate"] = dc.group_votes(scores, groups, cands)
        r["mean_score"] = {g: {c: round(float(np.mean([scores[k][c] for k in
                                                        dc.ids_of(scores, f"grp|{g}|")])), 4)
                               for c in cands} for g in groups}  # fmt: skip
    lec = {}
    for n in map(str, range(1, 8)):
        w = {d: r["lectures"].get(n, {}).get("winner") for d, r in res["doses"].items()}
        same = len(set(w.values())) == 1 and None not in w.values()
        lec[n] = {"by_dose": w,
                  "both_doses": next(iter(w.values())) if same and res["passed_both"]
                  else "no answer"}  # fmt: skip
    res["lectures"] = lec
    agree = {}
    for g in [*groups, "book_of_mormon"]:
        tops = {}
        for d, r in res["doses"].items():
            v = r["chunk_nearest_candidate"].get(g, {})
            tops[d] = max(v, key=v.get) if v else None
        same = len(set(tops.values())) == 1 and None not in tops.values()
        agree[g] = {"most_chunks_by_dose": tops,
                    "both_doses": next(iter(tops.values())) if same and res["passed_both"]
                    else "no answer"}  # fmt: skip
    res["groups_both_doses"] = agree
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["train"])
    ap.add_argument("--dose", help="train: one dose of lab.dictations.doses")
    a = ap.parse_args(argv)
    return train(config.load(), a.dose)


if __name__ == "__main__":
    raise SystemExit(main())
