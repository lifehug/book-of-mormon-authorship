"""Fast meaning search over the passage index (the lab's search by meaning).

The study's passage index (``semantic.index``: one 384-number vector per 128-word passage, 119 GB)
is exact but takes minutes to scan. ``build`` makes a small companion beside it: each vector
reduced to its 384 signs (48 bytes a passage), with the work each passage belongs to. A search
then runs in two passes: the signs pick the ``lab.candidates`` nearest passages among the works a
rule set admits, and those few are scored exactly from the study's own vectors. Nothing in the
study's index is changed, and the companion is rebuilt from it at any time.

Usage::

    python -m lab.passages build     # -> data/corpus/lab/ (about 8 GB; one pass over the index)
    python -m lab.passages status
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from lab.paths import FAST, out
from metadata.config import load as load_config
from metadata.config import stamp
from semantic.index import INDEX

CODES, ROWS, META = FAST / "codes.npy", FAST / "rows.npy", FAST / "index.json"
BYTES = 48  # 384 signs


def shards() -> list[Path]:
    return [d.with_suffix("") for d in sorted(INDEX.glob("shard_*.done"))]


def build() -> int:
    names = shards()
    sizes = [pq.read_metadata(s.with_suffix(".parquet")).num_rows for s in names]
    n = sum(sizes)
    codes = np.lib.format.open_memmap(out(CODES), mode="w+", dtype=np.uint8, shape=(n, BYTES))
    rows = np.lib.format.open_memmap(out(ROWS), mode="w+", dtype=np.int32, shape=(n,))
    works: dict[str, int] = {}
    at = 0
    for i, (s, size) in enumerate(zip(names, sizes, strict=True)):
        vec = np.load(s.with_suffix(".npy"), mmap_mode="r")
        if vec.shape[0] != size:
            raise SystemExit(f"{s.name}: {vec.shape[0]} vectors, {size} passages")
        codes[at : at + size] = np.packbits(np.asarray(vec) > 0, axis=1)
        ids = pq.read_table(s.with_suffix(".parquet"), columns=["work_id"])["work_id"].to_pylist()
        rows[at : at + size] = [works.setdefault(w, len(works)) for w in ids]
        at += size
        if i % 20 == 0:
            print(f"{i + 1}/{len(names)} shards, {at:,} passages", flush=True)
    codes.flush()
    rows.flush()
    listed = [{"name": s.name, "rows": k} for s, k in zip(names, sizes, strict=True)]
    meta = {**stamp(), "passages": n, "works": list(works), "shards": listed}
    out(META).write_text(json.dumps(meta) + "\n")
    print(f"{n:,} passages of {len(works):,} works -> {FAST}")
    return 0


class Index:
    """The companion index, opened read-only."""

    def __init__(self) -> None:
        if not META.exists():
            raise SystemExit("no fast index yet: run `python -m lab.passages build`")
        m = json.loads(META.read_text())
        self.works: list[str] = m["works"]
        self.shards = m["shards"]
        self.starts = np.cumsum([0] + [s["rows"] for s in self.shards])
        self.codes = np.load(CODES, mmap_mode="r")
        self.rows = np.load(ROWS, mmap_mode="r")
        self.stale = [s.name for s in shards()] != [s["name"] for s in self.shards]

    def allowed(self, work_ids: set[str] | None) -> np.ndarray | None:
        """A yes/no per indexed work, or None for every work."""
        if work_ids is None:
            return None
        return np.fromiter((w in work_ids for w in self.works), dtype=bool, count=len(self.works))

    def candidates(self, q: np.ndarray, ok: np.ndarray | None, keep: int, chunk: int) -> np.ndarray:
        """Row numbers of the ``keep`` passages whose signs differ least from the query's."""
        code = np.packbits(q > 0).view(np.uint64)
        best_d = np.empty(0, dtype=np.uint16)
        best_i = np.empty(0, dtype=np.int64)
        for a in range(0, len(self.rows), chunk):
            block = np.ascontiguousarray(self.codes[a : a + chunk]).view(np.uint64)
            d = np.bitwise_count(block ^ code).sum(axis=1, dtype=np.uint16)
            if ok is not None:
                d[~ok[self.rows[a : a + chunk]]] = np.iinfo(np.uint16).max
            k = min(keep, len(d))
            top = np.argpartition(d, k - 1)[:k]
            best_d = np.concatenate([best_d, d[top]])
            best_i = np.concatenate([best_i, top + a])
            if len(best_d) > keep:
                sel = np.argpartition(best_d, keep - 1)[:keep]
                best_d, best_i = best_d[sel], best_i[sel]
        return np.sort(best_i[best_d < np.iinfo(np.uint16).max])

    def exact(self, q: np.ndarray, rows: np.ndarray) -> np.ndarray:
        """The study's own score (inner product of unit vectors) for the given passages."""
        scores = np.empty(len(rows), dtype=np.float32)
        which = np.searchsorted(self.starts, rows, side="right") - 1
        for s in np.unique(which):
            sel = which == s
            vec = np.load(INDEX / f"{self.shards[s]['name']}.npy", mmap_mode="r")
            scores[sel] = np.asarray(vec[rows[sel] - self.starts[s]], dtype=np.float32) @ q
        return scores

    def describe(self, rows: np.ndarray) -> list[dict]:
        """Work id, passage number and character span of each passage."""
        result = []
        which = np.searchsorted(self.starts, rows, side="right") - 1
        tables: dict[int, list[dict]] = {}
        for r, s in zip(rows.tolist(), which.tolist(), strict=True):
            if s not in tables:
                tables[s] = pq.read_table(INDEX / f"{self.shards[s]['name']}.parquet").to_pylist()
            result.append(tables[s][r - int(self.starts[s])])
        return result


def embed(texts: list[str], cfg: dict, question: bool) -> np.ndarray:
    """Query vectors from the index's own model; a question gets the model's search prefix."""
    from semantic.index import _model

    prefix = cfg["lab"]["query_prefix"] if question else ""
    vec = _model(cfg).encode([prefix + " ".join(t.split()) for t in texts],
                             normalize_embeddings=True, convert_to_numpy=True,
                             show_progress_bar=False)  # fmt: skip
    return vec.astype(np.float32)


def search(texts: list[str], work_ids: set[str] | None, top: int, question: bool = False,
           cfg: dict | None = None, index: Index | None = None) -> list[list[dict]]:  # fmt: skip
    """For each query text, its ``top`` nearest passages among ``work_ids`` (None: every work)."""
    cfg = cfg or load_config()
    ix = index or Index()
    ok = ix.allowed(work_ids)
    results = []
    for q in embed(texts, cfg, question):
        rows = ix.candidates(q, ok, cfg["lab"]["candidates"], cfg["lab"]["chunk_rows"])
        scores = ix.exact(q, rows)
        order = np.argsort(-scores)[:top]
        hits = ix.describe(rows[order])
        results.append([{**h, "score": round(float(s), 4)}
                        for h, s in zip(hits, scores[order], strict=True)])  # fmt: skip
    return results


def status() -> int:
    ix = Index()
    print(f"{len(ix.rows):,} passages of {len(ix.works):,} works in {len(ix.shards)} shards"
          + ("; the study's index has changed since: rebuild" if ix.stale else ""))  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["build", "status"])
    return {"build": build, "status": status}[ap.parse_args(argv).command]()


if __name__ == "__main__":
    sys.exit(main())
