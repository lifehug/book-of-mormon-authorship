"""Training passages for the style embeddings (BOM-30; pre-registration 5.4, Amendment 24).

The time-locked model's training volumes (BOM-27), grouped by catalog author; corporate and
unnamed authors left out; a work is an author's volumes sharing the first
``style_embed.work_title_words`` title words; authors with at least ``style_embed.min_works``
works qualify, and ``style_embed.heldout_share`` of them (seeded hash) are held out of training.
Per author up to ``max_works`` works, per work ``passages_per_work`` passages of
``passage_tokens`` tokens, each from a random volume of the work at a random position, in the
benchmark's word form (lowercased tokens joined by spaces).

Writes ``data/style_embed/authors.parquet`` and ``works.parquet`` (ids and counts, no text) and
the passages themselves, which are licensed text in another form, to
``data/corpus/style_embed/passages.bin`` (uint16, rows of ``passage_tokens``) with their index
``passages.parquet``.

Usage::

    python -m style_embed.data build [--workers 6]
"""

from __future__ import annotations

import argparse
import hashlib
import random
import re
import sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/style_embed")
WORK = Path("data/corpus/style_embed")
TRAINING_SET = Path("data/timelocked_lm/training_set.parquet")
CATALOG = Path("data/catalog/catalog.parquet")
WINDOW_CHARS = 3000  # characters read around a passage start; ample for 128 tokens

_tok = None


def _held_out(author: str, salt: int, share: float) -> bool:
    h = int(hashlib.sha256(f"{salt}:{author}".encode()).hexdigest()[:8], 16)
    return h % 10000 < share * 10000


def _named(a: str) -> bool:
    """A person's name, not an empty field, a stray letter or a record number ("a",
    "50044062, guy s hospital n"): Amendment 24's "no author"."""
    if re.search(r",\s*an?$", a):  # "subscriber, a": a descriptive pseudonym, not a name
        return False
    return bool(a) and a[0].isalpha() and len(re.sub(r"[^a-z]", "", a.split(",")[0])) >= 3


def authors(cfg: dict) -> dict[str, dict[str, list[dict]]]:
    """Qualifying author -> work key -> catalog rows of its volumes."""
    from reuse.exact import _title_key

    s = cfg["style_embed"]
    bad = re.compile(r"\b(" + "|".join(re.escape(c) for c in s["corporate"]) + r")\b")
    ids = set(pq.read_table(TRAINING_SET, columns=["work_id"]).column(0).to_pylist())
    cols = ["work_id", "source", "text_path", "author_norm", "title"]
    by: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in pq.read_table(CATALOG, columns=cols).to_pylist():
        a = (r["author_norm"] or "").strip()
        if r["work_id"] not in ids or not _named(a) or bad.search(a):
            continue
        key = " ".join(_title_key(r["title"]).split()[: s["work_title_words"]])
        by[a][key].append(r)
    return {a: dict(ws) for a, ws in sorted(by.items()) if len(ws) >= s["min_works"]}


def _init() -> None:
    global _tok
    from tokenizers import Tokenizer

    from timelocked_lm.release import TOKENIZER

    _tok = Tokenizer.from_file(str(TOKENIZER))


def _author_passages(job: tuple[str, dict[str, list[dict]], dict, int]) -> tuple[str, list]:
    """(work key, volume id, token row) for one author's sampled passages."""
    from classic.features import tokenize
    from ocr_fix.normalize import norm_path

    author, works, s, seed = job
    rng = random.Random(seed)
    keys = sorted(works)
    if len(keys) > s["max_works"]:
        keys = sorted(rng.sample(keys, s["max_works"]))
    out = []
    for key in keys:
        vols = sorted(works[key], key=lambda r: r["work_id"])
        picks = defaultdict(int)
        for _ in range(s["passages_per_work"]):
            picks[rng.randrange(len(vols))] += 1
        for vi, n in sorted(picks.items()):
            try:
                text = norm_path(vols[vi]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if len(text) < WINDOW_CHARS:
                continue
            got, tries = 0, 0
            while got < n and tries < 4 * n:
                tries += 1
                start = rng.randrange(len(text) - WINDOW_CHARS + 1)
                words = tokenize(text[start : start + WINDOW_CHARS])[1:]  # first word may be cut
                ids = _tok.encode(" ".join(words)).ids
                if len(ids) >= s["passage_tokens"]:
                    out.append((key, vols[vi]["work_id"], ids[: s["passage_tokens"]]))
                    got += 1
    return author, out


def build(workers: int) -> int:
    cfg = load_config()
    s = cfg["style_embed"]
    auth = authors(cfg)
    salt = derive_seed(s["heldout_seed"], cfg)
    split = {a: "heldout" if _held_out(a, salt, s["heldout_share"]) else "train" for a in auth}
    print(f"{len(auth):,} qualifying authors; {sum(v == 'heldout' for v in split.values()):,} "
          f"held out", flush=True)  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    jobs = [(a, ws, s, derive_seed(f"{s['passage_seed']}:{a}", cfg)) for a, ws in auth.items()]
    index = {"author": [], "work": [], "volume": []}
    counts: dict[str, int] = defaultdict(int)
    with (WORK / "passages.bin").open("wb") as f, Pool(workers, initializer=_init) as pool:
        for k, (a, rows) in enumerate(pool.imap(_author_passages, jobs, chunksize=8), 1):
            for key, vol, ids in rows:
                f.write(np.asarray(ids, dtype=np.uint16).tobytes())
                index["author"].append(a)
                index["work"].append(key)
                index["volume"].append(vol)
                counts[a] += 1
            if k % 500 == 0:
                print(f"  {k:,}/{len(jobs):,} authors, {len(index['author']):,} passages",
                      flush=True)  # fmt: skip
    pq.write_table(pa.table(index), WORK / "passages.parquet")
    pq.write_table(pa.table({
        "author": list(auth), "split": [split[a] for a in auth],
        "works": [len(ws) for ws in auth.values()],
        "volumes": [sum(len(v) for v in ws.values()) for ws in auth.values()],
        "passages": [counts[a] for a in auth]}), OUT / "authors.parquet")  # fmt: skip
    pq.write_table(pa.table({
        "author": [a for a, ws in auth.items() for k in ws],
        "work": [k for ws in auth.values() for k in ws],
        "volumes": [[r["work_id"] for r in v] for ws in auth.values() for v in ws.values()]}),
        OUT / "works.parquet")  # fmt: skip
    (OUT / "build.json").write_text(__import__("json").dumps(
        {**stamp(), "authors": len(auth), "heldout": sum(v == "heldout" for v in split.values()),
         "passages": len(index["author"])}, indent=1) + "\n")  # fmt: skip
    print(f"-> {WORK / 'passages.bin'}: {len(index['author']):,} passages", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    return build(a.workers)


if __name__ == "__main__":
    sys.exit(main())
