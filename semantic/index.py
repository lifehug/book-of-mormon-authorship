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

A rented GPU can take part of the build (``docs/runpod-setup.md``): ``pack`` writes the passages
of the volumes from ``--from`` on, with their text, to ``data/corpus/semantic/pack/`` for upload
(licensed text: never in git, deleted from the rented machine after); ``embed-pack`` embeds them
there into shards of the same format, named ``shard_pNNNNN``; ``build --before`` keeps the Mac to
the volumes ahead of that boundary. Neither changes a passage, the model or its settings; ``pack
--check`` adds passages the Mac already embedded, so the two machines' vectors can be compared
before any GPU shard is used.

Usage::

    python -m semantic.index build [--workers 6] [--before WORK_ID]   # resumable; ~7 days on the M4
    python -m semantic.index pack --from WORK_ID [--before WORK_ID] [--first N] [--workers 4]
    python -m semantic.index embed-pack --pack DIR --out DIR [--batch-size 512]   # on the GPU
    python -m semantic.index compare --check DIR                    # GPU against Mac vectors
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
PACK = Path("data/corpus/semantic/pack")
CHECK_PASSAGES = 20000  # passages of shard_00000 re-embedded on the GPU for the comparison
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
    device = ("cuda" if torch.cuda.is_available()
              else "mps" if torch.backends.mps.is_available() else "cpu")  # fmt: skip
    st = SentenceTransformer(s["index_model"], device=device)
    st.max_seq_length = s["max_tokens"]
    return st.half() if s["half_precision"] and device != "cpu" else st


def remaining(cfg: dict, start: str | None = None, before: str | None = None) -> list[dict]:
    """Eligible volumes no finished shard holds, by work id, within ``[start, before)``."""
    from reuse.exact import eligible_any_year

    have = indexed()
    return sorted((r for r in eligible_any_year(cfg) if r["work_id"] not in have
                   and (start is None or r["work_id"] >= start)
                   and (before is None or r["work_id"] < before)),
                  key=lambda r: r["work_id"])  # fmt: skip


def build(workers: int, before: str | None = None) -> int:
    import numpy as np

    from ocr_fix.normalize import norm_path

    cfg = load_config()
    s = cfg["semantic"]
    INDEX.mkdir(parents=True, exist_ok=True)
    have = indexed()
    rows = remaining(cfg, before=before)
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


def _meta_and_texts(pool, rows: list[dict], s: dict) -> tuple[list[dict], list[str]]:
    from ocr_fix.normalize import norm_path

    jobs = [(r["work_id"], str(norm_path(r)), s["passage_words"], s["min_passage_words"])
            for r in rows]  # fmt: skip
    meta, texts = [], []
    for wid, ts, sp in pool.map(_read, jobs, chunksize=8):
        texts += ts
        meta += [{"work_id": wid, "passage": i, "char_begin": a, "char_end": b, "words": w}
                 for i, (a, b, w) in enumerate(sp)]  # fmt: skip
    return meta, texts


def pack(start: str, workers: int, check: bool, before: str | None = None, first: int = 0) -> int:
    """The passages (with text) of every remaining volume in ``[start, before)``, for a rented GPU.
    Files are numbered from ``first`` so a second batch never collides with one already sent."""
    from reuse.exact import eligible_any_year

    cfg = load_config()
    s = cfg["semantic"]
    PACK.mkdir(parents=True, exist_ok=True)
    rows = remaining(cfg, start=start, before=before)
    shards = [rows[i : i + s["shard_volumes"]] for i in range(0, len(rows), s["shard_volumes"])]
    schema = META.append(pa.field("text", pa.string()))
    total = 0
    with ProcessPoolExecutor(workers) as pool:
        if check:
            # the first passages of the Mac's first shard, to compare the machines' vectors
            first = pq.read_table(INDEX / "shard_00000.parquet").slice(0, CHECK_PASSAGES)
            wids = list(dict.fromkeys(first["work_id"].to_pylist()))
            by = {r["work_id"]: r for r in eligible_any_year(cfg)}
            meta, texts = _meta_and_texts(pool, [by[w] for w in wids], s)
            meta, texts = meta[:CHECK_PASSAGES], texts[:CHECK_PASSAGES]
            assert [(m["work_id"], m["passage"]) for m in meta] == list(
                zip(first["work_id"].to_pylist(), first["passage"].to_pylist(), strict=True)
            )
            rows_t = [m | {"text": t} for m, t in zip(meta, texts, strict=True)]
            pq.write_table(pa.Table.from_pylist(rows_t, schema=schema), PACK / "check.parquet",
                           compression="zstd")  # fmt: skip
            print(f"check: {len(meta):,} passages of shard_00000", flush=True)
        for k, shard in enumerate(shards):
            name = PACK / f"pack_{first + k:05d}.parquet"
            if name.exists():
                total += pq.read_metadata(name).num_rows
                continue
            meta, texts = _meta_and_texts(pool, shard, s)
            rows_t = [m | {"text": t} for m, t in zip(meta, texts, strict=True)]
            tmp = name.with_suffix(".tmp")
            pq.write_table(pa.Table.from_pylist(rows_t, schema=schema), tmp, compression="zstd")
            tmp.rename(name)
            total += len(meta)
            print(f"pack {first + k}: {len(shard)} volumes, {len(meta):,} passages", flush=True)
    info = {
        **stamp(),
        "from": start,
        "before": before,
        "first": first,
        "volumes": len(rows),
        "packs": len(shards),
        "passages": total,
    }
    (PACK / ("pack.json" if first == 0 else f"pack_from_{first:05d}.json")).write_text(
        json.dumps(info, indent=1) + "\n"
    )
    print(f"packed {len(rows):,} volumes, {total:,} passages in {len(shards)} files")
    return 0


def embed_pack(pack_dir: Path, out: Path, batch_size: int) -> int:
    """Embed packed passages into ``shard_pNNNNN`` files of the index format (no text)."""
    import numpy as np

    cfg = load_config()
    st = _model(cfg)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(pack_dir.glob("pack_*.parquet"))
    if (pack_dir / "check.parquet").exists():
        files = [pack_dir / "check.parquet", *files]
    start, n = time.time(), 0
    for f in files:
        stem = "check" if f.stem == "check" else f"shard_p{f.stem.split('_')[1]}"
        name = out / stem
        if name.with_suffix(".done").exists():
            continue
        t = pq.read_table(f)
        vec = st.encode(t["text"].to_pylist(), batch_size=batch_size, normalize_embeddings=True,
                        convert_to_numpy=True, show_progress_bar=False)  # fmt: skip
        tmp = name.with_suffix(".tmp.npy")
        np.save(tmp, vec.astype(np.float16))
        tmp.rename(name.with_suffix(".npy"))
        pq.write_table(t.drop(["text"]), name.with_suffix(".parquet"))
        vols = len(set(t["work_id"].to_pylist()))
        name.with_suffix(".done").write_text(
            json.dumps({"volumes": vols, "passages": t.num_rows}) + "\n"
        )
        n += t.num_rows
        print(f"{stem}: {t.num_rows:,} passages; {n / (time.time() - start):.0f}/s", flush=True)
    print("embed-pack complete")
    return 0


def compare(check_dir: Path) -> int:
    """Cosine of the GPU's vectors for shard_00000's first passages against the Mac's."""
    import numpy as np

    gpu = np.load(check_dir / "check.npy").astype(np.float32)
    mac = np.load(INDEX / "shard_00000.npy", mmap_mode="r")[: len(gpu)].astype(np.float32)
    cos = (gpu * mac).sum(1) / np.linalg.norm(gpu, axis=1) / np.linalg.norm(mac, axis=1)
    res = {
        "passages": len(gpu),
        "min_cosine": float(cos.min()),
        "mean_cosine": float(cos.mean()),
        "p001_cosine": float(np.quantile(cos, 0.001)),
    }
    print(json.dumps(res))
    (INDEX / "gpu_check.json").write_text(json.dumps({**stamp(), **res}, indent=1) + "\n")
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
    b.add_argument("--before", default=None, help="only volumes whose work id sorts before this")
    pk = sub.add_parser("pack")
    pk.add_argument("--from", dest="start", required=True)
    pk.add_argument("--workers", type=int, default=4)
    pk.add_argument("--no-check", dest="check", action="store_false")
    pk.add_argument("--before", default=None)
    pk.add_argument("--first", type=int, default=0)
    e = sub.add_parser("embed-pack")
    e.add_argument("--pack", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    e.add_argument("--batch-size", type=int, default=512)
    c = sub.add_parser("compare")
    c.add_argument("--check", type=Path, required=True)
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        return build(a.workers, a.before)
    if a.cmd == "pack":
        return pack(a.start, a.workers, a.check, a.before, a.first)
    if a.cmd == "embed-pack":
        return embed_pack(a.pack, a.out, a.batch_size)
    if a.cmd == "compare":
        return compare(a.check)
    return status()


if __name__ == "__main__":
    sys.exit(main())
