"""Units of the author sweep (BOM-39; Amendment 28, ``docs/sweep-plan.md``).

The volumes are the time-locked model's training set (``data/timelocked_lm/training_set.parquet``,
both splits): deduplication keepers in the registered date range, newspapers out, the Book of
Mormon and every volume sharing its strings removed. An author is a catalog ``author_norm`` that is
a personal name and not corporate (Amendment 24's rules) with at least ``sweep.min_words`` words;
a work is a title group (the first ``style_embed.work_title_words`` title words).

Each swept author gets up to ``sweep.max_blocks`` blocks of ``sweep.block_words`` words, taken
round-robin over the author's works in a seeded order, each at a seeded non-overlapping slot of a
volume. The 200 calibration books (``sweep.calibration_books``) are title groups of authors held
out of the style encoder's training, with at least one ``sweep.query_chunk_words``-word chunk and
``sweep.min_words`` words outside the book; their authors get a second profile from their other
works (role ``calib_profile``) and the book up to ``sweep.max_query_chunks`` chunks (role
``calib_query``).

Writes ids, offsets and counts only: ``data/sweep/authors.parquet`` and ``blocks.parquet``. A
block's text is whitespace word ``start`` to ``start + words`` of the volume's normalised text
(``block_text``).

Usage::

    python -m sweep.units build
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, sha256_of_config
from metadata.config import load as load_config

OUT = Path("data/sweep")
CATALOG = Path("data/catalog/catalog.parquet")
TRAINING_SET = Path("data/timelocked_lm/training_set.parquet")
SIGNATURES = Path("data/catalog/signatures_normalized")
STYLE_AUTHORS = Path("data/style_embed/authors.parquet")


def block_text(row: dict, start: int, words: int) -> str:
    """A block's text: whitespace words ``start`` to ``start + words`` of the normalised volume."""
    from ocr_fix.normalize import norm_path

    return " ".join(norm_path(row).read_text(encoding="utf-8").split()[start : start + words])


def volume_words() -> dict[str, int]:
    out: dict[str, int] = {}
    for f in sorted(SIGNATURES.glob("*.parquet")):
        t = pq.read_table(f, columns=["work_id", "words"])
        out.update(zip(t.column(0).to_pylist(), t.column(1).to_pylist(), strict=True))
    return out


def authors(cfg: dict) -> dict[str, dict[str, list[tuple[str, int]]]]:
    """Swept author -> work key -> [(volume id, words)]."""
    from reuse.exact import _title_key
    from style_embed.data import _named

    s, se = cfg["sweep"], cfg["style_embed"]
    bad = re.compile(r"\b(" + "|".join(re.escape(c) for c in se["corporate"]) + r")\b")
    ids = set(pq.read_table(TRAINING_SET, columns=["work_id"]).column(0).to_pylist())
    nwords = volume_words()
    by: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in pq.read_table(CATALOG, columns=["work_id", "author_norm", "title"]).to_pylist():
        a = (r["author_norm"] or "").strip()
        if r["work_id"] not in ids or not _named(a) or bad.search(a):
            continue
        key = " ".join(_title_key(r["title"]).split()[: se["work_title_words"]])
        by[a][key].append((r["work_id"], nwords.get(r["work_id"], 0)))
    return {
        a: {k: sorted(v) for k, v in sorted(ws.items())}
        for a, ws in sorted(by.items())
        if sum(n for v in ws.values() for _, n in v) >= s["min_words"]
    }


def sample(works: dict[str, list[tuple[str, int]]], n: int, size: int,
           rng: random.Random) -> list[tuple[str, int]]:  # fmt: skip
    """Up to ``n`` (volume, start) blocks of ``size`` words, round-robin over the works in a
    seeded order, each a distinct slot of a random volume of the work that has slots left."""
    slots = {v: rng.sample(range(w // size), w // size) for vols in works.values() for v, w in vols}
    order = rng.sample(sorted(works), len(works))
    out: list[tuple[str, int]] = []
    while len(out) < n:
        took = False
        for k in order:
            open_ = [v for v, _ in works[k] if slots[v]]
            if not open_ or len(out) >= n:
                continue
            v = rng.choice(open_)
            out.append((v, slots[v].pop() * size))
            took = True
        if not took:
            break
    return out


def chunks(vols: list[tuple[str, int]], size: int, most: int,
           rng: random.Random) -> list[tuple[str, int]]:  # fmt: skip
    """A book's consecutive ``size``-word chunks, volume by volume; a seeded ``most`` if more."""
    every = [(v, i * size) for v, w in vols for i in range(w // size)]
    return sorted(rng.sample(every, most)) if len(every) > most else every


def calibration(swept: dict, cfg: dict) -> dict[str, str]:
    """Calibration author -> the book (work key) held out of their profile."""
    s = cfg["sweep"]
    style = pq.read_table(STYLE_AUTHORS).to_pylist()
    held = {r["author"] for r in style if r["split"] == "heldout"}
    eligible: dict[str, list[str]] = {}
    for a in sorted(held & set(swept)):
        ws = swept[a]
        total = sum(n for v in ws.values() for _, n in v)
        books = [k for k, vols in ws.items()
                 if any(n >= s["query_chunk_words"] for _, n in vols)
                 and total - sum(n for _, n in vols) >= s["min_words"]]  # fmt: skip
        if books:
            eligible[a] = books
    rng = random.Random(derive_seed(s["calibration_seed"], cfg))
    pick = rng.sample(sorted(eligible), min(s["calibration_books"], len(eligible)))
    return {a: rng.choice(eligible[a]) for a in sorted(pick)}


def build() -> int:
    cfg = load_config()
    s = cfg["sweep"]
    swept = authors(cfg)
    calib = calibration(swept, cfg)
    size, n = s["block_words"], s["max_blocks"]
    rows: list[dict] = []
    for a, ws in swept.items():
        rng = random.Random(derive_seed(f"{s['block_seed']}:{a}", cfg))
        for i, (v, st) in enumerate(sample(ws, n, size, rng)):
            rows.append({"block_id": f"profile:{a}:{i}", "author": a, "role": "profile",
                         "work_id": v, "start": st, "words": size})  # fmt: skip
        if a in calib:
            others = {k: vols for k, vols in ws.items() if k != calib[a]}
            rng = random.Random(derive_seed(f"{s['block_seed']}:calib:{a}", cfg))
            for i, (v, st) in enumerate(sample(others, n, size, rng)):
                rows.append({"block_id": f"calib_profile:{a}:{i}", "author": a,
                             "role": "calib_profile", "work_id": v, "start": st,
                             "words": size})  # fmt: skip
            q = chunks(ws[calib[a]], s["query_chunk_words"], s["max_query_chunks"], rng)
            for i, (v, st) in enumerate(q):
                rows.append({"block_id": f"calib_query:{a}:{i}", "author": a,
                             "role": "calib_query", "work_id": v, "start": st,
                             "words": s["query_chunk_words"]})  # fmt: skip
    per: dict[str, int] = defaultdict(int)
    for r in rows:
        if r["role"] == "profile":
            per[r["author"]] += 1
    meta = {b"config_sha256": sha256_of_config().encode()}
    OUT.mkdir(parents=True, exist_ok=True)
    auth = [{"author": a, "works": len(ws), "volumes": sum(len(v) for v in ws.values()),
             "words": sum(n for v in ws.values() for _, n in v), "blocks": per[a],
             "calibration_book": calib.get(a)} for a, ws in swept.items()]  # fmt: skip
    for name, table in (("authors", auth), ("blocks", rows)):
        pq.write_table(pa.Table.from_pylist(table).replace_schema_metadata(meta),
                       OUT / f"{name}.parquet")  # fmt: skip
    roles: dict[str, int] = defaultdict(int)
    for r in rows:
        roles[r["role"]] += 1
    print(f"{len(swept):,} swept authors; {len(calib)} calibration books; blocks {dict(roles)}; "
          f"-> {OUT}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["build"])
    ap.parse_args(argv)
    return build()


if __name__ == "__main__":
    sys.exit(main())
