"""Robustness to deliberate imitation (BOM-31; pre-registration 9, Amendments 7 and 31,
``docs/imitation-plan.md``).

The dual-register authors (``data/benchmark/dual_register.json``, BOM-46: authors with a curated
imitation-biblical work and at least 10,000 words of other prose) are candidates on their ordinary
prose beside ``imitation.distractors_per_list`` seeded period authors from each of the history and
general-prose control lists. **Forward** (section 9, sets the weights): each imitation work's
non-overlapping 5,000-word windows are attributed; does the method still pick the real author?
**Reverse** (reported only): candidates on imitation text (the dual-register authors' and every
other curated imitation author's), tests from the dual-register authors' ordinary prose.

Each method part writes ``data/benchmark/imitation/<method>.json`` (names and numbers only);
``report`` merges them into ``data/benchmark/imitation.json``: per method the forward accuracy with
its exact (Clopper-Pearson) 95% interval and n (Amendment 7), per-author accuracy, and section 9's
weight (full at or above 80%, half from 60%, dropped below).

Usage::

    python -m eval.imitation build            # -> data/benchmark/imitation_tasks.json (ids)
    python -m eval.imitation classic          # Delta, Cosine Delta, GI, ENSC (Mac CPU)
    python -m eval.imitation style            # style embeddings (Mac GPU)
    python -m eval.imitation alm <size> [--variant v1|v3] [--micro-batch 8]   # GPU
    python -m eval.imitation report           # -> data/benchmark/imitation.json
    python -m eval.imitation files <size>     # paths the model part reads (a pod's uploads)
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")
TASKS = DIR / "imitation_tasks.json"
PARTS = DIR / "imitation"
OUT = DIR / "imitation.json"
DUAL = DIR / "dual_register.json"
CURATED = Path("data/controls/pseudo_biblical_curated.txt")
KNOWN = DIR / "pseudo_biblical_known.json"
LISTS = ("history", "general_prose")


def windows(tokens: list, size: int) -> list[tuple[int, int]]:
    """Non-overlapping ``size``-word windows (start, end); a test is never counted twice."""
    return [(i, i + size) for i in range(0, len(tokens) - size + 1, size)]


def clopper_pearson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    from scipy.stats import beta

    if n == 0:
        return (0.0, 1.0)
    a = (1 - level) / 2
    lo = 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a, k + 1, n - k))
    return (lo, hi)


def weight(acc: float, bands: list[list[float]]) -> float:
    """Section 9: the first band whose floor the accuracy reaches gives the weight, else 0."""
    for floor, w in sorted(bands, reverse=True):
        if acc >= floor:
            return w
    return 0.0


def _words() -> dict[str, int]:
    out = {}
    for f in glob.glob("data/catalog/signatures_normalized/*.parquet"):
        t = pq.read_table(f, columns=["work_id", "words"])
        out.update(zip(t.column(0).to_pylist(), t.column(1).to_pylist(), strict=True))
    return out


def build() -> int:
    """Ids only: candidates, their reference works in each direction, the imitation works."""
    from metadata.pseudo_biblical import eligible_rows, work_key
    from style_embed.data import _named

    cfg = load_config()
    im = cfg["imitation"]
    dual = json.loads(DUAL.read_text())["dual_register_authors"]
    curated = CURATED.read_text().split()
    cat = {r["work_id"]: r for r in pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "author_norm", "title", "source"]
    ).to_pylist()}  # fmt: skip
    nw = _words()
    known = json.loads(KNOWN.read_text())["authors"]
    imitation: dict[str, list[str]] = defaultdict(list)
    for w in curated:
        a = (cat.get(w) or {}).get("author_norm")
        if a:
            imitation[a].append(w)
    for a, w in im["extra_imitation_works"].items():  # volumes the curated list keeps apart
        imitation[a] += [x for x in w if x not in imitation[a]]
    pb_keys = {work_key(cat[w]["title"]) for w in curated if w in cat}
    skip = set(im["exclude_reference_titles"])
    ordinary: dict[str, dict[str, str]] = defaultdict(dict)  # author -> key -> longest copy
    for r in eligible_rows(cfg):
        a, k = r["author_norm"], work_key(r["title"])
        if a in dual and r["work_id"] not in curated and k not in pb_keys and k not in skip:
            if nw.get(r["work_id"], 0) > nw.get(ordinary[a].get(k, ""), 0):
                ordinary[a][k] = r["work_id"]
    bad = cfg["style_embed"]["corporate"]
    taken = set(dual) | {(cat.get(w) or {}).get("author_norm") for w in curated}
    distractors: dict[str, str] = {}
    for name in LISTS:
        rows = [json.loads(ln) for ln in Path(f"data/controls/{name}.jsonl").read_text()
                .splitlines()]  # fmt: skip
        by: dict[str, str] = {}
        for r in sorted(rows, key=lambda r: r["work_id"]):
            a = ((cat.get(r["work_id"]) or {}).get("author_norm") or "").strip()
            if (r["source"] == "chronicling_america" or (r["words"] or 0) < im["min_words"]
                    or not _named(a) or any(c in a for c in bad) or a in taken
                    or a in distractors):  # fmt: skip
                continue
            if (r["words"] or 0) > nw.get(by.get(a, ""), 0):
                by[a] = r["work_id"]
        rng = random.Random(derive_seed(f"{im['distractor_seed']}:{name}", cfg))
        for a in rng.sample(sorted(by), im["distractors_per_list"]):
            distractors[a] = by[a]
    other_im = {a: ws for a, ws in imitation.items() if a not in dual}
    for k, s in known.items():  # the benchmark's imitation authors not already in by a copy
        if not any(work_key(cat[w]["title"]) in pb_keys for w in s["works"] if w in cat):
            other_im[k] = s["works"]
    # a reverse candidate needs the reference floor of imitation text, as every other candidate
    other_im = {a: ws for a, ws in other_im.items()
                if sum(nw.get(w, 0) for w in ws) >= im["min_words"]}  # fmt: skip
    spec = {**stamp(),
            "forward": {"candidates": {**{a: sorted(ordinary[a].values()) for a in dual},
                                       **{a: [w] for a, w in sorted(distractors.items())}},
                        "tests": {a: sorted(imitation[a]) for a in dual}},
            "reverse": {"candidates": {**{a: sorted(imitation[a]) for a in dual},
                                       **{a: sorted(ws) for a, ws in sorted(other_im.items())}},
                        "tests": {a: sorted(ordinary[a].values()) for a in dual}}}  # fmt: skip
    ids = {w for d in ("forward", "reverse") for part in ("candidates", "tests")
           for ws in spec[d][part].values() for w in ws}  # fmt: skip
    spec["words"] = {w: nw.get(w, 0) for w in sorted(ids)}
    TASKS.write_text(json.dumps(spec, indent=1) + "\n")
    f = spec["forward"]
    print(f"forward: {len(f['candidates'])} candidates ({len(dual)} dual-register, "
          f"{len(distractors)} distractors); imitation works "
          f"{ {a: len(w) for a, w in f['tests'].items()} } -> {TASKS}")  # fmt: skip
    return 0


def task(direction: str, cfg: dict, tokens) -> dict:
    """``eval.benchmark``'s task form: {"authors": {a: blocks}, "tests": [(a, words, None)]}.
    ``tokens`` maps work ids to word lists (benchmark word form, or original words for the ALM).
    Reverse tests are capped at ``imitation.reverse_max_tests`` per author (seeded)."""
    from eval.power import blocks

    im, n = cfg["imitation"], cfg["benchmark"]["test_words"]
    spec = json.loads(TASKS.read_text())[direction]
    toks = tokens(sorted({w for ws in [*spec["candidates"].values(), *spec["tests"].values()]
                          for w in ws}))  # fmt: skip
    authors = {a: blocks([t for w in ws for t in toks[w]]) for a, ws in spec["candidates"].items()}
    tests = []
    for a, ws in sorted(spec["tests"].items()):
        mine = [(a, toks[w][s:e], f"{w}:{s}") for w in ws for s, e in windows(toks[w], n)]
        if direction == "reverse" and len(mine) > im["reverse_max_tests"]:
            rng = random.Random(derive_seed(f"{im['reverse_seed']}:{a}", cfg))
            mine = sorted(rng.sample(mine, im["reverse_max_tests"]), key=lambda x: x[2])
        tests += [(x[0], x[1], None, x[2]) for x in mine]
    return {"authors": authors, "tests": [t[:3] for t in tests], "where": [t[3] for t in tests]}


def _pool(cfg: dict) -> list[list[str]]:
    from eval.benchmark import imposter_pool

    spec = json.loads(TASKS.read_text())
    ids = {w for d in ("forward", "reverse") for part in ("candidates", "tests")
           for ws in spec[d][part].values() for w in ws}  # fmt: skip
    names = tuple(sorted(set(spec["forward"]["candidates"]) | set(spec["reverse"]["candidates"])))
    return imposter_pool(cfg["imitation"]["imposter_pool"], ids, cfg, exclude_authors=names)


def _save(method: str, recs_by: dict[str, list[dict]]) -> None:
    PARTS.mkdir(parents=True, exist_ok=True)
    (PARTS / f"{method}.json").write_text(json.dumps({**stamp(), "records": recs_by},
                                                     indent=1) + "\n")  # fmt: skip


def classic() -> int:
    from eval.benchmark import _ensc_predict, _masked_tokens, run_task
    from metadata.config import classic_kwargs

    cfg = load_config()
    ens = json.loads((DIR / "benchmark.json").read_text())["ensc"]  # the benchmark's calibration
    priors = classic_kwargs(cfg)["ensc"]["priors"]
    pool = _pool(cfg)
    out: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for direction in ("forward", "reverse"):
        t = task(direction, cfg, _masked_tokens)
        rng = random.Random(derive_seed(f"bom31-gi:{direction}", cfg))
        recs = run_task(t, pool, cfg, rng, progress=f"classic {direction}")
        for m in ("burrows_delta", "cosine_delta", "general_imposters"):
            out[m][direction] = [{"author": r["author"], "predicted": r[m], "where": w}
                                 for r, w in zip(recs, t["where"], strict=True)]  # fmt: skip
        out["ensc"][direction] = [
            {"author": r["author"], "where": w,
             "predicted": _ensc_predict(r, ens["shrinkage"], ens["alpha"], priors, None)}
            for r, w in zip(recs, t["where"], strict=True)]  # fmt: skip
    for m, recs_by in out.items():
        _save(m, recs_by)
    print(f"classic parts -> {PARTS}")
    return 0


def _vector_method(name: str, embed, cfg: dict, tokens) -> int:
    """Closed set by cosine distance to each candidate's profile (the BOM-30 benchmark's rule)."""
    from classic.delta import cosine_delta

    recs_by = {}
    for direction in ("forward", "reverse"):
        t = task(direction, cfg, tokens)
        prof = {a: embed([w for b in bl for w in b]) for a, bl in t["authors"].items()}
        recs = []
        for (a, words, _), where in zip(t["tests"], t["where"], strict=True):
            x = embed(words)
            dist = {b: cosine_delta(x, p) for b, p in prof.items()}
            recs.append({"author": a, "where": where,
                         "predicted": min(dist, key=lambda b: (dist[b], b))})  # fmt: skip
        recs_by[direction] = recs
        print(f"  {name} {direction}: {len(recs)} tests", flush=True)
    _save(name, recs_by)
    return 0


def style() -> int:
    from eval.benchmark import _masked_tokens
    from style_embed.benchmark import MODEL, embedder

    cfg = load_config()
    return _vector_method("style_embed", embedder(MODEL, cfg), cfg, _masked_tokens)


def _original(ids: list[str]) -> dict[str, list[str]]:
    from alm.benchmark import _words

    masks = [Path("data/kjv_mask/controls/spans.jsonl"),
             Path("data/kjv_mask/known_answer/spans.jsonl")]  # fmt: skip
    return _words(ids, masks)


def alm(size: str, variant: str, micro: int) -> int:
    """Amendment 22's ALM (``variant`` "" or "v1": one fine-tuned copy per candidate, score =
    mean window loss less the base model's) or Amendment 23's V3 (base hidden states, cosine)."""
    cfg = load_config()
    tag = f"alm_{size}_{variant}" if variant else f"alm_{size}"
    if variant == "v3":
        import torch
        from tokenizers import Tokenizer

        from alm.benchmark import _base, _device
        from alm.variants import hidden
        from timelocked_lm.release import TOKENIZER

        dev = _device()
        model = _base(size, cfg).to(dev).eval()
        tok = Tokenizer.from_file(str(TOKENIZER))
        w = cfg["alm"]["score_window"]

        @torch.no_grad()
        def embed(words: list[str]) -> np.ndarray:
            ids = tok.encode(" ".join(words)).ids
            n = max(1, len(ids) // w)
            x = torch.tensor(ids[: n * w] if len(ids) >= w else ids, device=dev).view(n, -1)
            return hidden(model, x).mean(dim=(0, 1)).float().cpu().numpy().astype(np.float64)

        return _vector_method(tag, embed, cfg, _original)
    import torch
    from tokenizers import Tokenizer

    from alm.benchmark import EOT, WORK, _base, _device, _encode, finetune, window_loss
    from timelocked_lm.release import TOKENIZER

    a = cfg["alm"]
    dev = _device()
    tok = Tokenizer.from_file(str(TOKENIZER))
    eot = tok.token_to_id(EOT)
    lr = a["v1_finetune_lr"] if variant == "v1" else cfg["timelocked_lm"]["finetune_lr"]
    work = WORK / f"imitation_{size}{'_' + variant if variant else ''}"
    work.mkdir(parents=True, exist_ok=True)
    base = _base(size, cfg).to(dev).eval()
    state = {k: v.clone() for k, v in base.state_dict().items()}
    recs_by = {}
    for direction in ("forward", "reverse"):
        spec = json.loads(TASKS.read_text())[direction]
        toks = _original(sorted({w for ws in [*spec["candidates"].values(),
                                              *spec["tests"].values()] for w in ws}))  # fmt: skip
        t = task(direction, cfg, lambda ids, toks=toks: {w: toks[w] for w in ids})
        ids_t = [_encode(tok, words) for _, words, _ in t["tests"]]
        path = work / f"{direction}__base.json"
        if not path.exists():
            path.write_text(json.dumps([window_loss(base, x, a["score_window"], dev)
                                        for x in ids_t]))  # fmt: skip
        b0 = json.loads(path.read_text())
        got = {}
        for c, wids in sorted(spec["candidates"].items()):
            path = work / f"{direction}__{c.replace('/', '_')}.json"
            if not path.exists():
                ids = np.array([i for w in wids for i in [*_encode(tok, toks[w]), eot]],
                               dtype=np.int32)  # fmt: skip
                base.load_state_dict(state)
                seed = derive_seed(f"{a['train_seed']}:imitation:{direction}:{c}", cfg)
                torch.manual_seed(seed)
                info = finetune(base, ids, cfg, seed, micro, dev, lr)
                losses = [window_loss(base, x, a["score_window"], dev) for x in ids_t]
                path.write_text(json.dumps({"train_tokens": len(ids), **info, "losses": losses}))
                print(f"  {tag} {direction} {c}: {len(ids):,} tokens", flush=True)
            got[c] = json.loads(path.read_text())["losses"]
        recs = []
        for i, ((auth, _, _), where) in enumerate(zip(t["tests"], t["where"], strict=True)):
            r = {c: float(np.mean(np.array(g[i]) - np.array(b0[i]))) for c, g in got.items()}
            recs.append({"author": auth, "where": where,
                         "predicted": min(r, key=lambda c: (r[c], c))})  # fmt: skip
        recs_by[direction] = recs
    _save(tag, recs_by)
    return 0


def files(size: str) -> list[str]:
    """Every local file the model part reads beyond the repository: the normalised texts of the
    tasks' works and the size's base model (for ``scripts/pod_jobs.py --files``)."""
    from ocr_fix.normalize import norm_path

    spec = json.loads(TASKS.read_text())
    ids = {w for d in ("forward", "reverse") for part in ("candidates", "tests")
           for ws in spec[d][part].values() for w in ws}  # fmt: skip
    cols = ["work_id", "source", "text_path"]
    rows = [r for r in pq.read_table("data/catalog/catalog.parquet", columns=cols).to_pylist()
            if r["work_id"] in ids]  # fmt: skip
    missing = ids - {r["work_id"] for r in rows}
    if missing:
        raise SystemExit(f"{len(missing)} task works not in the catalog, e.g. {sorted(missing)[0]}")
    return sorted({str(norm_path(r)) for r in rows}) + [
        f"data/corpus/timelocked_lm/runs/{size}/model.pt"
    ]


def summarise(recs: list[dict], bands: list[list[float]]) -> dict:
    k, n = sum(r["predicted"] == r["author"] for r in recs), len(recs)
    acc = k / n if n else 0.0
    per: dict[str, list[bool]] = defaultdict(list)
    for r in recs:
        per[r["author"]].append(r["predicted"] == r["author"])
    authors_right = sum(np.mean(v) > 0.5 for v in per.values())
    return {"tests": n, "correct": k, "accuracy": acc, "ci95": clopper_pearson(k, n),
            "by_author": {a: float(np.mean(v)) for a, v in sorted(per.items())},
            "authors": len(per), "authors_majority_right": int(authors_right),
            "authors_ci95": clopper_pearson(int(authors_right), len(per)),
            "weight": weight(acc, bands)}  # fmt: skip


def report() -> int:
    cfg = load_config()
    bands = cfg["imitation"]["weight_bands"]
    methods = {}
    for p in sorted(PARTS.glob("*.json")):
        recs_by = json.loads(p.read_text())["records"]
        methods[p.stem] = {"forward": summarise(recs_by["forward"], bands),
                           "reverse": summarise(recs_by["reverse"], bands)}  # fmt: skip
        methods[p.stem]["weight"] = methods[p.stem]["forward"]["weight"]
    doc = {**stamp(), "rule": "section 9: forward accuracy; full weight >= 0.8, half >= 0.6, "
           "else dropped (Amendment 7: exact 95% interval and n reported; equal-weight run "
           "beside)", "methods": methods}  # fmt: skip
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    for m, r in methods.items():
        f = r["forward"]
        print(f"{m}: forward {f['correct']}/{f['tests']} = {f['accuracy']:.2f} "
              f"(95% {f['ci95'][0]:.2f}-{f['ci95'][1]:.2f}), weight {r['weight']}; reverse "
              f"{r['reverse']['accuracy']:.2f}")  # fmt: skip
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["build", "classic", "style", "alm", "report", "files"])
    ap.add_argument("size", nargs="?", choices=["pilot", "base", "large"])
    ap.add_argument("--variant", choices=["v1", "v3"], default="")
    ap.add_argument("--micro-batch", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "alm":
        if not a.size:
            ap.error("alm needs a size")
        return alm(a.size, a.variant, a.micro_batch)
    if a.cmd == "files":
        if not a.size:
            ap.error("files needs a size")
        print("\n".join(files(a.size)))
        return 0
    return {"build": build, "classic": classic, "style": style, "report": report}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
