"""Semantic parallels (BOM-25; plan ``docs/semantic-plan.md``, Amendment 14).

A query passage is 128 words of the target's full text, labelled with the share of its words
inside BOM-16's King James spans. Its own bar is the highest similarity it reaches among
``semantic.null_passages`` random passages from the target's date window; a passage of another
text is a **parallel** when the query's similarity to it is above that bar. A source's score is
the number of the target's scored query passages (King James share at most
``semantic.max_query_kjv_share``) with a parallel in it, per 10,000 words of those passages.

``named`` scores the named proposed sources against the Book of Mormon directly (every passage
pair, no index) and ranks each within its registered control group. The whole-corpus search
reads the index and follows once it is built.

Usage::

    python -m semantic.search named   # -> data/semantic/named.json
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

OUT = Path("data/semantic")
CANDIDATES = Path("data/candidates")
CURATED = Path("data/controls/pseudo_biblical_curated.txt")
HISTORY = Path("data/controls/history.jsonl")
# the named proposed sources not in a control list, by candidate file: the cleaned text where the
# project made one, else the OCR as fetched (the 1825 View of the Hebrews is kept as a witness)
NAMED = {
    "the_late_war_1816": ("pseudo_biblical", "clean/gh-1816-late-war.txt"),
    "view_of_the_hebrews_1823": ("origins", "clean/es-1823-view-of-the-hebrews.txt"),
    "view_of_the_hebrews_1825": ("origins", "text/es-1825-view-of-the-hebrews.txt"),
    "spalding_manuscript_story": ("origins", "clean/ss-manuscript-story-1885.txt"),
}
NAPOLEON = "institutional_books:HH2NE7"  # in the curated list; ranked among the other 17


def bom_queries(n: int) -> list[dict]:
    """The 1830 text cut into ``n``-word passages, each with its King James share (BOM-16)."""
    spans: dict[str, list[dict]] = {}
    for ln in Path("data/kjv_mask/bom/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    words: list[tuple[str, bool]] = []
    for ln in Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if not r["book"]:
            continue
        sp = spans.get(f"bom:{r['seq']}", [])
        pos = 0
        for w in r["text"].split():
            start = r["text"].index(w, pos)
            pos = start + len(w)
            words.append((w, any(s["start"] <= start < s["end"] for s in sp)))
    out = []
    for i in range(0, len(words), n):
        part = words[i : i + n]
        out.append({"text": " ".join(w for w, _ in part), "words": len(part),
                    "kjv_share": sum(k for _, k in part) / len(part)})  # fmt: skip
    return out


def text_passages(text: str, cfg: dict) -> list[str]:
    from semantic.index import spans

    s = cfg["semantic"]
    return [" ".join(text[a:b].split()) for a, b, _ in
            spans(text, s["passage_words"], s["min_passage_words"])]  # fmt: skip


def null_passages(key: str, lo: int, hi: int, exclude: set[str], cfg: dict) -> list[str]:
    """``semantic.null_passages`` passages drawn at random from volumes dated ``lo``-``hi``:
    a random volume, then a random passage of it, with a seed derived from the target's key."""
    from ocr_fix.normalize import norm_path
    from reuse.exact import eligible_any_year

    rows = [r for r in eligible_any_year(cfg) if lo <= r["year"] <= hi
            and r["work_id"] not in exclude]  # fmt: skip
    rng = random.Random(derive_seed(f"{cfg['semantic']['null_seed']}:{key}", cfg))
    out: list[str] = []
    while len(out) < cfg["semantic"]["null_passages"]:
        r = rng.choice(rows)
        try:
            text = Path(norm_path(r)).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        ps = text_passages(text, cfg)
        if ps:
            out.append(rng.choice(ps))
    return out


def _embed(model, texts: list[str], cfg: dict) -> np.ndarray:
    v = model.encode(texts, batch_size=cfg["semantic"]["batch_size"], normalize_embeddings=True,
                     convert_to_numpy=True, show_progress_bar=False)  # fmt: skip
    return v.astype(np.float32)


def control_groups() -> dict[str, dict[str, tuple[str, str]]]:
    """The registered control groups with the named sources in them: group -> id -> (title,
    text path)."""
    import pyarrow.parquet as pq

    from metadata.pseudo_biblical import CATALOG
    from ocr_fix.normalize import norm_path

    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist()}
    groups: dict[str, dict[str, tuple[str, str]]] = {"pseudo_biblical": {}, "origins": {}}
    for w in CURATED.read_text().split():
        if (cat[w]["author_norm"] or "").startswith("hunt, gilbert"):
            continue  # The Late War itself: scored once, from its cleaned text (NAMED)
        groups["pseudo_biblical"][w] = (cat[w]["title"] or "", str(norm_path(cat[w])))
    for ln in HISTORY.read_text().splitlines():
        r = json.loads(ln)
        if r["origins"]:
            w = r["work_id"]
            groups["origins"][w] = (cat[w]["title"] or "", str(norm_path(cat[w])))
    for key, (group, fname) in NAMED.items():
        groups[group][key] = (key, str(CANDIDATES / fname))
    return groups


def named() -> int:
    from metadata.sealed import sealed_ids
    from semantic.index import _model

    cfg = load_config()
    s = cfg["semantic"]
    lo, hi = cfg["corpus"]["date_range"]
    model = _model(cfg)
    queries = bom_queries(s["passage_words"])
    scored = np.array([q["kjv_share"] <= s["max_query_kjv_share"] for q in queries])
    scored_words = sum(q["words"] for q, k in zip(queries, scored, strict=True) if k)
    qv = _embed(model, [q["text"] for q in queries], cfg)
    nv = _embed(model, null_passages("bom", lo, hi, sealed_ids(), cfg), cfg)
    bar = (qv @ nv.T).max(axis=1)
    print(f"{len(queries)} query passages ({int(scored.sum())} scored); null of {len(nv)}",
          flush=True)  # fmt: skip

    groups = control_groups()
    rng = np.random.default_rng(derive_seed(s["bootstrap_seed"], cfg))
    boots = rng.integers(0, int(scored.sum()), (s["bootstrap"], int(scored.sum())))
    widx = np.flatnonzero(scored)
    qwords = np.array([q["words"] for q in queries])
    out: dict = {"queries": len(queries), "scored_queries": int(scored.sum()),
                 "scored_words": scored_words, "null_passages": len(nv), "groups": {}}  # fmt: skip
    for group, members in groups.items():
        rows = []
        for w, (title, path) in members.items():
            ps = text_passages(Path(path).read_text(encoding="utf-8", errors="replace"), cfg)
            if not ps:
                continue
            sim = qv @ _embed(model, ps, cfg).T
            hit = (sim > bar[:, None]).any(axis=1)
            best = sim.argmax(axis=1)
            sc = 10000 * hit[scored].sum() / scored_words
            h = hit[widx][boots]
            bw = qwords[widx][boots].sum(axis=1)
            bs = 10000 * h.sum(axis=1) / bw
            pairs = [{"query": int(i), "passage": int(best[i]), "score": float(sim[i, best[i]]),
                      "bar": float(bar[i]), "kjv_share": queries[i]["kjv_share"]}
                     for i in np.flatnonzero(hit & scored)]  # fmt: skip
            rows.append({"id": w, "title": title[:100], "passages": len(ps),
                         "parallels": int((hit & scored).sum()), "score": float(sc),
                         "score_ci95": [float(x) for x in np.percentile(bs, [2.5, 97.5])],
                         "pairs": sorted(pairs, key=lambda p: p["bar"] - p["score"])[:50],
                         })  # fmt: skip
            print(f"  {group}: {title[:50]}: {rows[-1]['parallels']} parallels, {sc:.2f}",
                  flush=True)  # fmt: skip
        rows.sort(key=lambda r: -r["score"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        out["groups"][group] = {"members": len(rows), "ranking": rows}
    named_ids = [*NAMED, NAPOLEON]
    out["named"] = {r["id"]: {"group": g, "rank": r["rank"], "of": v["members"],
                              "score": r["score"], "score_ci95": r["score_ci95"],
                              "parallels": r["parallels"]}
                    for g, v in out["groups"].items() for r in v["ranking"]
                    if r["id"] in named_ids}  # fmt: skip
    path = OUT / "named.json"
    path.write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    for k, v in out["named"].items():
        print(f"{k}: rank {v['rank']} of {v['of']} in {v['group']}, score {v['score']:.2f}")
    print(f"-> {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("named")
    ap.parse_args(argv)
    return named()


if __name__ == "__main__":
    sys.exit(main())
