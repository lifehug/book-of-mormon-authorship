"""Cross-work decoys and the register placebo (BOM-76; Amendment 49; ``docs/part2-plan.md``).

**Cross-work decoys.** Every Amendment 43 candidate model trained on all of its unit's works, so a
different work is reached by leaving one out. For each candidate unit with two or more works (a
work is one publication: a book, or one periodical's pieces together), one model per held-out work
is fine-tuned on the unit's other works with Amendment 43's settings, and the held-out work gives
up to ``alm.max_tests`` distinct seeded 5,000-word windows. Each window is scored by the fold's
model and by the Amendment 43 model of every unit belonging to the other candidates. A window is
recognised when the fold's model scores closest; a candidate's cross-work recognition rate pools
its folds, with a 95% Wilson interval.

**Register placebo.** Writers in biblical or prophetic style who could not have written the book
(``data/benchmark/part2/placebo.json``): primary, died before September 1827; secondary, born
after 1830. Each is fine-tuned on ``candidates.dose_check.slices`` seeded slices of exactly the
revelation sample's training tokens (Amendment 45) and scored on the sealed set. ``report`` ranks
all equal-dose models (Amendment 45's slices, the placebo slices, the revelation model) on each
Book of Mormon chunk.

Texts: candidates as Amendment 43 reads them (King James spans masked, Book of Mormon quotations
dropped); placebo texts masked by ``kjv_mask.run placebo``. Inputs (licensed text as token ids) go
under ``data/corpus/alm/part2/``; results hold names and numbers only.

Usage::

    python -m eval.part2_decoys plan                     # Mac: folds, placebo slices, inputs
    python -m eval.part2_decoys lowo pilot|base|mid      # GPU: fold models; every rival scores
    python -m eval.part2_decoys placebo pilot|base|mid   # GPU: placebo slices on the sealed set
    python -m eval.part2_decoys report                   # Mac, after both: data/benchmark/part2/
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/benchmark/part2")
PLAN = OUT / "decoys_plan.json"
WORK = Path("data/corpus/alm/part2")
INPUTS = WORK / "inputs"
CAND = Path("data/corpus/alm/candidates")  # Amendment 43's weights, per size
PLACEBO = OUT / "placebo.json"
PLACEBO_SPANS = Path("data/kjv_mask/placebo/spans.jsonl")
BLIND = Path("data/blind/part2")
BLOCK = 1000


def work_of(doc_id: str) -> str:
    """A publication: a periodical's pieces share the part before ``__``."""
    return doc_id.split("__")[0]


def person_of(unit: str) -> str:
    return unit.split("__")[1]


def _placebo_words() -> dict[str, list[list[str]]]:
    """{writer: [masked original words per text]} for both placebo groups."""
    from alm.benchmark import _words
    from kjv_mask.run import artifacts
    from segment.build import original_words

    pl = json.loads(PLACEBO.read_text())
    out: dict[str, list[list[str]]] = {}
    for who, v in pl["primary"].items():
        got = _words(v["works"], [PLACEBO_SPANS])
        out[f"primary:{who}"] = [got[w] for w in v["works"]]
    spans = {json.loads(ln)["id"]: json.loads(ln)["spans"]
             for ln in PLACEBO_SPANS.read_text().splitlines()}  # fmt: skip
    for f in sorted((OUT / "texts").glob("*.txt")):
        text = artifacts(f.read_text(encoding="utf-8", errors="replace"))[0]
        who = next(k for k, v in pl["secondary"].items() if isinstance(v, dict)
                   and f.stem.split("_")[0] in v["work"].lower().replace(" ", "_"))  # fmt: skip
        out[f"secondary:{who}"] = [original_words(text, spans.get(f"placebo:{f.stem}", []))]
    return out


def plan() -> int:
    from tokenizers import Tokenizer

    from alm.candidates import PLAN as A43_PLAN
    from alm.candidates import candidate_words, slug, window_starts
    from timelocked_lm.release import EOT, TOKENIZER

    cfg = load_config()
    a, bm = cfg["alm"], cfg["benchmark"]
    k = bm["test_words"] // BLOCK
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    INPUTS.mkdir(parents=True, exist_ok=True)
    units = {u["key"] for u in json.loads(A43_PLAN.read_text())["units"]
             if u["kind"] == "candidate"}  # fmt: skip
    folds, untestable = [], {}
    for (who, sample, period), docs in sorted(candidate_words().items()):
        unit = slug("cand", who, sample, period)
        if unit not in units:
            continue
        works: dict[str, list[list[str]]] = defaultdict(list)
        for d, ws in docs:
            works[work_of(d)].append(ws)
        if len(works) < 2:
            untestable[unit] = f"{len(works)} work"
            continue
        for w in sorted(works):
            test = [x for ws in works[w] for x in ws]
            n = len(test) // BLOCK
            name = f"{unit}#{w.removeprefix('cand:')}"
            if n < k:
                note = f"held-out work {len(test):,} words, under one window"
                folds.append({"fold": name, "unit": unit, "work": w, "tests": 0,
                              "note": note})  # fmt: skip
                continue
            rng = random.Random(derive_seed(f"{a['test_seed']}:part2-lowo:{name}", cfg))
            starts = window_starts(n, n, k, a["max_tests"], rng)
            tests = [tok.encode(" ".join(test[s * BLOCK : (s + k) * BLOCK])).ids for s in starts]
            train = [ws for o in sorted(works) if o != w for ws in works[o]]
            ids = np.array([i for ws in train for i in [*tok.encode(" ".join(ws)).ids, eot]],
                           dtype=np.int32)  # fmt: skip
            np.savez(INPUTS / f"lowo__{name.replace('#', '__')}.npz", train=ids,
                     tests=np.array([i for t in tests for i in t], dtype=np.int32),
                     lens=np.array([len(t) for t in tests], dtype=np.int64))  # fmt: skip
            folds.append({"fold": name, "unit": unit, "work": w, "tests": len(tests),
                          "train_tokens": int(len(ids)), "test_words": len(test)})  # fmt: skip
            print(f"  {name}: train {len(ids):,} tokens, {len(tests)} windows", flush=True)
    placebo = {}
    for who, texts in sorted(_placebo_words().items()):
        ids = np.array([i for ws in texts for i in [*tok.encode(" ".join(ws)).ids, eot]],
                       dtype=np.int32)  # fmt: skip
        key = "placebo__" + who.replace(":", "__").replace(" ", "-")
        np.savez(INPUTS / f"{key}.npz", train=ids)
        placebo[key] = {"writer": who, "tokens": int(len(ids)),
                        "words": sum(len(ws) for ws in texts)}  # fmt: skip
        print(f"  {key}: {len(ids):,} tokens", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    PLAN.write_text(json.dumps({**stamp(), "folds": folds, "untestable": untestable,
                                "placebo": placebo}, indent=1) + "\n")  # fmt: skip
    print(f"{sum(f['tests'] > 0 for f in folds)} testable folds, {len(placebo)} placebo writers "
          f"-> {PLAN}")  # fmt: skip
    return 0


def _setup(size: str):
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device
    from timelocked_lm.release import TOKENIZER

    cfg = load_config()
    dev = _device()
    model = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    torch.set_grad_enabled(True)
    return cfg, dev, model, state, Tokenizer.from_file(str(TOKENIZER))


def _losses(model, tests: list[list[int]], window: int, dev: str) -> list[float]:
    import torch

    from alm.benchmark import window_loss

    with torch.no_grad():
        return [float(np.mean(window_loss(model, t, window, dev))) for t in tests]


def lowo(size: str, micro: int) -> int:
    """Fine-tune each fold's model; score every fold's windows with it, the base model and every
    candidate unit's Amendment 43 model (rivals chosen in ``report``)."""
    import torch

    from alm.benchmark import finetune

    cfg, dev, model, state, _ = _setup(size)
    a = cfg["alm"]
    folds = [f for f in json.loads(PLAN.read_text())["folds"] if f["tests"]]
    tests = {}
    for f in folds:
        z = np.load(INPUTS / f"lowo__{f['fold'].replace('#', '__')}.npz")
        cut = np.cumsum(z["lens"])[:-1]
        tests[f["fold"]] = [t.tolist() for t in np.split(z["tests"], cut)]
    out = BLIND / f"lowo_{size}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = json.loads(out.read_text()) if out.exists() else {"base": {}, "a43": {}, "fold": {}}
    w = a["score_window"]
    if not res["base"]:
        res["base"] = {f: _losses(model, t, w, dev) for f, t in tests.items()}
        out.write_text(json.dumps(res))
    for p in sorted((CAND / size).glob("cand__*.pt")):
        if p.stem in res["a43"]:
            continue
        model.load_state_dict(torch.load(p, map_location=dev, weights_only=True))
        res["a43"][p.stem] = {f: _losses(model, t, w, dev) for f, t in tests.items()}
        out.write_text(json.dumps(res))
        print(f"  {size} a43 {p.stem} scored", flush=True)
    for f in folds:
        name = f["fold"]
        if name in res["fold"]:
            continue
        ids = np.load(INPUTS / f"lowo__{name.replace('#', '__')}.npz")["train"]
        model.load_state_dict(state)
        seed = derive_seed(f"{a['train_seed']}:part2-lowo:{name}", cfg)
        torch.manual_seed(seed)
        info = finetune(model, ids, cfg, seed, micro, dev, cfg["timelocked_lm"]["finetune_lr"])
        res["fold"][name] = {"seed": seed, "steps": info["steps"],
                             "losses": _losses(model, tests[name], w, dev)}  # fmt: skip
        out.write_text(json.dumps(res))
        print(f"  {size} fold {name}: {len(ids):,} tokens, {info['steps']} steps", flush=True)
    return 0


def placebo(size: str, micro: int) -> int:
    """Amendment 45's equal-dose check for the placebo writers, on the sealed set."""
    import torch

    from alm.benchmark import finetune
    from alm.candidates import PLAN as A43_PLAN
    from eval.js_register import REVELATION, _rows

    cfg, dev, model, state, tok = _setup(size)
    a, dc = cfg["alm"], cfg["candidates"]["dose_check"]
    n = next(u for u in json.loads(A43_PLAN.read_text())["units"]
             if u["key"] == REVELATION)["train_tokens"]  # fmt: skip
    rows = sorted(_rows(), key=lambda r: r["id"])
    texts = [tok.encode(r["text"]).ids for r in rows]
    from alm.benchmark import window_loss

    with torch.no_grad():
        base = [window_loss(model, x, a["score_window"], dev) for x in texts]
    out = BLIND / f"placebo_{size}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    res = json.loads(out.read_text()) if out.exists() else {"tokens": n, "models": {}}
    for key in sorted(json.loads(PLAN.read_text())["placebo"]):
        ids = np.load(INPUTS / f"{key}.npz")["train"]
        for k in range(dc["slices"]):
            name = f"{key}#slice{k}"
            if name in res["models"]:
                continue
            rng = random.Random(derive_seed(f"{dc['seed']}:{key}:{k}", cfg))
            start = rng.randrange(0, len(ids) - n + 1)
            model.load_state_dict(state)
            seed = derive_seed(f"{a['train_seed']}:part2-placebo:{name}", cfg)
            torch.manual_seed(seed)
            finetune(model, ids[start : start + n], cfg, seed, micro, dev,
                     cfg["timelocked_lm"]["finetune_lr"])  # fmt: skip
            with torch.no_grad():
                loss = [window_loss(model, x, a["score_window"], dev) for x in texts]
            res["models"][name] = {"start": start, "scores": {
                r["id"]: float(np.mean(np.array(loss[i]) - np.array(base[i])))
                for i, r in enumerate(rows)}}  # fmt: skip
            out.write_text(json.dumps(res))
            print(f"  placebo {size} {name}: start {start}", flush=True)
    return 0


def report() -> int:
    """Cross-work recognition per candidate; placebo writers' ranks against the revelation
    model on the Book of Mormon chunks."""
    from eval.js_register import A43, KEY, REVELATION
    from eval.js_register import OUT as A44
    from eval.open_set import wilson

    p = json.loads(PLAN.read_text())
    res: dict = {"cross_work": {}, "placebo": {}, "untestable": p["untestable"]}
    for size in ("pilot", "base", "mid"):
        f = BLIND / f"lowo_{size}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        per: dict[str, list[int]] = defaultdict(list)
        for fold in (x for x in p["folds"] if x["tests"] and x["fold"] in d["fold"]):
            name, unit = fold["fold"], fold["unit"]
            rivals = [u for u in d["a43"] if person_of(u) != person_of(unit)]
            base = d["base"][name]
            own = [x - b for x, b in zip(d["fold"][name]["losses"], base, strict=True)]
            for i, s in enumerate(own):
                best = min(d["a43"][u][name][i] - base[i] for u in rivals)
                per[person_of(unit)].append(int(s < best))
        res["cross_work"][size] = {
            who: {"windows": len(v), "recognised": sum(v), "rate": sum(v) / len(v),
                  "ci95": wilson(sum(v), len(v))} for who, v in sorted(per.items())}  # fmt: skip
    key = json.loads(KEY.read_text())
    bom = [i for i, k in key.items() if k["kind"] == "bom"]
    for size in ("pilot", "base", "mid"):
        fp, fd = BLIND / f"placebo_{size}.json", A44.parent / "a45" / f"dose_{size}.json"
        if not (fp.exists() and fd.exists()):
            continue
        pm = json.loads(fp.read_text())["models"]
        dm = json.loads(fd.read_text())["models"]
        rev = json.loads((A43 / "outputs" / f"alm_{size}.json").read_text())["scores"]["ids"]
        models = {**{m: v["scores"] for m, v in dm.items()},
                  **{m: v["scores"] for m, v in pm.items()}}  # fmt: skip
        ranks: dict[str, list[float]] = defaultdict(list)
        for i in bom:
            s = {m: v[i] for m, v in models.items()}
            s["revelation"] = rev[i]["scores"][REVELATION]
            order = sorted(s, key=s.get)
            pos = {m: order.index(m) + 1 for m in order}
            by: dict[str, list[int]] = defaultdict(list)
            for m, r in pos.items():
                by[m.split("#")[0]].append(r)
            for who, rs in by.items():
                ranks[who].append(float(np.mean(rs)))
        med = {who: float(np.median(v)) for who, v in ranks.items()}
        rv = med["revelation"]
        prim = {w: m for w, m in med.items() if w.startswith("placebo__primary")}
        res["placebo"][size] = {
            "models_ranked": len(models) + 1, "chunks": len(bom), "median_rank": med,
            "revelation_median_rank": rv,
            "primary_at_or_better_than_revelation": sorted(w for w, m in prim.items() if m <= rv),
            "register_reading_triggered": any(m <= rv for m in prim.values())}  # fmt: skip
    (OUT / "decoys_report.json").write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    for size, v in res["cross_work"].items():
        print(f"{size} cross-work: " + "; ".join(f"{w} {x['recognised']}/{x['windows']}"
                                                 for w, x in v.items()))  # fmt: skip
    for size, v in res["placebo"].items():
        print(f"{size} placebo: revelation median rank {v['revelation_median_rank']:.1f} of "
              f"{v['models_ranked']}; primary at or above it: "
              f"{v['primary_at_or_better_than_revelation']}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "lowo", "placebo", "report"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "mid"])
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        return plan()
    if a.cmd == "report":
        return report()
    if not a.size:
        ap.error("lowo and placebo need a size")
    return (lowo if a.cmd == "lowo" else placebo)(a.size, a.micro_batch)


if __name__ == "__main__":
    sys.exit(main())
