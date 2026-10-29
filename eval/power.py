"""Power analysis: how much text each classical method needs (BOM-43).

Section 7 defines a method's minimum sample as the smallest size at which closed-set accuracy
stays at or above 80%. This measures it on known authors only -- the Federalist Papers and the
known-author pseudo-biblical works -- so no seal is broken, and on KJV-masked word counts where
masks exist (4.4). Two sizes matter and they differ:

* **test size**: how long the questioned text must be. An author's held-out passage of N words
  is attributed among all the authors, each represented by the rest of their text. This decides
  whether the Book of Mormon's 2,000- and 5,000-word chunks (4.5) are usable per method.
* **reference size**: how much known text an author needs. A fixed 5,000-word test is attributed
  with every author's reference text capped at R words. This decides whether a candidate with
  only so many masked words is testable at all.

Text is cut into 1,000-word blocks; a test is a run of contiguous blocks, references are the
author's other blocks. Methods (all from ``classic`` with the registered settings): Burrows' and
Cosine Delta on the middle registered MFW size, General Imposters (the author with the highest
score), and ENSC (closed-set posterior; shrinkage 0 until BOM-21 selects it, so its floor is
provisional). Each author is tested ``power.trials`` times per size, seeded.

The floor per method and corpus is the smallest size from which every larger size also reaches
80%; none if it never does. The candidate table puts each candidate's masked word count (BOM-13
and BOM-16) beside the reference floors.

Usage::

    python -m eval.power        # -> data/benchmark/power.json, power_candidates.csv
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

import numpy as np

from classic import (
    ENSC,
    build_vocabulary,
    frequency_matrix,
    general_imposters,
    nearest_authors,
    tokenize,
    word_counts,
)
from metadata.config import classic_kwargs, derive_seed, stamp
from metadata.config import load as load_config

DIR = Path("data/benchmark")
FEDERALIST = DIR / "federalist/papers.jsonl"
PSEUDO = DIR / "pseudo_biblical_known.json"
SPANS = Path("data/kjv_mask/controls/spans.jsonl")
OUT = DIR / "power.json"
TABLE = DIR / "power_candidates.csv"
BLOCK = 1000
METHODS = ("burrows_delta", "cosine_delta", "general_imposters", "ensc")


def federalist() -> dict[str, list[str]]:
    by: dict[str, list[str]] = {}
    for ln in FEDERALIST.read_text().splitlines():
        r = json.loads(ln)
        by.setdefault(r["author"], []).extend(tokenize(r["text"]))
    return by


def pseudo_biblical() -> dict[str, list[str]]:
    import pyarrow.parquet as pq

    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    spec = json.loads(PSEUDO.read_text())["authors"]
    want = {w for a in spec.values() for w in a["works"]}
    spans = {}
    for ln in SPANS.read_text().splitlines():
        r = json.loads(ln)
        if r["id"] in want:
            spans[r["id"]] = r["spans"]
    cols = ["work_id", "source", "text_path"]
    table = pq.read_table("data/catalog/catalog.parquet", columns=cols).to_pylist()
    rows = {r["work_id"]: r for r in table if r["work_id"] in want}
    by: dict[str, list[str]] = {}
    for a, s in spec.items():
        for w in s["works"]:
            text = norm_path(rows[w]).read_text(encoding="utf-8", errors="replace")
            masked = original_words(text, spans.get(w, []))  # KJV removed (4.4)
            by.setdefault(a, []).extend(tokenize(" ".join(masked)))
    return by


def blocks(tokens: list[str]) -> list[list[str]]:
    return [tokens[i : i + BLOCK] for i in range(0, len(tokens) - BLOCK + 1, BLOCK)]


def _attribute(test: list[str], refs: dict[str, list[list[str]]], top_n: int, kw: dict,
               rng: random.Random) -> dict[str, str]:  # fmt: skip
    """Each method's predicted author for ``test`` given reference blocks per author."""
    names = sorted(refs)
    docs = [word_counts(b) for a in names for b in refs[a]]
    labels = [a for a in names for _ in refs[a]]
    vocab = build_vocabulary(docs, top_n=top_n, min_doc_fraction=kw["mfw_min_doc_fraction"])
    X = frequency_matrix(docs, vocab)
    x = frequency_matrix([word_counts(test)], vocab)[0]
    prof = {a: X[[i for i, y in enumerate(labels) if y == a]].mean(axis=0) for a in names}
    out = {
        "burrows_delta": nearest_authors(x, prof, method="burrows", reference=X)[0][0],
        "cosine_delta": nearest_authors(x, prof, method="cosine", reference=X)[0][0],
    }
    gi = kw["imposters"]
    scores = {}
    for a in names:
        imps = np.vstack([prof[b] for b in names if b != a])
        scores[a] = general_imposters(x, prof[a], imps, seed=rng.randrange(2**31), **gi)
    out["general_imposters"] = max(names, key=lambda a: (scores[a], a))
    try:
        model = ENSC(shrinkage=0.0, **kw["ensc"]).fit(X, labels)
        post = model.posteriors(x)
        out["ensc"] = max(post, key=post.__getitem__)
    except ValueError:  # too few reference blocks to pool a variance
        out["ensc"] = None
    return out


def curve(by: dict[str, list[str]], sizes: list[int], kind: str, cfg: dict) -> dict:
    """Accuracy per method per size. ``kind`` is 'test' or 'reference'."""
    kw = classic_kwargs(cfg)
    pw = cfg["power"]
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    rng = random.Random(derive_seed(f"power:{kind}", cfg))
    bl = {a: blocks(t) for a, t in by.items()}
    # One author set for the whole curve, so its points compare like with like: the authors who
    # can supply every size. If fewer than two can, the largest size is dropped instead.
    sizes = sorted(sizes)
    while sizes:
        need = (sizes[-1] // BLOCK + pw["min_reference_blocks"] if kind == "test"
                else pw["fixed_test_words"] // BLOCK + sizes[-1] // BLOCK)  # fmt: skip
        authors = sorted(a for a in bl if len(bl[a]) >= need)
        if len(authors) >= 2:
            break
        sizes = sizes[:-1]
    out = {"authors": authors, "chance": 1 / len(authors) if sizes else None, "points": {}}
    for n in sizes:
        k_test = (n if kind == "test" else pw["fixed_test_words"]) // BLOCK
        k_ref = None if kind == "test" else n // BLOCK
        hits = {m: [] for m in METHODS}
        for a in authors:
            for _ in range(pw["trials"]):
                s = rng.randrange(len(bl[a]) - k_test + 1)
                test = [w for b in bl[a][s : s + k_test] for w in b]
                refs = {}
                for b_ in authors:
                    pool = bl[b_] if b_ != a else bl[a][:s] + bl[a][s + k_test :]
                    if k_ref is not None:
                        start = rng.randrange(len(pool) - k_ref + 1)
                        pool = pool[start : start + k_ref]
                    refs[b_] = pool
                pred = _attribute(test, refs, top_n, kw, rng)
                for m in METHODS:
                    if pred[m] is not None:
                        hits[m].append(pred[m] == a)
        out["points"][str(n)] = {m: (sum(h) / len(h) if h else None) for m, h in hits.items()}
    return out


def floor(curve_: dict, method: str, target: float) -> int | None:
    """Smallest size from which this and every larger size reach ``target``."""
    points = curve_["points"]
    sizes = sorted(int(n) for n in points if points[n][method] is not None)
    for i, n in enumerate(sizes):
        if all(points[str(m)][method] >= target for m in sizes[i:]):
            return n
    return None


def candidate_words() -> dict[tuple[str, str, str], int]:
    """Masked (original) words per candidate x sample x period, from BOM-16's report."""
    from ocr_fix.candidates import units

    meta = {}
    for u in units():
        meta["cand:" + u["unit"].replace(":", "__")] = (u["author"], u["sample"], u["period"])
    rep = json.loads(Path("data/kjv_mask/candidates/report.json").read_text())["per_text"]
    out: dict[tuple[str, str, str], int] = {}
    for tid, r in rep.items():
        if tid in meta:
            key = meta[tid]
        else:  # Joseph Smith Papers samples: cand:<person>__<sample>__<period>
            person, sample, period = tid.removeprefix("cand:").split("__")
            key = (person.replace("-", " ").title(), sample, period)
        out[key] = out.get(key, 0) + r["words"] - r["masked_words"]
    return out


def run() -> int:
    cfg = load_config()
    pw = cfg["power"]
    corpora = {"federalist": federalist(), "pseudo_biblical": pseudo_biblical()}
    result = {**stamp(), "target_accuracy": pw["target_accuracy"], "corpora": {}}
    for name, by in corpora.items():
        words = {a: len(t) for a, t in by.items()}
        print(f"{name}: {words}", flush=True)
        tc = curve(by, pw["sizes"], "test", cfg)
        rc = curve(by, pw["sizes"], "reference", cfg)
        result["corpora"][name] = {
            "words": words, "chance": 1 / len(by), "test_size": tc, "reference_size": rc,
            "floors": {m: {"test": floor(tc, m, pw["target_accuracy"]),
                           "reference": floor(rc, m, pw["target_accuracy"])} for m in METHODS},
        }  # fmt: skip
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    # candidate table. Strict floor = the larger of the two corpora's reference floors (the
    # Federalist papers share one subject, so they are the harder and more honest test); a count
    # at or above it is testable, between the two floors unreliable, below both untestable. Each
    # sample type is listed, then each candidate's pre-1830 total (the confirmatory unit, 3).
    floors = {m: [result["corpora"][c]["floors"][m]["reference"] for c in corpora] for m in METHODS}

    def verdict(n: int, m: str) -> str:
        fs = floors[m]
        if any(f is None for f in fs):
            return "untestable (no floor)"
        return "testable" if n >= max(fs) else "unreliable" if n >= min(fs) else "untestable"

    words = candidate_words()
    totals: dict[str, int] = {cand: 0 for cand, _s, _p in words}  # 0 = no pre-1830 text at all
    for (cand, _sample, period), n in words.items():
        if period == "pre1830":
            totals[cand] = totals.get(cand, 0) + n
    with TABLE.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate", "sample", "period", "masked_words", *METHODS])
        for (cand, sample, period), n in sorted(words.items()):
            w.writerow([cand, sample, period, n, *(verdict(n, m) for m in METHODS)])
        for cand, n in sorted(totals.items()):
            w.writerow([cand, "ALL", "pre1830", n, *(verdict(n, m) for m in METHODS)])
    result["candidate_floors"] = {m: max(f for f in fs if f is not None) if all(fs) else None
                                  for m, fs in floors.items()}  # fmt: skip
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    for c in corpora:
        print(c, json.dumps(result["corpora"][c]["floors"]))
    print(f"-> {OUT}, {TABLE}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
