"""The problem of "nobody": existing verification tools beside ours, on known books (BOM-96;
exploratory).

Can any method say "the author of this book is not among these people"? Each method gives a
score to a (book, candidate author) pair; a verifier is judged by how well the score separates
true pairs from false ones: the area under the curve, the share of true authors confirmed when 5%
of false pairs are accepted, and the share of false pairs accepted when 95% of true authors are
confirmed (the registered bar, section 7 of the pre-registration, is at most 5%).

The books are the sweep's known books (``sweep.units``): the questioned text is the book's first
query chunk, a candidate's known text is their profile (for the true author, rebuilt without the
book), both with King James spans cut out and punctuation kept, since LambdaG models sentences.

- ``prepare``: ``nobody.books`` seeded known books and, for each, the true author and
  ``nobody.others`` seeded other known-book authors as candidates; writes the texts (licensed,
  local only) and the pair list.
- ``scripts/lambdag.R`` runs LambdaG (Nini et al., arXiv 2403.08462) from the authors' R
  package ``idiolect``: POSnoise content masking, sentence tokens, grammar models of order 10,
  the other candidates' profiles as the reference population.
- ``report``: LambdaG, the second style encoder (closest episode) and, where the author models
  of BOM-94 scored the same book, those, on the same pairs.

Usage::

    python -m eval.nobody prepare
    KMP_DUPLICATE_LIB_OK=TRUE RETICULATE_PYTHON=.venv/bin/python Rscript scripts/lambdag.R
    python -m eval.nobody report      # -> data/sweep/nobody.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

WORK = Path("data/corpus/nobody")
OUT = Path("data/sweep/nobody.json")


def masked(text: str, spans: list[dict]) -> str:
    """``text`` with the masked spans cut out, punctuation kept, artifacts normalised."""
    from segment.build import artifacts

    keep, pos = [], 0
    for s in sorted(spans, key=lambda s: s["start"]):
        keep.append(text[pos : s["start"]])
        pos = max(pos, s["end"])
    keep.append(text[pos:])
    return " ".join(artifacts(" ".join(keep))[0].split())


def prepare() -> int:
    import pyarrow.parquet as pq

    from sweep.units import OUT as SWEEP
    from sweep.units import block_text

    cfg = load_config()
    nb = cfg["nobody"]
    blocks = [b for b in pq.read_table(SWEEP / "blocks.parquet").to_pylist()
              if b["role"] != "profile"]  # fmt: skip
    known = sorted({b["author"] for b in blocks})
    rng = random.Random(derive_seed(nb["seed"], cfg))
    books = sorted(rng.sample(known, min(nb["books"], len(known))))
    spans = {}
    want = {b["block_id"] for b in blocks if b["author"] in books}
    for ln in Path("data/kjv_mask/sweep/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if r["id"] in want:
            spans[r["id"]] = r["spans"]
    need = {b["work_id"] for b in blocks if b["author"] in books}
    cat = {r["work_id"]: r for r in pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]).to_pylist()
        if r["work_id"] in need}  # fmt: skip
    WORK.mkdir(parents=True, exist_ok=True)
    with (WORK / "texts.jsonl").open("w") as f:
        for a in books:
            mine = [b for b in blocks if b["author"] == a]
            prof = [b for b in mine if b["role"] == "calib_profile"]
            q = sorted((b for b in mine if b["role"] == "calib_query"),
                       key=lambda b: int(b["block_id"].rsplit(":", 1)[1]))[0]  # fmt: skip
            for role, bs in (("k", prof), ("q", [q])):
                text = " ".join(masked(block_text(cat[b["work_id"]], b["start"], b["words"]),
                                       spans[b["block_id"]]) for b in bs)  # fmt: skip
                f.write(json.dumps({"id": f"{role}:{a}", "author": a, "role": role,
                                    "text": text}) + "\n")  # fmt: skip
    pairs = []
    for a in books:
        others = rng.sample([x for x in books if x != a], min(nb["others"], len(books) - 1))
        pairs += [{"book": a, "candidate": c, "target": c == a} for c in [a, *sorted(others)]]
    (WORK / "pairs.json").write_text(json.dumps(pairs))
    print(f"{len(books)} books, {len(pairs)} pairs ({sum(p['target'] for p in pairs)} true) "
          f"-> {WORK}")  # fmt: skip
    return 0


def verifier(pos: np.ndarray, neg: np.ndarray) -> dict:
    """AUC and the two operating points; higher score = more likely the same author."""
    both = np.concatenate([pos, neg])
    r = both.argsort().argsort() + 1.0
    auc = (r[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
    at5 = float((pos >= np.quantile(neg, 0.95)).mean())
    at95 = float((neg >= np.quantile(pos, 0.05)).mean())
    return {"true_pairs": int(len(pos)), "false_pairs": int(len(neg)),
            "auc": round(float(auc), 3), "true_confirmed_at_5pct_false": round(at5, 3),
            "false_accepted_at_95pct_true": round(at95, 3)}  # fmt: skip


def report() -> int:
    import csv

    from sweep.episodes import load, padded, topk_scores

    pairs = json.loads((WORK / "pairs.json").read_text())
    doc = {**stamp(), "exploratory": True, "pairs": len(pairs), "methods": {}}
    lg = WORK / "lambdag.csv"
    if lg.exists():
        sc = {(r["Q"], r["K"]): float(r["score"]) for r in csv.DictReader(lg.open())}
        got = [(sc[f"q:{p['book']}", p["candidate"]], p["target"]) for p in pairs
               if (f"q:{p['book']}", p["candidate"]) in sc]  # fmt: skip
        v = np.array([g[0] for g in got])
        t = np.array([g[1] for g in got])
        doc["methods"]["LambdaG (Nini et al. 2024), authors' package"] = verifier(v[t], v[~t])
    eps, _ = load("_v2")
    v, t = [], []
    for book in sorted({p["book"] for p in pairs}):
        cands = [p for p in pairs if p["book"] == book]
        q = eps[f"calib_query:{book}:0"]
        G, M = padded([eps[f"calib_profile:{p['candidate']}"] for p in cands])
        s = topk_scores(q, G, M, [1])[1]
        v += s.tolist()
        t += [p["target"] for p in cands]
    v, t = np.array(v), np.array(t)
    doc["methods"]["Second style encoder, closest episode (ours)"] = verifier(v[t], v[~t])
    pool = Path("data/sweep/pool_pilot.npz")
    if pool.exists():  # BOM-94's equal-dose 125M author models scored these books' first chunks
        from eval.library_pool import dose_tables

        z = np.load(pool)
        t_auth, where = z["test_author"].tolist(), z["test_where"].tolist()
        row = {a: i for i, (a, w) in enumerate(zip(t_auth, where, strict=True))
               if w.endswith(":0")}  # fmt: skip
        tables = dose_tables(z["scores"].astype(np.float64), z["models"].tolist())
        labels = {
            "large": "Author models, 125M, 11,264 tokens (ours)",
            "small": "Author models, 125M, 3,039 tokens, median of 3 (ours)",
        }
        for dose, label in labels.items():
            authors, X = tables[dose]
            col = {a: j for j, a in enumerate(authors)}
            got = [(-X[row[p["book"]], col[p["candidate"]]], p["target"]) for p in pairs
                   if p["book"] in row and p["candidate"] in col]  # fmt: skip
            v = np.array([g[0] for g in got])
            t = np.array([g[1] for g in got])
            doc["methods"][label] = verifier(v[t], v[~t])
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    for m, r in doc["methods"].items():
        print(f"{m:55s} AUC {r['auc']:.3f}  true confirmed at 5% false "
              f"{100 * r['true_confirmed_at_5pct_false']:.0f}%  false accepted at 95% true "
              f"{100 * r['false_accepted_at_95pct_true']:.0f}%")  # fmt: skip
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["prepare", "report"])
    return {"prepare": prepare, "report": report}[ap.parse_args(argv).cmd]()


if __name__ == "__main__":
    sys.exit(main())
