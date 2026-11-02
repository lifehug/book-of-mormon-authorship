"""The period tokenizer and the encoded training set (BOM-27; Amendment 2).

``train``: byte-level BPE with ``timelocked_lm.vocab_size`` (32,000) entries, fit on a seeded
sample of ``timelocked_lm.tokenizer_sample_bytes`` of training-split text (whole volumes, drawn
in a seeded order), so no modern text enters the model at any layer. One special token,
``<|endoftext|>``, separates volumes.

``encode``: every volume of ``data/timelocked_lm/training_set.parquet`` encoded, each followed by
``<|endoftext|>``, into ``train_NNN.bin`` / ``validation_NNN.bin`` (uint16, about 1 GB each)
under ``data/corpus/timelocked_lm/tokens/`` (not in git: it is the licensed text, encoded) with
an index of work id, file, offset and length. Resumable: a finished file has a ``.done`` marker.

Usage::

    python -m timelocked_lm.tokenize train    # -> data/timelocked_lm/tokenizer.json
    python -m timelocked_lm.tokenize encode [--workers 6]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/timelocked_lm")
TOKENIZER = OUT / "tokenizer.json"
TOKENS = Path("data/corpus/timelocked_lm/tokens")
EOT = "<|endoftext|>"


def _paths() -> dict[str, str]:
    from metadata.pseudo_biblical import CATALOG
    from ocr_fix.normalize import norm_path

    want = set(pq.read_table(OUT / "training_set.parquet", columns=["work_id"]).column(0)
               .to_pylist())  # fmt: skip
    return {r["work_id"]: str(norm_path(r)) for r in pq.read_table(CATALOG).to_pylist()
            if r["work_id"] in want}  # fmt: skip


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def train() -> int:
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

    cfg = load_config()
    t = cfg["timelocked_lm"]
    sel = pq.read_table(OUT / "training_set.parquet").to_pylist()
    paths = _paths()
    ids = sorted(r["work_id"] for r in sel if r["split"] == "train")
    random.Random(derive_seed(t["tokenizer_seed"], cfg)).shuffle(ids)
    used: list[str] = []

    def sample():
        got = 0
        for w in ids:
            if got >= t["tokenizer_sample_bytes"]:
                return
            text = _read(paths[w])
            got += len(text.encode("utf-8"))
            used.append(w)
            yield text

    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(vocab_size=t["vocab_size"], special_tokens=[EOT],
                                  initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
                                  show_progress=False)  # fmt: skip
    t0 = time.time()
    tok.train_from_iterator(sample(), trainer=trainer)
    OUT.mkdir(parents=True, exist_ok=True)
    tok.save(str(TOKENIZER))
    (OUT / "tokenizer_sample.json").write_text(json.dumps(
        {**stamp(), "volumes": len(used), "vocab_size": tok.get_vocab_size(),
         "minutes": round((time.time() - t0) / 60, 1), "work_ids": used}) + "\n")  # fmt: skip
    print(f"tokenizer: {tok.get_vocab_size()} entries from {len(used):,} volumes, "
          f"{(time.time() - t0) / 60:.0f} min -> {TOKENIZER}")  # fmt: skip
    return 0


_TOK: list = []


def _encode_one(job: tuple[str, str]) -> tuple[str, np.ndarray]:
    from tokenizers import Tokenizer

    if not _TOK:
        _TOK.append(Tokenizer.from_file(str(TOKENIZER)))
    w, path = job
    try:
        ids = _TOK[0].encode(_read(path)).ids
    except OSError:
        return w, np.zeros(0, np.uint16)
    ids.append(_TOK[0].token_to_id(EOT))
    return w, np.asarray(ids, np.uint16)


def encode(workers: int) -> int:
    """Each split encoded in a fixed (sorted) order into files of ``FILE_TOKENS``; a file is
    written whole and then marked done, so a stopped run redoes at most one file."""
    TOKENS.mkdir(parents=True, exist_ok=True)
    sel = pq.read_table(OUT / "training_set.parquet").to_pylist()
    paths = _paths()
    t0, total = time.time(), 0
    for split in ("validation", "train"):
        ids = sorted(r["work_id"] for r in sel if r["split"] == split)
        # files are cut by volume count fixed in advance, so a resumed run cuts the same way
        per_file = 2500 if split == "train" else len(ids)
        groups = [ids[i : i + per_file] for i in range(0, len(ids), per_file)]
        for n, group in enumerate(groups):
            stem = TOKENS / f"{split}_{n:03d}"
            if stem.with_suffix(".done").exists():
                continue
            parts, rows, off = [], [], 0
            with ProcessPoolExecutor(workers) as ex:
                for w, arr in ex.map(_encode_one, [(w, paths[w]) for w in group], chunksize=8):
                    parts.append(arr)
                    rows.append((w, off, len(arr)))
                    off += len(arr)
            np.concatenate(parts).tofile(stem.with_suffix(".bin"))
            pq.write_table(pa.table({"work_id": [r[0] for r in rows],
                                     "offset": pa.array([r[1] for r in rows], pa.int64()),
                                     "length": pa.array([r[2] for r in rows], pa.int64())}),
                           stem.with_suffix(".parquet"))  # fmt: skip
            stem.with_suffix(".done").write_text(json.dumps({"tokens": off}) + "\n")
            total += off
            rate = total / (time.time() - t0)
            print(f"{stem.name}: {len(group)} volumes, {off:,} tokens; {rate / 1e6:.1f}M/s",
                  flush=True)  # fmt: skip
    return status()


def status() -> int:
    done = sorted(TOKENS.glob("*.done"))
    n = {s: sum(json.loads(p.read_text())["tokens"] for p in done if p.name.startswith(s))
         for s in ("train", "validation")}  # fmt: skip
    print(f"{len(done)} files done; train {n['train']:,} tokens, validation "
          f"{n['validation']:,}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("train")
    e = sub.add_parser("encode")
    e.add_argument("--workers", type=int, default=6)
    sub.add_parser("status")
    a = ap.parse_args(argv)
    return {"train": train, "status": status}.get(a.cmd, lambda: encode(a.workers))()


if __name__ == "__main__":
    sys.exit(main())
