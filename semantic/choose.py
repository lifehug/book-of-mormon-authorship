"""Choosing the embedding model for BOM-25 on a test with a known answer, before any build.

The 1807 *New Translation of the Book of Psalms* (``institutional_books:AH5KIN``) renders each
psalm afresh from the Hebrew, so its Psalm n says what the King James Psalm n says in different
period English: paraphrase, which is what BOM-25 has to find. Each of its passages is a query;
the gallery is the whole King James Bible (Apocrypha included) cut into passages the same way. A
query is answered right when the King James Psalm with its number is among the top k. Reported
per model: recall at 1 and 10, and passages embedded per second on this machine, which sets how
long the full index takes. Nothing here reads the Book of Mormon.

``distractors`` repeats the test with corpus passages added to the gallery: what the full index
looks like to a query. Distractors are 128-word passages, up to 100 per volume, from eligible
volumes drawn with a fixed seed, leaving out Bibles, psalters, hymnals and prayer books (other
psalm versions would be right answers counted wrong). Reported: recall at 1, 10, 100, 300 and
1,000, and with ``--rescore``, recall when a second model re-scores the first model's top k.

Usage::

    python -m semantic.choose                          # -> data/semantic/model_choice.json
    python -m semantic.choose distractors <model> [--n 1000000] [--rescore <model>]
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

OUT = Path("data/semantic/model_choice.json")
PASSAGE_WORDS = 128  # candidate passage length; registered with the model in BOM-25's amendment
MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-mpnet-base-v2",
    "BAAI/bge-base-en-v1.5",
    "intfloat/e5-base-v2",
]
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def _roman(s: str) -> int:
    total = 0
    for a, b in zip(s, s[1:] + " ", strict=True):
        total += -_ROMAN[a] if b in _ROMAN and _ROMAN[b] > _ROMAN[a] else _ROMAN[a]
    return total


def passages(text: str, n: int = PASSAGE_WORDS) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + n]) for i in range(0, len(words), n) if words[i : i + n]]


def test_set() -> tuple[list[str], list[str], list[str], list[str]]:
    """(queries, their KJV chapter, gallery passages, their KJV chapter)."""
    from kjv_mask.run import _docs

    queries, qref = [], []
    for d in _docs("italics"):
        if not d["id"].startswith("institutional_books:AH5KIN"):
            continue
        text = d["load"]()
        m = re.search(r"PSALM\s+([IVXLC]+)\s*\.", text)
        if not m:
            continue
        for p in passages(text[m.end() :]):
            queries.append(p)
            qref.append(f"kjv:PSA.{_roman(m.group(1))}")
    chapters: dict[str, list[str]] = {}
    for ln in Path("data/kjv/kjv.jsonl").read_text().splitlines():
        r = json.loads(ln)
        chapters.setdefault(f"kjv:{r['book']}.{r['chapter']}", []).append(r["text"])
    gallery, gref = [], []
    for ref, verses in chapters.items():
        for p in passages(" ".join(verses)):
            gallery.append(p)
            gref.append(ref)
    return queries, qref, gallery, gref


def _prefix(model: str, kind: str) -> str:
    if "e5" in model:
        return "query: " if kind == "q" else "passage: "
    return ""


def score(model: str, data: tuple, device: str) -> dict:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    queries, qref, gallery, gref = data
    st = SentenceTransformer(model, device=device)
    st.max_seq_length = min(st.max_seq_length or 512, 512)
    start = time.time()
    g = st.encode([_prefix(model, "p") + x for x in gallery], batch_size=64,
                  normalize_embeddings=True, convert_to_numpy=True)  # fmt: skip
    rate = len(gallery) / (time.time() - start)
    q = st.encode([_prefix(model, "q") + x for x in queries], batch_size=64,
                  normalize_embeddings=True, convert_to_numpy=True)  # fmt: skip
    top = np.argsort(-(q @ g.T), axis=1)[:, :10]
    gref_a = np.array(gref)
    hit1 = float(np.mean([gref_a[t[0]] == r for t, r in zip(top, qref, strict=True)]))
    hit10 = float(np.mean([r in set(gref_a[t]) for t, r in zip(top, qref, strict=True)]))
    return {"recall_at_1": hit1, "recall_at_10": hit10, "passages_per_second": rate,
            "dim": int(g.shape[1]), "max_seq_length": st.max_seq_length}  # fmt: skip


DISTRACTOR_SKIP = re.compile(r"psalm|bible|testament|hymn|scriptur|psalter|devotion|prayer", re.I)


def distractor_passages(n: int) -> list[str]:
    import random

    from metadata.config import load
    from ocr_fix.normalize import norm_path
    from reuse.exact import eligible_any_year

    rows = [r for r in eligible_any_year(load()) if not DISTRACTOR_SKIP.search(r["title"] or "")]
    rng = random.Random("bom25-distractors")
    rng.shuffle(rows)
    out: list[str] = []
    for r in rows:
        try:
            ps = passages(Path(norm_path(r)).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        ps = [p for p in ps if len(p.split()) == PASSAGE_WORDS]
        out += rng.sample(ps, min(100, len(ps)))
        if len(out) >= n:
            break
    return out[:n]


def distractors(model: str, n: int, rescore: str | None) -> int:
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer

    from metadata.config import stamp

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    q, qref, g, gref = test_set()
    dis = distractor_passages(n)
    allg = g + dis
    gref_a = np.array(gref + ["-"] * len(dis))

    def enc(name: str, texts: list[str], kind: str) -> np.ndarray:
        st = SentenceTransformer(name, device=device).half()
        v = st.encode([_prefix(name, kind) + t for t in texts], batch_size=64,
                      normalize_embeddings=True, convert_to_numpy=True)  # fmt: skip
        return v.astype(np.float32)

    start = time.time()
    gv = enc(model, allg, "p")
    rate = len(allg) / (time.time() - start)
    sims = enc(model, q, "q") @ gv.T
    order = np.argsort(-sims, axis=1)[:, :1000]
    res: dict = {"model": model, "queries": len(q), "kjv_passages": len(g),
                 "distractors": len(dis), "passages_per_second": rate}  # fmt: skip
    for k in (1, 10, 100, 300, 1000):
        res[f"recall_at_{k}"] = float(np.mean([r in set(gref_a[o[:k]]) for o, r in
                                               zip(order, qref, strict=True)]))  # fmt: skip
    if rescore:
        cand = np.unique(order.ravel())
        ev = dict(zip(cand.tolist(), enc(rescore, [allg[i] for i in cand], "p"), strict=True))
        qe = enc(rescore, q, "q")
        for k in (10, 100, 300, 1000):
            h1 = h10 = 0
            for i, r in enumerate(qref):
                c = order[i, :k]
                top = c[np.argsort(-(np.array([ev[j] for j in c]) @ qe[i]))[:10]]
                h1 += gref_a[top[0]] == r
                h10 += r in set(gref_a[top])
            res[f"rescore_{k}"] = {"model": rescore, "recall_at_1": h1 / len(q),
                                   "recall_at_10": h10 / len(q)}  # fmt: skip
    out = OUT.parent / f"distractors_{model.split('/')[-1]}.json"
    out.write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    import torch

    from metadata.config import stamp

    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("distractors")
    d.add_argument("model")
    d.add_argument("--n", type=int, default=1_000_000)
    d.add_argument("--rescore")
    a = ap.parse_args(argv)
    if a.cmd == "distractors":
        return distractors(a.model, a.n, a.rescore)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    data = test_set()
    print(f"{len(data[0])} queries, {len(data[2])} gallery passages, device {device}", flush=True)
    out = {"test": __doc__.split("\n\n")[1], "passage_words": PASSAGE_WORDS, "device": device,
           "queries": len(data[0]), "gallery": len(data[2]), "models": {}}  # fmt: skip
    for m in MODELS:
        r = score(m, data, device)
        out["models"][m] = r
        print(f"{m}: R@1 {r['recall_at_1']:.3f}  R@10 {r['recall_at_10']:.3f}  "
              f"{r['passages_per_second']:.0f}/s", flush=True)  # fmt: skip
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
