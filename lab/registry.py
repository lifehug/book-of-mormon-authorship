"""One row for every catalogued work, with the facts a test filters on (the lab's registry).

Nothing is dropped: a work with no text, a newspaper page, a duplicate copy and an anonymous
pamphlet each keep their row, with a column that says so. The columns are joined from tables the
study already published (catalog, corrected dates, duplicate groups, OCR exclusions, genre, word
counts, the models' training set, the swept authors and their life dates, the style models' author
split, the sealed Book of Mormon copies) plus one read from disk (which works the passage index
holds). Ids and flags only: no text, no titles (join ``data/catalog/catalog.parquet`` on
``work_id`` for those).

A *rule set* (``lab.views`` in the config) is a named list of conditions on these columns: what
one kind of test may use. ``select`` applies one; every lab result records which.

Usage::

    python -m lab.registry build    # -> data/lab/registry.parquet, registry.json (about a minute)
    python -m lab.registry views    # each rule set and how many works it admits
    python -m lab.registry map      # -> docs/lab/data-map.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from lab.paths import DOCS, REGISTRY, out
from metadata.config import load as load_config
from metadata.config import stamp

CATALOG = Path("data/catalog/catalog.parquet")
SEALED = Path("data/catalog/sealed.json")
TABLE = REGISTRY / "registry.parquet"
REPORT = REGISTRY / "registry.json"
COLUMNS = {
    "work_id": "the catalog's id (source:source_id)",
    "source": "where the record came from",
    "kind": "work (book or pamphlet) or newspaper_page",
    "has_text": "text is on disk",
    "year": "the year date-window selections use (title-page and body corrections applied); "
            "empty when undated or found to be later than 1830",
    "year_catalog": "the year as catalogued",
    "words": "words in the normalised text (empty when not counted)",
    "genre": "the genre label (data/catalog/genre.parquet)",
    "dup_keeper": "false for a reprint or second copy that another row stands for",
    "ocr_excluded": "set aside for unreadable OCR",
    "author_kind": "person, corporate (an institution or government) or none",
    "author_swept": "the author is one of the library search's authors (10,000+ words)",
    "author_life": "alive, dead, too_young or unknown in 1829 (swept authors only)",
    "author_style_split": "train or heldout: whether the style models were trained on this author",
    "training": "train, validation or none: whether the language models were trained on this work",
    "in_passage_index": "the meaning-search index holds this work's passages",
    "sealed": "a copy of the Book of Mormon, kept out of every model and every search",
}  # fmt: skip


def _lookup(path: str, key: str, value: str) -> dict:
    t = pq.read_table(path, columns=[key, value])
    return dict(zip(t[key].to_pylist(), t[value].to_pylist(), strict=True))


def rows(cfg: dict) -> list[dict]:
    """The registry, one dict per catalogued work, in catalog order."""
    from metadata.dates import effective_year
    from metadata.pseudo_biblical import DUPES, NOT_WORKS, VOLUMES
    from semantic.index import indexed
    from style_embed.data import _named
    from sweep.units import TRAINING_SET, volume_words

    names = "|".join(map(re.escape, cfg["style_embed"]["corporate"]))
    corporate = re.compile(r"\b(" + names + r")\b")
    genre = _lookup("data/catalog/genre.parquet", "work_id", "genre")
    keeper = _lookup(str(DUPES), "work_id", "is_keeper")
    excluded = _lookup(str(VOLUMES), "work_id", "ocr_excluded")
    split = _lookup(str(TRAINING_SET), "work_id", "split")
    life = _lookup("data/sweep/people.parquet", "author", "status")
    style = _lookup("data/style_embed/authors.parquet", "author", "split")
    sealed = {w["work_id"] for w in json.loads(SEALED.read_text())["works"]}
    words, held = volume_words(), indexed()
    cols = ["work_id", "source", "author_norm", "year", "has_text"]
    result = []
    for r in pq.read_table(CATALOG, columns=cols).to_pylist():
        w, a = r["work_id"], (r["author_norm"] or "").strip()
        kind = "none" if not _named(a) else "corporate" if corporate.search(a) else "person"
        result.append({
            "work_id": w, "source": r["source"],
            "kind": "newspaper_page" if r["source"] in NOT_WORKS else "work",
            "has_text": bool(r["has_text"]),
            "year": effective_year(w, r["year"]), "year_catalog": r["year"],
            "words": words.get(w), "genre": genre.get(w),
            "dup_keeper": keeper.get(w, True), "ocr_excluded": bool(excluded.get(w, False)),
            "author_kind": kind,
            "author_swept": a in life, "author_life": life.get(a),
            "author_style_split": style.get(a), "training": split.get(w, "none"),
            "in_passage_index": w in held, "sealed": w in sealed,
        })  # fmt: skip
    return result


def matches(value, cond) -> bool:
    """One condition of a rule set against one cell."""
    if isinstance(cond, dict):
        if "any" in cond:
            return value in cond["any"]
        if value is None:
            return False
        return cond.get("min", value) <= value <= cond.get("max", value)
    return value == cond


def select(table: pa.Table, view: dict) -> pa.Table:
    """The rows of ``table`` a rule set admits."""
    unknown = set(view) - set(table.column_names)
    if unknown:
        raise KeyError(f"rule set names columns the registry lacks: {sorted(unknown)}")
    keep = [True] * table.num_rows
    for col, cond in view.items():
        keep = [k and matches(v, cond) for k, v in zip(keep, table[col].to_pylist(), strict=True)]
    return table.filter(pa.array(keep))


def load() -> pa.Table:
    if not TABLE.exists():
        raise SystemExit("no registry yet: run `python -m lab.registry build`")
    return pq.read_table(TABLE)


def view(name: str, cfg: dict | None = None) -> pa.Table:
    """The registry rows of the named rule set."""
    views = (cfg or load_config())["lab"]["views"]
    if name not in views:
        raise SystemExit(f"no rule set {name!r}; there are: {', '.join(views)}")
    return select(load(), views[name])


def counts(cfg: dict) -> dict[str, dict]:
    t = load()
    result = {}
    for name, v in cfg["lab"]["views"].items():
        s = select(t, v)
        result[name] = {"works": s.num_rows, "with_text": sum(s["has_text"].to_pylist()),
                        "words": sum(x or 0 for x in s["words"].to_pylist())}  # fmt: skip
    return result


def build() -> int:
    cfg = load_config()
    t = pa.Table.from_pylist(rows(cfg))
    pq.write_table(t, out(TABLE), compression="zstd")
    report = {**stamp(), "works": t.num_rows, "columns": COLUMNS,
              "by_column": {c: dict(Counter(map(str, t[c].to_pylist())).most_common(12))
                            for c in t.column_names
                            if c not in ("work_id", "year", "year_catalog", "words")},
              "views": counts(cfg)}  # fmt: skip
    out(REPORT).write_text(json.dumps(report, indent=1) + "\n")
    print(f"{t.num_rows:,} works -> {TABLE}")
    return views()


def views() -> int:
    for name, c in counts(load_config()).items():
        print(f"{name:26} {c['works']:>9,} works  {c['with_text']:>9,} with text  "
              f"{c['words'] / 1e9:6.2f} billion words")  # fmt: skip
    return 0


def data_map() -> int:
    """The data map: what the registry holds and what each rule set admits, for the docs."""
    cfg, rep = load_config(), json.loads(REPORT.read_text())
    lines = ["# The data map", "",
             "Generated by `python -m lab.registry map`; do not edit by hand.", "",
             f"The registry has one row for each of the {rep['works']:,} catalogued works.", "",
             "## Rule sets", "",
             "| Rule set | Works | With text | Words | Conditions |",
             "| --- | --- | --- | --- | --- |"]  # fmt: skip
    for name, c in rep["views"].items():
        cond = "; ".join(f"`{k}` = {json.dumps(v)}" for k, v in cfg["lab"]["views"][name].items())
        lines.append(f"| `{name}` | {c['works']:,} | {c['with_text']:,} | "
                     f"{c['words'] / 1e9:.2f} billion | {cond or 'none'} |")  # fmt: skip
    lines += ["", "## Columns", "", "| Column | Meaning | Most common values |",
              "| --- | --- | --- |"]  # fmt: skip
    for col, meaning in COLUMNS.items():
        top = rep["by_column"].get(col, {})
        vals = ", ".join(f"{k} {v:,}" for k, v in list(top.items())[:6])
        lines.append(f"| `{col}` | {meaning} | {vals} |")
    out(DOCS / "data-map.md").write_text("\n".join(lines) + "\n")
    print(f"-> {DOCS / 'data-map.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["build", "views", "map"])
    a = ap.parse_args(argv)
    return {"build": build, "views": views, "map": data_map}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
