"""Derived tables an outsider can check the results with, without the corpus (BOM-44).

The corpus cannot be redistributed (Harvard's and HathiTrust's terms, the Joseph Smith Papers'
copyright; ``docs/derived-data-terms.md``). What the analyses read can be: counts and hashes that
cannot be assembled back into a book. This writes them to ``data/corpus/derived/`` for release:

* ``benchmark_blocks.parquet`` -- the validation benchmark (BOM-21, 6.1) as the classical methods
  see it: every 1,000-token reference block, test sample and imposter-pool sample of every task,
  as counts over that task's 1,000 most frequent words (the registered MFW maximum). Burrows' and
  Cosine Delta, General Imposters and ENSC take only these counts, so the benchmark reruns from
  this table. ``benchmark_vocabulary.json`` holds the words; ``coverage`` in the report says how
  many of the benchmark's per-test vocabularies fall wholly inside them.
* ``rare_hits_bom.parquet``, ``rare_hits_known.parquet`` -- 5.5 and 6.5's rare-phrase inputs:
  for every scanned volume, its word count and the hashes of the target's 4-grams it contains
  (BOM-22, BOM-24; Amendment 9's known-answer scans). The hashes are of the target's own 4-grams
  (the Book of Mormon and public known-answer texts; ``target_grams_*.txt`` list each target's
  hashes, recomputable from its public text with ``reuse.rare.gram_ids``), so the table holds
  nothing of the scanned volume but which of the target's phrases it shares.

``check`` runs the non-reconstructability check on every table: no string column but ids and
labels, no position or order within a volume (block indexes are positions of 1,000-token bags,
not of words), vocabularies within the registered cap, counts as integers. Licence and
attribution notes go in ``README.md`` beside the tables.

Usage::

    python -m eval.derived export    # -> data/corpus/derived/
    python -m eval.derived check
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

OUT = Path("data/corpus/derived")
REPORT = Path("data/derived/export.json")
MAX_VOCAB = 1000  # the registered maximum MFW (5.1)
ALLOWED_STRINGS = {"task", "kind", "author", "work_id", "target"}
# A complete set of one text's 4-gram hashes can be unrolled back into that text (guess a phrase,
# test every next word against the hashes), so target hashes are published only for targets whose
# own text is from an open source; the others' rows and lists stay out.
RESTRICTED_SOURCES = {"institutional_books", "hathitrust"}
COPIES = {
    "rare_hits_bom.parquet": Path("data/reuse/bom/hits.parquet"),
    "rare_hits_known.parquet": Path("data/reuse/rare_known/hits.parquet"),
}


def benchmark(cfg: dict) -> dict:
    """Every benchmark document as word counts over its task's vocabulary."""
    from classic import build_vocabulary, word_counts
    from eval.benchmark import TASKS, imposter_pool, load_tasks
    from metadata.config import classic_kwargs

    kw = classic_kwargs(cfg)
    top_n = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    spec = json.loads(TASKS.read_text())
    tasks = load_tasks(cfg)
    rows, vocabs, coverage = [], {}, {}
    for name, task in tasks.items():
        pool = imposter_pool(task["pool_set"], set(spec[name].get("exclude_from_pool", [])), cfg,
                             task["pool_genre"], task["pool_exclude_authors"],
                             spec[name].get("imposter_fill"))  # fmt: skip
        # (kind, author, index, tokens, test span in the author's reference blocks)
        docs = [("reference", a, i, b, None) for a in sorted(task["authors"])
                for i, b in enumerate(task["authors"][a])]  # fmt: skip
        docs += [("test", a, i, t, sp) for i, (a, t, sp) in enumerate(task["tests"])]
        docs += [("pool", None, i, p, None) for i, p in enumerate(pool)]
        total = word_counts([w for d in docs for w in d[3]])
        vocab = [w for w, _ in total.most_common(MAX_VOCAB)]
        col = set(vocab)
        vocabs[name] = vocab
        # does every per-test vocabulary the benchmark builds fall inside the published one?
        names = sorted(task["authors"])
        inside = 0
        for a, _, span in task["tests"]:
            refs = [b for x in names for b in (task["authors"][x] if x != a or span is None else
                    task["authors"][x][: span[0]] + task["authors"][x][span[1] :])]  # fmt: skip
            v = build_vocabulary([word_counts(b) for b in refs], top_n=top_n,
                                 min_doc_fraction=kw["mfw_min_doc_fraction"])  # fmt: skip
            inside += set(v) <= col
        coverage[name] = {"tests": len(task["tests"]), "vocabulary_inside": inside}
        for kind, author, idx, toks, span in docs:
            c = word_counts(toks)
            rows.append({"task": name, "kind": kind, "author": author, "doc": idx,
                         "span_start": span[0] if span else None,
                         "span_end": span[1] if span else None, "tokens": len(toks),
                         "counts": [int(c.get(w, 0)) for w in vocab]})  # fmt: skip
    table = pa.table({
        "task": [r["task"] for r in rows], "kind": [r["kind"] for r in rows],
        "author": [r["author"] for r in rows],
        "doc": pa.array([r["doc"] for r in rows], pa.int32()),
        "span_start": pa.array([r["span_start"] for r in rows], pa.int32()),
        "span_end": pa.array([r["span_end"] for r in rows], pa.int32()),
        "tokens": pa.array([r["tokens"] for r in rows], pa.int32()),
        "counts": pa.array([r["counts"] for r in rows], pa.list_(pa.int32())),
    })  # fmt: skip
    pq.write_table(table, OUT / "benchmark_blocks.parquet")
    (OUT / "benchmark_vocabulary.json").write_text(json.dumps(vocabs, indent=1) + "\n")
    return {"documents": table.num_rows, "coverage": coverage,
            "vocabulary": {k: len(v) for k, v in vocabs.items()}}  # fmt: skip


def export() -> int:
    cfg = load_config()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {**stamp(), "benchmark": benchmark(cfg), "copied": {}}
    held = restricted_targets()
    report["withheld_targets"] = sorted(held)
    for name, src in COPIES.items():
        t = pq.read_table(src)
        if "target" in t.column_names:
            keep = [x not in held for x in t.column("target").to_pylist()]
            t = t.filter(pa.array(keep))
        pq.write_table(t, OUT / name)
        report["copied"][name] = {"from": str(src), "rows": t.num_rows}
    grams = [Path("data/reuse/bom/target_grams.txt"),
             *sorted(Path("data/reuse/rare_known/target_grams").glob("*.txt"))]  # fmt: skip
    for src in grams:
        if src.parent.name == "bom":
            shutil.copyfile(src, OUT / "target_grams_bom.txt")
        elif src.stem not in held:
            shutil.copyfile(src, OUT / f"target_grams_known_{src.stem}.txt")
    report["check"] = check_all()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: v for k, v in report.items() if "sha" not in k}, indent=1))
    return 0 if all(r["ok"] for r in report["check"].values()) else 1


def restricted_targets() -> set[str]:
    """Known-answer targets whose text came from a source that forbids redistribution."""
    keys = set()
    for ln in Path("data/known_answer/set.jsonl").read_text().splitlines():
        t = json.loads(ln)
        if {v["source"] for v in t["volumes"]} & RESTRICTED_SOURCES:
            keys.add(t["key"])
    return keys


def check_table(path: Path) -> dict:
    """The non-reconstructability check on one table."""
    t = pq.read_table(path)
    problems = []
    for f in t.schema:
        if pa.types.is_string(f.type) or pa.types.is_large_string(f.type):
            if f.name not in ALLOWED_STRINGS:
                problems.append(f"string column {f.name}")
        elif pa.types.is_list(f.type):
            if not pa.types.is_integer(f.type.value_type):
                problems.append(f"list column {f.name} is not integer")
        if any(k in f.name for k in ("text", "offset", "position", "token_ids")):
            problems.append(f"column {f.name} names text or positions")
    if "counts" in t.column_names:
        width = {len(x) for x in t.column("counts").to_pylist()[:1000]}
        if max(width, default=0) > MAX_VOCAB:
            problems.append(f"vocabulary {max(width)} over {MAX_VOCAB}")
    return {"rows": t.num_rows, "columns": t.column_names, "ok": not problems,
            "problems": problems}  # fmt: skip


def check_all() -> dict:
    out = {p.name: check_table(p) for p in sorted(OUT.glob("*.parquet"))}
    for p in OUT.glob("target_grams_*.txt"):
        # the target's 4-gram hashes: integers only, nothing readable
        ok = all(ln.strip().isdigit() for ln in p.read_text().splitlines() if ln.strip())
        out[p.name] = {"ok": ok}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=("export", "check"))
    a = ap.parse_args(argv)
    if a.cmd == "check":
        res = check_all()
        print(json.dumps(res, indent=1))
        return 0 if all(r["ok"] for r in res.values()) else 1
    return export()


if __name__ == "__main__":
    sys.exit(main())
