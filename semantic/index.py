"""The passage index of the whole corpus (BOM-25; plan in ``docs/semantic-plan.md``).

Every volume the corpus searches use (``reuse.exact.eligible_any_year``: text, a date,
deduplication keepers, OCR exclusions applied, no newspapers) is cut into passages of
``semantic.passage_words`` words on its normalised text and embedded with ``semantic.index_model``.
Date windows, own copies and every other selection are applied when the index is searched, so a
corrected date never forces a rebuild.

On disk, under ``data/corpus/semantic/index/`` (not in git; checksummed by manifest): shards of
``semantic.shard_volumes`` volumes, each ``shard_NNNNN.npy`` (float16 vectors, one row per
passage) and ``shard_NNNNN.parquet`` (work id, passage number, character span, word count: no
text). A shard's ``.done`` marker is written last, so a stopped build resumes at the first shard
without one, and a later build indexes only volumes no finished shard holds: new volumes are
added, nothing is re-embedded.

Usage::

    python -m semantic.index build [--workers 6]   # resumable; ~7 days on the M4
    python -m semantic.index status
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

INDEX = Path("data/corpus/semantic/index")
_WORD = re.compile(r"\S+")
META = pa.schema([("work_id", pa.string()), ("passage", pa.int32()), ("char_begin", pa.int64()),
                  ("char_end", pa.int64()), ("words", pa.int16())])  # fmt: skip


def spans(text: str, n: int, min_words: int) -> list[tuple[int, int, int]]:
    """(char_begin, char_end, words) of consecutive ``n``-word passages; a last passage shorter
    than ``min_words`` is dropped. Words are whitespace-separated, as in ``semantic.choose``."""
    bounds = [(m.start(), m.end()) for m in _WORD.finditer(text)]
    out = []
    for i in range(0, len(bounds), n):
        chunk = bounds[i : i + n]
        if len(chunk) >= min_words:
            out.append((chunk[0][0], chunk[-1][1], len(chunk)))
    return out


def _read(job: tuple[str, str, int, int]) -> tuple[str, list[str], list[tuple[int, int, int]]]:
    wid, path, n, min_words = job
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return wid, [], []
    sp = spans(text, n, min_words)
    return wid, [" ".join(text[a:b].split()) for a, b, _ in sp], sp


def _done() -> list[Path]:
    return sorted(INDEX.glob("shard_*.done"))


def indexed() -> set[str]:
    """Work ids held by finished shards."""
    out: set[str] = set()
    for d in _done():
        t = pq.read_table(d.with_suffix(".parquet"), columns=["work_id"])
        out.update(t["work_id"].unique().to_pylist())
    return out


def _model(cfg: dict):
    import torch
    from sentence_transformers import SentenceTransformer

    s = cfg["semantic"]
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    st = SentenceTransformer(s["index_model"], device=device)
    st.max_seq_length = s["max_tokens"]
    return st.half() if s["half_precision"] and device != "cpu" else st


def build(workers: int) -> int:
    import numpy as np

    from ocr_fix.normalize import norm_path
    from reuse.exact import eligible_any_year

    cfg = load_config()
    s = cfg["semantic"]
    INDEX.mkdir(parents=True, exist_ok=True)
    have = indexed()
    rows = sorted((r for r in eligible_any_year(cfg) if r["work_id"] not in have),
                  key=lambda r: r["work_id"])  # fmt: skip
    first = len(_done())
    shards = [rows[i : i + s["shard_volumes"]] for i in range(0, len(rows), s["shard_volumes"])]
    print(f"{len(have):,} volumes indexed in {first} shards; {len(rows):,} to go in "
          f"{len(shards)} shards", flush=True)  # fmt: skip
    (INDEX / "settings.json").write_text(json.dumps({**stamp(), "semantic": s}, indent=1) + "\n")
    st = _model(cfg)
    start, done_passages = time.time(), 0
    with ProcessPoolExecutor(workers) as pool:
        for k, shard in enumerate(shards):
            name = INDEX / f"shard_{first + k:05d}"
            jobs = [(r["work_id"], str(norm_path(r)), s["passage_words"], s["min_passage_words"])
                    for r in shard]  # fmt: skip
            meta, texts = [], []
            for wid, ts, sp in pool.map(_read, jobs, chunksize=8):
                texts += ts
                meta += [{"work_id": wid, "passage": i, "char_begin": a, "char_end": b,
                          "words": w} for i, (a, b, w) in enumerate(sp)]  # fmt: skip
            vec = st.encode(texts, batch_size=s["batch_size"], normalize_embeddings=True,
                            convert_to_numpy=True, show_progress_bar=False)  # fmt: skip
            tmp = name.with_suffix(".tmp.npy")
            np.save(tmp, vec.astype(np.float16))
            tmp.rename(name.with_suffix(".npy"))
            pq.write_table(pa.Table.from_pylist(meta, schema=META), name.with_suffix(".parquet"))
            done = {"volumes": len(shard), "passages": len(meta)}
            name.with_suffix(".done").write_text(json.dumps(done) + "\n")
            done_passages += len(meta)
            rate = done_passages / (time.time() - start)
            left = (len(shards) - k - 1) * done_passages / (k + 1) / rate / 86400
            print(f"shard {first + k}: {len(shard)} volumes, {len(meta):,} passages; "
                  f"{rate:.0f}/s, about {left:.1f} days left", flush=True)  # fmt: skip
    print("index complete")
    return 0


def status() -> int:
    vols = passages = 0
    for d in _done():
        r = json.loads(d.read_text())
        vols += r["volumes"]
        passages += r["passages"]
    print(f"{len(_done())} shards, {vols:,} volumes, {passages:,} passages")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--workers", type=int, default=6)
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build(a.workers)
    return status()


if __name__ == "__main__":
    sys.exit(main())
