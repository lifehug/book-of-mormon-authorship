"""The enlarged benchmark's corpus-author tasks (BOM-75; Amendment 48; ``docs/part2-plan.md``).

Part 1's benchmark had 110 held-out tests, too few to tell a 9% false-match rate from 5%. This adds
four tasks of 1780-1830 corpus authors, one per genre, drawn by the rule fixed in Amendment 48
before any draw or scoring:

* **Pool:** ``classic.corpus_run.eligible`` (personal authors, 1780-1830, at least four distinct
  works of 15,000+ words, OCR passed, duplicates removed, no candidate), less benchmark authors,
  pseudo-biblical control and placebo authors (BOM-76), and authors of sealed works.
* **Genre:** the first ``genre.parquet`` label held by more than half of an author's eligible works;
  no majority, or a periodical / uncertain / other majority, leaves the author out.
* **Draw:** ``part2_benchmark.authors_per_genre`` per genre, seeded, among authors with
  ``min_author_words``; text capped at ``max_author_words``, works in catalog order.

``select`` writes the draw to ``data/benchmark/part2/authors.json`` (names, work ids and word
counts; never text). ``alm.benchmark --part2`` and ``eval.benchmark --part2`` add the tasks
(``p2_<genre>``) to the original three and score all seven.

Usage::

    python -m eval.part2_benchmark      # draw -> data/benchmark/part2/authors.json (seconds)
    python -m eval.part2_benchmark --ext --queue 20   # Amendment 56: next authors to screen
    python -m eval.part2_benchmark --ext              # Amendment 56's draw -> authors_ext.json
"""

from __future__ import annotations

import json
import random
import sys
import zlib
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from classic.corpus_run import CATALOG, SIGS  # as eligible() reads them
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/benchmark/part2/authors.json")
# Benchmark authors outside the catalog (the Federalist comes from Project Gutenberg) and the
# BOM-76 placebo writers named in its issue, matched on the catalog's "Surname, Forename" form.
NAMED = (
    "hamilton, alexander", "madison, james", "jay, john", "ilive, jacob", "leacock, john",
    "southcott, joanna", "brothers, richard", "snowden, richard", "blake, william",
)  # fmt: skip


def _authors_of(work_ids: set[str], meta: dict[str, dict]) -> set[str]:
    return {(meta[w]["author_norm"] or "").lower() for w in work_ids if w in meta} - {""}


def excluded_authors(meta: dict[str, dict]) -> set[str]:
    """Benchmark, pseudo-biblical control, placebo and sealed-work authors (lower case)."""
    from metadata.sealed import sealed_ids

    ids: set[str] = set(sealed_ids())
    spec = json.loads(Path("data/benchmark/pseudo_biblical_known.json").read_text())["authors"]
    ids |= {w for a in spec.values() for w in a["works"]}
    d = json.loads(Path("data/benchmark/tasks.json").read_text())["dictated"]
    ids |= set(d["tests"]) | {w for ws in d["reference"].values() for w in ws}
    for name in ("pseudo_biblical_primary", "pseudo_biblical", "pseudo_biblical_curated"):
        ids |= set(Path(f"data/controls/{name}.txt").read_text().split())
    return _authors_of(ids, meta) | set(NAMED)


def _blocked(author: str, blocked: set[str]) -> bool:
    a = author.lower()
    return a in blocked or any(a.startswith(b) for b in NAMED)


def _shingles(words: list[str], n: int, mod: int) -> set[int]:
    """A fixed sample (hash % mod == 0) of the work's n-word sequences, lower case."""
    low = [w.lower() for w in words]
    out = set()
    for i in range(len(low) - n + 1):
        h = zlib.crc32(" ".join(low[i : i + n]).encode())
        if h % mod == 0:
            out.add(h)
    return out


def distinct_works(work_ids: list[str], cfg: dict) -> tuple[list[str], list[str]]:
    """Works largest first, dropping any whose sampled n-grams are more than ``dup_share`` in a
    kept work (another edition, a reprint, or a piece inside a collected works). Kept works are
    returned in catalog order. (kept, dropped)."""
    from alm.benchmark import _words

    p2 = cfg["part2_benchmark"]
    got = _words(work_ids, [])
    seen: set[int] = set()
    kept, dropped = [], []
    for w in sorted(work_ids, key=lambda x: (-len(got[x]), x)):
        sh = _shingles(got[w], p2["dup_ngram"], p2["dup_sample_mod"])
        if sh and len(sh & seen) > p2["dup_share"] * len(sh):
            dropped.append(w)
            continue
        kept.append(w)
        seen |= sh
    return sorted(kept), sorted(dropped)


def _pools(cfg: dict) -> tuple[dict[str, list[dict]], Counter, dict[str, int]]:
    """Each genre's eligible authors after the automatic rules; reasons left out; word counts."""
    from classic.corpus_run import eligible

    p2 = cfg["part2_benchmark"]
    cols = ["work_id", "author_norm", "title"]
    meta = {r["work_id"]: r for r in pq.read_table(CATALOG, columns=cols).to_pylist()}
    gen = pq.read_table("data/catalog/genre.parquet", columns=["work_id", "genre"])
    genre = {r["work_id"]: (r["genre"] or "").split(",")[0] for r in gen.to_pylist()}
    words: dict[str, int] = {}
    for f in SIGS.glob("*.parquet"):
        for r in pq.read_table(f, columns=["work_id", "words"]).to_pylist():
            words[r["work_id"]] = r["words"]
    blocked = excluded_authors(meta)
    pat = p2["translation_title"]
    by_genre: dict[str, list[dict]] = {g: [] for g in p2["genres"]}
    counts: Counter = Counter()
    for author, works in sorted(eligible(cfg).items()):
        if _blocked(author, blocked):
            counts["excluded"] += 1
            continue
        if any(pat in (meta[w["work_id"]]["title"] or "").lower() for w in works):
            counts["translated from another language"] += 1
            continue
        top, n = Counter(genre.get(w["work_id"], "uncertain") for w in works).most_common(1)[0]
        if n <= p2["genre_majority"] * len(works) or top in p2["exclude_genres"]:
            counts["no genre majority"] += 1
            continue
        total = sum(words.get(w["work_id"], 0) for w in works)
        if top not in by_genre or total < p2["min_author_words"]:
            counts["other genre or too short"] += 1
            continue
        ids = sorted(w["work_id"] for w in works)
        by_genre[top].append({"author": author, "works": ids, "words": total})
    return by_genre, counts, words


def _order(pool: list[dict], g: str, cfg: dict) -> list[dict]:
    order = list(pool)
    random.Random(derive_seed(f"{cfg['part2_benchmark']['seed']}:{g}", cfg)).shuffle(order)
    return order


def _seen() -> set[str]:
    """Authors Amendment 48's draw already took or skipped (Amendment 56 continues past them)."""
    d = json.loads(OUT.read_text())
    return {r["author"] for k in ("drawn", "skipped") for rows in d[k].values() for r in rows}


def select(cfg: dict, ext: bool = False) -> dict:
    """Amendment 48's draw: seeded order, automatic rules, then the recorded screen; ``ext``
    continues each genre's order past round one for Amendment 56's extension."""
    p2 = cfg["part2_benchmark"]
    per = p2["extension"]["authors_per_genre"] if ext else p2["authors_per_genre"]
    seen = _seen() if ext else set()
    min_works = cfg["classic"]["corpus_run"]["min_works"]
    by_genre, counts, words = _pools(cfg)
    sp = Path(p2["screen"])
    screen = json.loads(sp.read_text())["authors"] if sp.exists() else {}
    drawn: dict[str, list] = {}
    skipped: dict[str, list] = {}
    pending: dict[str, list] = {}
    for g, pool in by_genre.items():
        drawn[g], skipped[g], pending[g] = [], [], []
        for cand in _order(pool, g, cfg):
            if len(drawn[g]) >= per:
                break
            if cand["author"] in seen:
                continue
            sc = screen.get(cand["author"])
            if sc is None:
                pending[g].append(cand["author"])
                break  # the draw stops at the first author not yet screened
            if sc["decision"] == "reject":
                skipped[g].append({"author": cand["author"], "screen": sc["reason"]})
                continue
            works = [w for w in cand["works"] if w not in sc.get("drop_works", {})]
            kept, dropped = distinct_works(works, cfg)
            total = sum(words.get(w, 0) for w in kept)
            if len(kept) < min_works or total < p2["min_author_words"]:
                skipped[g].append({"author": cand["author"], "screen": "under the floor after "
                                   f"repeats ({len(kept)} works, {total:,} words)"})  # fmt: skip
                continue
            drawn[g].append({"author": cand["author"], "works": kept, "words": total,
                             "repeats_dropped": dropped,
                             "screen_dropped": sc.get("drop_works", {})})  # fmt: skip
        if not ext:
            drawn[g].sort(key=lambda r: r["author"])
    return {"eligible_by_genre": {g: len(v) for g, v in by_genre.items()},
            "left_out": dict(counts), "skipped": skipped, "awaiting_screen": pending,
            "drawn": drawn}  # fmt: skip


def queue(cfg: dict, n: int, ext: bool = False) -> None:
    """The first ``n`` authors of each genre's seeded order (with ``ext``, past round one), works
    after the automatic repeat check, with titles and years: the list the screen is decided on."""
    cols = ["work_id", "title", "year"]
    meta = {r["work_id"]: r for r in pq.read_table(CATALOG, columns=cols).to_pylist()}
    by_genre, _, words = _pools(cfg)
    seen = _seen() if ext else set()
    for g, pool in by_genre.items():
        print(f"== {g}")
        for cand in [c for c in _order(pool, g, cfg) if c["author"] not in seen][:n]:
            kept, dropped = distinct_works(cand["works"], cfg)
            total = sum(words.get(w, 0) for w in kept)
            print(f"  {cand['author']} ({total:,} words kept; repeats dropped {len(dropped)})")
            for w in kept:
                print(f"      {w} {meta[w]['year']} {(meta[w]['title'] or '')[:100]}")


def ext_tasks(cfg: dict) -> dict[str, list[dict]]:
    """Amendment 56: {p3_<genre>_<k>: drawn authors}, the first 4 kept in a genre's order in task
    1, the next 4 in task 2."""
    e = cfg["part2_benchmark"]["extension"]
    drawn = json.loads(Path(e["out"]).read_text())["drawn"]
    k = e["authors_per_genre"] // e["tasks_per_genre"]
    return {f"p3_{g}_{i + 1}": rows[i * k : (i + 1) * k]
            for g, rows in drawn.items() for i in range(e["tasks_per_genre"])}  # fmt: skip


def corpus_works(cfg: dict, ext: bool = False) -> dict[str, dict[str, list[list[str]]]]:
    """{p2_<genre>: {author: [original words per work]}}, capped at ``max_author_words``; with
    ``ext``, Amendment 56's {p3_<genre>_<k>: ...} instead."""
    from alm.benchmark import _words

    if ext:
        groups = ext_tasks(cfg)
    else:
        groups = {f"p2_{g}": rows for g, rows in json.loads(OUT.read_text())["drawn"].items()}
    cap = cfg["part2_benchmark"]["max_author_words"]
    out: dict[str, dict[str, list[list[str]]]] = {}
    for name, authors in groups.items():
        task = out.setdefault(name, {})
        for a in authors:
            got = _words(a["works"], [])
            kept, used = [], 0
            for w in a["works"]:
                if used >= cap:
                    break
                kept.append(got[w][: cap - used])
                used += len(kept[-1])
            task[a["author"]] = kept
    return out


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    cfg = load_config()
    ext = "--ext" in argv
    argv = [a for a in argv if a != "--ext"]
    if argv[:1] == ["--queue"]:
        queue(cfg, int(argv[1]) if len(argv) > 1 else 8, ext)
        return 0
    res = select(cfg, ext)
    out = Path(cfg["part2_benchmark"]["extension"]["out"]) if ext else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
    print(f"eligible per genre {res['eligible_by_genre']}; left out {res['left_out']}")
    for g, rows in res["drawn"].items():
        print(f"  {g}: " + "; ".join(f"{r['author']} ({r['words']:,} words, {len(r['works'])} "
                                       f"works)" for r in rows))  # fmt: skip
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
