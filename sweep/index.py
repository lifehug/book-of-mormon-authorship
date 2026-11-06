"""The author sweep's index (BOM-39; Amendment 28, ``docs/sweep-plan.md``).

Units are an author's profile (role ``profile``), a calibration author's rebuilt profile
(``calib_profile``) and each calibration query chunk (``calib_query``). ``tokens`` writes each
unit's words: its blocks' text with the ``sweep`` group's KJV spans removed, in the benchmark's word
form (``classic.features.tokenize`` of ``segment.build.original_words``). ``mfw`` takes the
``sweep.mfw`` most frequent words of the author profiles (mean relative frequency, in at least
``classic.mfw_min_doc_fraction`` of them) and writes every unit's relative frequencies over them.
``embed`` writes every unit's style vector (the BOM-30 encoder, the unit as one episode).

The tokens are licensed text in another form and stay in ``data/corpus/sweep/``, as do the
matrices (cheap to rebuild from the tokens).

Usage::

    python -m sweep.index tokens [--workers 8]
    python -m sweep.index mfw
    python -m sweep.index embed
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from sweep.units import OUT, block_text

WORK = Path("data/corpus/sweep")
TOKENS = WORK / "tokens"
SPANS = Path("data/kjv_mask/sweep/spans.jsonl")

_spans: dict[str, list] = {}
_cat: dict[str, dict] = {}


def unit_of(b: dict) -> str:
    """profile:<author>, calib_profile:<author>, or the query chunk's own block id."""
    return b["block_id"] if b["role"] == "calib_query" else f"{b['role']}:{b['author']}"


def path_of(unit: str) -> Path:
    h = hashlib.sha1(unit.encode()).hexdigest()
    return TOKENS / h[:2] / f"{h}.txt.gz"


def _init() -> None:
    global _spans, _cat
    for ln in SPANS.read_text().splitlines():
        r = json.loads(ln)
        _spans[r["id"]] = r["spans"]
    need = set(pq.read_table(OUT / "blocks.parquet", columns=["work_id"]).column(0).to_pylist())
    _cat = {r["work_id"]: r for r in pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
    ).to_pylist() if r["work_id"] in need}  # fmt: skip


def _author(blocks: list[dict]) -> list[tuple[str, int]]:
    from classic.features import tokenize
    from segment.build import original_words

    units: dict[str, list[str]] = defaultdict(list)
    for b in blocks:
        text = block_text(_cat[b["work_id"]], b["start"], b["words"])
        units[unit_of(b)] += tokenize(" ".join(original_words(text, _spans[b["block_id"]])))
    out = []
    for u, toks in units.items():
        p = path_of(u)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            f.write(" ".join(toks))
        tmp.replace(p)
        out.append((u, len(toks)))
    return out


def tokens(workers: int) -> int:
    if not SPANS.exists():
        raise SystemExit(f"{SPANS} missing: run python -m kjv_mask.run sweep first")
    by: dict[str, list[dict]] = defaultdict(list)
    for b in pq.read_table(OUT / "blocks.parquet").to_pylist():
        by[b["author"]].append(b)
    index = WORK / "units.parquet"
    done = {}
    jobs = [bs for _, bs in sorted(by.items())]
    with Pool(workers, initializer=_init) as pool:
        for k, res in enumerate(pool.imap_unordered(_author, jobs, chunksize=8), 1):
            done.update(res)
            if k % 1000 == 0:
                print(f"  {k:,}/{len(jobs):,} authors", flush=True)
    rows = [{"unit": u, "tokens": n} for u, n in sorted(done.items())]
    pq.write_table(pa.Table.from_pylist(rows), index)
    print(f"{len(rows):,} units, {sum(r['tokens'] for r in rows):,} tokens -> {index}")
    return 0


def _units() -> list[dict]:
    return pq.read_table(WORK / "units.parquet").to_pylist()


def _read(unit: str) -> list[str]:
    with gzip.open(path_of(unit), "rt", encoding="utf-8") as f:
        return f.read().split()


class _Lazy:
    """The units' counts one at a time, so 24,000 profiles never sit in memory together."""

    def __init__(self, names: list[str]):
        self.names = names

    def __len__(self) -> int:
        return len(self.names)

    def __iter__(self):
        return (Counter(_read(n)) for n in self.names)


def mfw() -> int:
    from classic.features import build_vocabulary, relative_frequencies

    cfg = load_config()
    names = [u["unit"] for u in _units() if u["tokens"]]
    prof = [n for n in names if n.startswith("profile:")]
    vocab = build_vocabulary(_Lazy(prof), top_n=cfg["sweep"]["mfw"],
                             min_doc_fraction=cfg["classic"]["mfw_min_doc_fraction"])  # fmt: skip
    X = np.stack([relative_frequencies(c, vocab) for c in _Lazy(names)]).astype(np.float32)
    np.savez_compressed(WORK / "mfw.npz", X=X, units=np.array(names), vocab=np.array(vocab))
    (OUT / "vocabulary.json").write_text(json.dumps({"config_sha256": sha256_of_config(),
                                                     "profiles": len(prof),
                                                     "vocabulary": vocab}) + "\n")  # fmt: skip
    print(f"{len(names):,} units x {len(vocab)} words -> {WORK / 'mfw.npz'}")
    return 0


def embed() -> int:
    from style_embed.benchmark import MODEL, embedder

    cfg = load_config()
    out = WORK / "style.npz"
    part = WORK / "style_part.npz"
    got: dict[str, np.ndarray] = {}
    if part.exists():  # resume
        z = np.load(part)
        got = dict(zip(z["units"].tolist(), z["V"], strict=True))
    f = embedder(MODEL, cfg)
    todo = [u["unit"] for u in _units() if u["tokens"] and u["unit"] not in got]
    print(f"{len(todo):,} units to embed ({len(got):,} done)", flush=True)
    for k, u in enumerate(todo, 1):
        got[u] = f(_read(u)).astype(np.float32)
        if k % 2000 == 0 or k == len(todo):
            names = sorted(got)
            np.savez(part, units=np.array(names), V=np.stack([got[n] for n in names]))
            print(f"  {k:,}/{len(todo):,}", flush=True)
    names = sorted(got)
    np.savez_compressed(out, units=np.array(names), V=np.stack([got[n] for n in names]))
    print(f"{len(names):,} vectors -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["tokens", "mfw", "embed"])
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    return {"tokens": lambda: tokens(a.workers), "mfw": mfw, "embed": embed}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
