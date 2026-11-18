"""The lab's one door to the corpus: list, read and search every work, under a named rule set.

Every command takes ``--view`` (a rule set from ``lab.views``; see ``python -m lab.registry
views``) and the same filters (``--author``, ``--title``, ``--year 1820-1829``, ``--genre``). The
door only reads. Each call is logged to ``logs/lab/queries.jsonl``; ``--save NAME`` also writes
what was shown to the private repository (``data/private/lab/<user>/NAME.md``), the only place a
result that quotes text may be kept.

Usage::

    python -m lab.door works --author "wroe, john"              # what do we hold?
    python -m lab.door read WORK_ID [--passage 12] [--count 3]   # read a work, or passages of it
    python -m lab.door find "a people led across the sea" --question --year 1800-1830
    python -m lab.door find --file passage.txt --view work-search   # nearest passages to a text
    python -m lab.door phrase "curious workmanship" --genre sermon_devotional
"""

from __future__ import annotations

import argparse
import getpass
import json
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq

from lab import registry
from lab.paths import LOGS, NOTES, out
from metadata.config import load as load_config

CATALOG = Path("data/catalog/catalog.parquet")
DEFAULT_VIEW = {"works": "everything", "read": "everything", "find": "borrowing",
                "phrase": "readable"}  # fmt: skip


def catalog(ids: set[str] | None = None) -> dict[str, dict]:
    """Catalog rows by work id (all of them, or the given ones)."""
    cols = ["work_id", "source", "source_id", "title", "author", "author_norm", "text_path"]
    t = pq.read_table(CATALOG, columns=cols)
    return {r["work_id"]: r for r in t.to_pylist() if ids is None or r["work_id"] in ids}


def chosen(a: argparse.Namespace, cfg: dict) -> list[dict]:
    """Registry rows of the rule set that pass the filters, each with its catalog fields."""
    rows = registry.view(a.view, cfg).to_pylist()
    lo, hi = map(int, a.year.split("-")) if a.year else (None, None)
    if a.year:
        rows = [r for r in rows if r["year"] is not None and lo <= r["year"] <= hi]
    if a.genre:
        rows = [r for r in rows if r["genre"] == a.genre]
    cat = catalog({r["work_id"] for r in rows})
    rows = [{**cat[r["work_id"]], **r} for r in rows]
    for field, want in (("author_norm", a.author), ("title", a.title)):
        if want:
            rows = [r for r in rows if want.lower() in (r[field] or "").lower()]
    return rows


def label(r: dict) -> str:
    return (f"{r['work_id']}  {r['year'] or 'n.d.'}  {(r['author'] or 'anon.')[:40]}  "
            f"{' '.join((r['title'] or '').split())[:70]}")  # fmt: skip


def text_of(row: dict) -> str:
    from ocr_fix.normalize import norm_path

    return norm_path(row).read_text(encoding="utf-8", errors="replace")


def works(a: argparse.Namespace, cfg: dict) -> list[str]:
    rows = chosen(a, cfg)
    lines = [f"{len(rows):,} works in rule set `{a.view}` after filters"]
    for r in rows[: a.limit]:
        marks = {"no text": not r["has_text"], "duplicate": not r["dup_keeper"],
                 "not in meaning index": not r["in_passage_index"]}  # fmt: skip
        flags = [k for k, on in marks.items() if on]
        lines.append(f"{label(r)}  [{r['genre']}; {r['words'] or 0:,} words"
                     + (f"; {', '.join(flags)}" if flags else "") + "]")  # fmt: skip
    return lines


def read(a: argparse.Namespace, cfg: dict) -> list[str]:
    from semantic.index import spans

    row = catalog({a.work_id}).get(a.work_id)
    if row is None or not row["text_path"]:
        raise SystemExit(f"{a.work_id}: not in the catalog, or no text on disk")
    t = registry.load()
    reg = t.filter(pc.equal(t["work_id"], a.work_id)).to_pylist()[0]
    text = text_of(row)
    s = cfg["semantic"]
    sp = spans(text, s["passage_words"], s["min_passage_words"])
    head = [label({**row, **reg}), f"{len(sp):,} passages of {s['passage_words']} words"]
    if a.passage is None:
        return head + [" ".join(text.split()[: a.count * s["passage_words"]])]
    body = []
    for i in range(a.passage, min(a.passage + a.count, len(sp))):
        body += [f"[passage {i}]", " ".join(text[sp[i][0] : sp[i][1]].split())]
    return head + body


def find(a: argparse.Namespace, cfg: dict) -> list[str]:
    from lab.passages import search

    query = Path(a.file).read_text() if a.file else a.text
    if not query:
        raise SystemExit("give a text to search for, or --file")
    rows = {r["work_id"]: r for r in chosen(a, cfg)}
    hits = search([query], set(rows), a.top or cfg["lab"]["top"], a.question, cfg)[0]
    lines = [f"nearest passages among {len(rows):,} works (rule set `{a.view}`); "
             "score 1.0 = same meaning, about 0.6 = same topic"]  # fmt: skip
    for h in hits:
        r = rows[h["work_id"]]
        passage = " ".join(text_of(r)[h["char_begin"] : h["char_end"]].split())
        lines += ["", f"{h['score']:.3f}  {label(r)}  passage {h['passage']}", passage]
    return lines


def _scan(job: tuple[dict, str, int]) -> list[tuple[str, int, str]]:
    row, pattern, context = job
    try:
        text = text_of(row)
    except OSError:
        return []
    return [(row["work_id"], m.start(),
             " ".join(text[max(0, m.start() - context) : m.end() + context].split()))
            for m in re.finditer(pattern, text, flags=re.IGNORECASE)]  # fmt: skip


def phrase(a: argparse.Namespace, cfg: dict) -> list[str]:
    lab = cfg["lab"]
    rows = [r for r in chosen(a, cfg) if r["has_text"]]
    if len(rows) > lab["phrase_max_works"] and not a.all:
        raise SystemExit(f"{len(rows):,} works to read: narrow with --year, --genre or --author, "
                         "or pass --all (every text is read; that can take hours)")  # fmt: skip
    pattern = r"\s+".join(map(re.escape, a.text.split()))
    by = {r["work_id"]: r for r in rows}
    jobs = [(r, pattern, lab["phrase_context"]) for r in rows]
    with ProcessPoolExecutor(lab["phrase_workers"]) as pool:
        found = [h for hs in pool.map(_scan, jobs, chunksize=64) for h in hs]
    n_works = len({w for w, _, _ in found})
    lines = [f"{len(found):,} occurrences of “{a.text}” in {n_works:,} of {len(rows):,} works "
             f"(rule set `{a.view}`)"]  # fmt: skip
    for w, at, around in found[: a.limit]:
        lines += ["", f"{label(by[w])}  at character {at:,}", around]
    return lines


def log(a: argparse.Namespace, shown: int, seconds: float) -> None:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "who": getpass.getuser(),
           "seconds": round(seconds, 1), "lines": shown,
           **{k: v for k, v in vars(a).items() if v not in (None, False)}}  # fmt: skip
    with out(LOGS / "queries.jsonl").open("a") as f:
        f.write(json.dumps(rec) + "\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["works", "read", "find", "phrase"])
    ap.add_argument("text", nargs="?", help="a work id (read), a query (find) or a phrase")
    ap.add_argument("--view", help="rule set (python -m lab.registry views)")
    ap.add_argument("--author", help="part of the catalogued author name, surname first")
    ap.add_argument("--title", help="part of the title")
    ap.add_argument("--year", help="a range of years, e.g. 1820-1829")
    ap.add_argument("--genre")
    ap.add_argument("--limit", type=int, default=50, help="rows shown (works, phrase)")
    ap.add_argument("--top", type=int, help="passages shown (find)")
    ap.add_argument(
        "--question", action="store_true", help="the query is a question, not a passage"
    )
    ap.add_argument("--file", help="read the query text from a file (find)")
    ap.add_argument("--passage", type=int, help="first passage to show (read)")
    ap.add_argument("--count", type=int, default=3, help="passages to show (read)")
    ap.add_argument("--all", action="store_true", help="allow a phrase scan of any size")
    ap.add_argument("--save", help="also write the output to data/private/lab/<user>/NAME.md")
    a = ap.parse_args(argv)
    a.view = a.view or DEFAULT_VIEW[a.command]
    a.work_id = a.text
    cfg, t0 = load_config(), time.time()
    lines = {"works": works, "read": read, "find": find, "phrase": phrase}[a.command](a, cfg)
    print("\n".join(lines))
    log(a, len(lines), time.time() - t0)
    if a.save:
        head = f"<!-- python -m lab.door {' '.join(argv or sys.argv[1:])} -->\n\n"
        path = NOTES / getpass.getuser() / f"{a.save}.md"
        out(path).write_text(head + "\n".join(lines) + "\n")
        print(f"\nsaved: {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
