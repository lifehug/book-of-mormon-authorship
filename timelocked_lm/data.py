"""The time-locked model's training set (BOM-27; pre-registration 5.2, Amendment 2).

Every volume the corpus searches use (``reuse.exact.eligible_any_year``: text, a date,
deduplication keepers, OCR exclusions applied, no newspapers) whose corrected year
(``metadata.dates.effective_year``, BOM-64) lies in the registered date range, less:

* **the Book of Mormon** (4.2): its catalogued copies (``metadata.sealed.sealed_ids``) and every
  volume holding ``metadata.sealed.MIN_SHARED`` or more of its 12-token original strings,
  whatever its date (the registered contamination check, run on every volume);
* **every text a model will later score**, so the base model has not already read what a
  perplexity ratio is computed on: all volumes by an author of the validation benchmark (BOM-21:
  the Federalist authors, the known imitation-scripture authors, Scott and his comparison
  novelists), all volumes by a named candidate (``data/candidates/sources.json``), and the
  known-answer texts with their own copies (BOM-61, ``reuse.exact.own_copies``).

``timelocked_lm.validation_share`` of the remaining volumes, chosen by a seeded hash, are held out
for validation loss. Writes ids, years and reasons only, no text.

Usage::

    python -m timelocked_lm.data select   # -> data/timelocked_lm/training_set.parquet, report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/timelocked_lm")
_ID = re.compile(r"\b(?:internet_archive|hathitrust|institutional_books|tcp):[^\"\s,\]]+")
BENCHMARK_FILES = ["data/benchmark/tasks.json", "data/benchmark/pseudo_biblical_known.json"]
FEDERALIST_AUTHORS = {"hamilton, alexander", "madison, james", "jay, john"}
GENERIC_AUTHORS = {"", "various", "anonymous", "anon"}  # not an author: never matched on


def _ids_in(path: str) -> set[str]:
    return set(_ID.findall(Path(path).read_text()))


def _author_key(name: str) -> str:
    """ "Gilbert J. Hunt" -> "hunt, gilbert" (catalog ``author_norm`` prefix)."""
    parts = name.replace(".", " ").split()
    return f"{parts[-1].lower()}, {parts[0].lower()}"


def exclusions(rows: list[dict]) -> dict[str, str]:
    """work id -> reason, for the texts a model will later score."""
    from reuse.exact import own_copies

    rows = [{**r, "author_norm": None if (r["author_norm"] or "") in GENERIC_AUTHORS
             else r["author_norm"]} for r in rows]  # fmt: skip
    by_id = {r["work_id"]: r for r in rows}
    out: dict[str, str] = {}
    bench = set().union(*(_ids_in(p) for p in BENCHMARK_FILES))
    authors = {by_id[w]["author_norm"] for w in bench if w in by_id and by_id[w]["author_norm"]}
    for r in rows:
        a = r["author_norm"] or ""
        if r["work_id"] in bench or a in authors or a in FEDERALIST_AUTHORS:
            out[r["work_id"]] = "benchmark author"
    cands = {_author_key(e["candidate"])
             for e in json.loads(Path("data/candidates/sources.json").read_text())}  # fmt: skip
    for r in rows:
        if (r["author_norm"] or "").startswith(tuple(cands)):
            out.setdefault(r["work_id"], "candidate author")
    for ln in Path("data/known_answer/set.jsonl").read_text().splitlines():
        t = json.loads(ln)
        ids = [v["work_id"] for v in t["volumes"]]
        for w in own_copies(t["key"], {"ids": ids}, rows):
            out.setdefault(w, f"known-answer text ({t['key']})")
    return out


def _held_out(work_id: str, salt: int, share: float) -> bool:
    h = hashlib.sha256(f"{salt}:{work_id}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64 < share


def select(workers: int) -> int:
    from metadata.sealed import MIN_SHARED, sealed_ids
    from reuse.exact import eligible_any_year
    from reuse.rare import seal_check

    cfg = load_config()
    t = cfg["timelocked_lm"]
    lo, hi = cfg["corpus"]["date_range"]
    rows = [r for r in eligible_any_year(cfg) if lo <= r["year"] <= hi]
    seal = seal_check([r["work_id"] for r in rows], workers)
    sealed = sealed_ids()
    reason = exclusions(rows)
    for r in rows:
        w = r["work_id"]
        if w in sealed:
            reason[w] = "Book of Mormon copy"
        elif seal.get(w, 0) >= MIN_SHARED:
            reason[w] = f"Book of Mormon strings ({seal[w]})"
        elif seal.get(w, 0) < 0:
            reason.setdefault(w, "text unreadable")
    salt = derive_seed(t["validation_seed"], cfg)
    keep = [r for r in rows if r["work_id"] not in reason]
    table = pa.table({
        "work_id": [r["work_id"] for r in keep],
        "source": [r["source"] for r in keep],
        "year": pa.array([r["year"] for r in keep], pa.int16()),
        "split": ["validation" if _held_out(r["work_id"], salt, t["validation_share"]) else "train"
                  for r in keep],
    })  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, OUT / "training_set.parquet")
    near = Counter(min(seal.get(r["work_id"], 0), MIN_SHARED) for r in keep)
    report = {
        "eligible_in_range": len(rows),
        "excluded": dict(Counter(v.split(" (")[0] for v in reason.values()).most_common()),
        "excluded_ids": dict(sorted(reason.items())),
        "kept": len(keep),
        "split": dict(Counter(table.column("split").to_pylist())),
        "by_source": dict(Counter(r["source"] for r in keep).most_common()),
        "kept_by_shared_bom_strings": {str(k): v for k, v in sorted(near.items())},
        "contamination_clean": all(seal.get(r["work_id"], 0) < MIN_SHARED for r in keep),
    }
    (OUT / "selection.json").write_text(json.dumps({**stamp(), **report}, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "excluded_ids"}, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    return select(a.workers)


if __name__ == "__main__":
    sys.exit(main())
