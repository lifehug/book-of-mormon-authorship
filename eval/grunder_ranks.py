"""Where the sources critics have proposed rank in our borrowing searches (BOM-33/BOM-42).

**Exploratory check, not pre-registered** (2026-11-06, after Grunder's *Mormon Parallels* was
bought). Rick Grunder's bibliography lists 500 texts proposed as parallels to the Book of Mormon;
``data/access/grunder_sources.csv`` matched 139 of them to our catalog by author and title (32
more by title only, reported apart). This reads the searches already run, no new search:

- **Paraphrase search** (BOM-25, ``data/semantic/corpus_bom.json``): each source's score and its
  percentile against 500 genre- and length-matched volumes, so the percentile already adjusts for
  the kind and size of book. Proposed volumes are compared with every other ranked volume by a
  rank-sum test on that percentile, and by the share that stands out (Fisher's exact test).
- **Rare phrases** (BOM-24, ``data/reuse/bom/rare.json``): rank where a proposed volume is in the
  stored top 100 or named list (only those are stored; the rest are not ranked here).
- **Exact reuse** (BOM-23, ``data/reuse/exact/sources/bom_full.json``): listed or not.
- **Story skeleton** (BOM-25, ``data/semantic/skeleton/top.json``): scored or not, with its order p.

Writes names and numbers only: ``data/semantic/grunder_ranks.json``.

Usage::

    python -m eval.grunder_ranks
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu

from metadata.config import stamp

GRUNDER = Path("data/access/grunder_sources.csv")
CORPUS = Path("data/semantic/corpus_bom.json")
RARE = Path("data/reuse/bom/rare.json")
EXACT = Path("data/reuse/exact/sources/bom_full.json")
SKELETON = Path("data/semantic/skeleton/top.json")
OUT = Path("data/semantic/grunder_ranks.json")


def entries(path: Path = GRUNDER) -> list[dict]:
    """Grunder entries matched to the catalog: entry, author, title, year, basis, volume ids."""
    out = []
    for r in csv.DictReader(path.open()):
        if r["catalog_match"] == "none" or not r["catalog_work_ids"].strip():
            continue
        out.append({"entry": r["entry"], "author": r["author"].strip(), "title": r["title"][:100],
                    "year": r["edition_year"], "basis": r["match_basis"],
                    "work_ids": r["catalog_work_ids"].split()})  # fmt: skip
    return out


def compare(proposed: list[dict], others: list[dict]) -> dict:
    """Percentile rank-sum test and stand-out rate, proposed volumes against all other volumes."""
    a = np.array([r["percentile"] for r in proposed if r["percentile"] is not None])
    b = np.array([r["percentile"] for r in others if r["percentile"] is not None])
    sa, sb = sum(r["stands_out"] for r in proposed), sum(r["stands_out"] for r in others)
    out = {"proposed_volumes": len(a), "other_volumes": len(b),
           "median_percentile": {"proposed": float(np.median(a)) if len(a) else None,
                                 "others": float(np.median(b)) if len(b) else None},
           "stand_out": {"proposed": [sa, len(proposed)], "others": [sb, len(others)]}}  # fmt: skip
    if len(a) and len(b):
        u = mannwhitneyu(a, b, alternative="greater")
        out["rank_sum_greater_p"] = float(u.pvalue)
        out["auc"] = float(u.statistic / (len(a) * len(b)))  # P(proposed > other)
        odds, p = fisher_exact([[sa, len(proposed) - sa], [sb, len(others) - sb]],
                               alternative="greater")  # fmt: skip
        out["stand_out_odds_ratio"], out["stand_out_greater_p"] = float(odds), float(p)
    return out


def run() -> int:
    ranking = {r["work_id"]: r for r in json.loads(CORPUS.read_text())["ranking"]}
    rare = json.loads(RARE.read_text())
    rare_rank = {r["work_id"]: r["rank"] for r in rare["top"]}
    rare_rank |= {v["work_id"]: v.get("rank") for v in rare["named"].values() if v.get("work_id")}
    exact = {v["work_id"] for v in json.loads(EXACT.read_text())["volumes"]}
    skel = {s["id"]: s for s in json.loads(SKELETON.read_text())["sources"]}
    es = entries()
    firm = [e for e in es if e["basis"] == "author+title"]
    proposed_ids = {w for e in es for w in e["work_ids"]}
    firm_ids = {w for e in firm for w in e["work_ids"]}
    rows = []
    for e in es:
        vols = [ranking[w] for w in e["work_ids"] if w in ranking]
        best = max(vols, key=lambda r: (r["percentile"] or 0, -r["rank"])) if vols else None
        rr = [rare_rank[w] for w in e["work_ids"] if w in rare_rank and rare_rank[w]]
        sk = [skel[w] for w in e["work_ids"] if w in skel]
        rows.append({**{k: e[k] for k in ("entry", "author", "title", "year", "basis")},
                     "volumes": len(e["work_ids"]), "ranked_volumes": len(vols),
                     "best": None if best is None else {
                         k: best[k] for k in ("work_id", "rank", "score", "percentile",
                                              "stands_out", "genre", "words")},
                     "rare_rank": min(rr) if rr else None,
                     "exact_reuse": any(w in exact for w in e["work_ids"]),
                     "skeleton_order_p": min(s["order_p"] for s in sk) if sk
                     else None})  # fmt: skip
    in_firm = [r for w, r in ranking.items() if w in firm_ids]
    not_proposed = [r for w, r in ranking.items() if w not in proposed_ids]
    by_genre = {}
    for g in sorted({r["genre"] for r in in_firm}):
        a = [r for r in in_firm if r["genre"] == g]
        b = [r for r in not_proposed if r["genre"] == g]
        if len(a) >= 5:
            by_genre[g] = compare(a, b)
    ranked = sorted((r for r in rows if r["best"] and r["basis"] == "author+title"),
                    key=lambda r: r["best"]["rank"])  # fmt: skip
    doc = {**stamp(), "note": "exploratory check, not pre-registered",
           "entries_matched": len(es), "entries_firm": len(firm),
           "firm_entries_in_paraphrase_ranking": sum(1 for r in rows if r["best"]
                                                     and r["basis"] == "author+title"),
           "ranked_sources": len(ranking),
           "paraphrase_firm_vs_unproposed": compare(in_firm, not_proposed),
           "paraphrase_by_genre": by_genre,
           "rare_top100_or_named": sorted((r["rare_rank"], r["entry"]) for r in rows
                                          if r["rare_rank"]),
           "exact_reuse_entries": [r["entry"] for r in rows if r["exact_reuse"]],
           "skeleton_entries": [(r["entry"], r["skeleton_order_p"]) for r in rows
                                if r["skeleton_order_p"] is not None],
           "top20": ranked[:20], "entries": rows}  # fmt: skip
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    c = doc["paraphrase_firm_vs_unproposed"]
    print(f"{len(firm)} firm entries ({doc['firm_entries_in_paraphrase_ranking']} with a ranked "
          f"volume); proposed volumes median percentile {c['median_percentile']['proposed']} vs "
          f"{c['median_percentile']['others']}; AUC {c.get('auc')}, rank-sum p "
          f"{c.get('rank_sum_greater_p')}; stand out {c['stand_out']} -> {OUT}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
