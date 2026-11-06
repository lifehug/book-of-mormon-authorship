"""Seal the Book of Mormon chunks for the blind run (BOM-32; section 8, Amendments 1 and 32).

The whole chunks of ``data/bom/segments/chunks.jsonl`` in ``blind.sealed_schemes`` and
``blind.sealed_sizes`` get opaque ids, and decoys are mixed in: for each chunk size, at least
``blind.decoy_ratio`` decoys per Book of Mormon chunk, each a run of that many words of KJV-masked
text by a known author, ``blind.candidate_share`` of them from candidates (each keeping
``candidates.min_masked_words`` out of the decoys as their reference) and the rest from control
authors (``blind.decoy_pool``); author drawn uniformly among those who can give one, position
seeded (``blind.seal_seed``), never overlapping another decoy. The sealed set is shuffled.

Written:

- the key (id -> chunk id, or decoy author, source and word span) to ``--key`` (default
  ``~/.bom-blind/key.json``, mode 600); refused inside the repository;
- the sealed set (id, words, text) to ``data/corpus/blind/sealed.jsonl``, not in git (it holds
  licensed and copyrighted text);
- ``data/blind/seal.json`` (committed): SHA-256 of the key and of the sealed set, counts, seed and
  config hash -- no mapping;
- ``data/blind/withheld.json`` (committed): the decoys' source spans, which every method must leave
  out of its references so a decoy is not scored against its own text. It names spans, not ids.

Usage::

    python -m blind.seal [--key ~/.bom-blind/key.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = Path("data/bom/segments/chunks.jsonl")
SEALED = Path("data/corpus/blind/sealed.jsonl")
OUT = Path("data/blind")
KEY = Path.home() / ".bom-blind" / "key.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def outside_repo(path: Path) -> Path:
    """The key's path, refused if it lies inside the repository."""
    p = path.expanduser().resolve()
    if p == ROOT or ROOT in p.parents:
        raise SystemExit(f"the key must be written outside the repository, not {p}")
    return p


def pick_decoys(pool: dict[str, list[tuple[str, list[str]]]], need: dict[int, int],
                rng: random.Random, keep: int = 0) -> list[dict]:  # fmt: skip
    """``need[size]`` decoys of ``size`` words: author uniform over those who can still give
    one, then a text of theirs long enough, then a seeded start; spans never overlap within a
    text, and each author keeps at least ``keep`` words out of the decoys (their reference)."""
    taken: dict[str, list[tuple[int, int]]] = {}
    left = {a: sum(len(w) for _, w in texts) - keep for a, texts in pool.items()}
    out = []
    for size in sorted(need, reverse=True):
        tries = 0
        while sum(d["words"] == size for d in out) < need[size]:
            authors = sorted(
                a
                for a, ts in pool.items()
                if left[a] >= size and any(len(w) >= size for _, w in ts)
            )
            tries += 1
            if not authors or tries > 100 * need[size] + 1000:
                raise SystemExit(f"cannot place {need[size]} non-overlapping {size}-word decoys")
            a = rng.choice(authors)
            src, words = rng.choice(sorted((s, w) for s, w in pool[a] if len(w) >= size))
            start = rng.randrange(0, len(words) - size + 1)
            if any(start < e and s < start + size for s, e in taken.get(src, [])):
                continue
            taken.setdefault(src, []).append((start, start + size))
            left[a] -= size
            out.append({"author": a, "source": src, "start": start, "words": size,
                        "text": " ".join(words[start : start + size])})  # fmt: skip
    return out


def split_need(need: dict[int, int], share: float) -> tuple[dict[int, int], dict[int, int]]:
    """Decoys per size from candidates (``share``, rounded up) and from controls (the rest)."""
    cand = {s: math.ceil(n * share) for s, n in need.items()}
    return cand, {s: n - cand[s] for s, n in need.items()}


def seal(bom: list[dict], decoys: list[dict], rng: random.Random) -> tuple[list[dict], dict]:
    """(sealed set, key). Ids are random hex, the order shuffled; nothing in a sealed row says
    which kind it is."""
    rows, key = [], {}
    for item in [*({"kind": "bom", **c} for c in bom), *({"kind": "decoy", **d} for d in decoys)]:
        i = secrets.token_hex(8)
        while i in key:
            i = secrets.token_hex(8)
        rows.append({"id": i, "words": len(item["text"].split()), "text": item["text"]})
        key[i] = ({"kind": "bom", "chunk_id": item["chunk_id"]} if item["kind"] == "bom" else
                  {"kind": "decoy", "author": item["author"], "source": item["source"],
                   "start": item["start"], "words": item["words"]})  # fmt: skip
    rng.shuffle(rows)
    return rows, key


def need_for(bom: list[dict], ratio: float) -> dict[int, int]:
    sizes: dict[int, int] = {}
    for c in bom:
        sizes[c["chunk_words"]] = sizes.get(c["chunk_words"], 0) + 1
    return {s: math.ceil(n * ratio) for s, n in sizes.items()}


def write(rows: list[dict], key: dict, decoys: list[dict], key_path: Path, sealed: Path,
          out: Path, meta: dict) -> dict:  # fmt: skip
    kp = outside_repo(key_path)
    kp.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(kp.parent, 0o700)
    fd = os.open(kp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(key, f, indent=1, sort_keys=True)
    sealed.parent.mkdir(parents=True, exist_ok=True)
    sealed.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out.mkdir(parents=True, exist_ok=True)
    doc = {**meta, "key_sha256": sha256(kp), "sealed_sha256": sha256(sealed),
           "sealed_ids": len(rows), "bom_chunks": sum(v["kind"] == "bom" for v in key.values()),
           "decoys": len(decoys),
           "decoys_by_size": {str(s): sum(d["words"] == s for d in decoys)
                              for s in sorted({d["words"] for d in decoys})}}  # fmt: skip
    (out / "seal.json").write_text(json.dumps(doc, indent=1) + "\n")
    spans = sorted({(d["source"], d["start"], d["start"] + d["words"]) for d in decoys})
    held = {
        "rule": "leave these word spans out of every reference profile and model",
        "spans": [{"source": s, "start": a, "end": b} for s, a, b in spans],
    }
    (out / "withheld.json").write_text(json.dumps(held, indent=1) + "\n")
    return doc


def decoy_pool(cfg: dict) -> dict[str, list[tuple[str, list[str]]]]:
    """Author -> [(source, masked words)] for the registered pool: public candidate texts of
    candidates with reliable samples, and the control texts named by ``blind.decoy_pool``."""
    import pyarrow.parquet as pq

    from reuse.exact import masked_text
    from segment.build import original_words

    b = cfg["blind"]["decoy_pool"]
    lines = Path("data/kjv_mask/candidates/spans.jsonl").read_text().splitlines()
    spans = {r["id"]: r["spans"] for r in map(json.loads, lines)}
    who = {
        r["id"]: r["candidate"]
        for r in json.loads(Path("data/candidates/sources.json").read_text())
    }
    pool: dict[str, list] = {}
    for p in sorted(Path("data/candidates/clean").glob("*.txt")):
        src = p.stem.split("__")[0]
        if who.get(src) not in b["candidates"]:
            continue
        sid = f"cand:{p.stem}"
        if sid not in spans:
            raise SystemExit(f"no KJV mask for {sid}")
        words = original_words(p.read_text(encoding="utf-8"), spans[sid])
        pool.setdefault(who[src], []).append((f"candidates/clean/{p.name}", words))
    rows = pq.read_table("data/catalog/catalog.parquet", columns=["work_id", "author_norm"])
    cat = {r["work_id"]: r["author_norm"] for r in rows.to_pylist()}
    for f in b["controls"]:
        for ln in Path(f).read_text().splitlines():
            w = json.loads(ln)["work_id"]
            a = cat.get(w)
            if a:
                pool.setdefault(f"control:{a}", []).append((w, masked_text([w]).split()))
    return pool


def main(argv: list[str] | None = None) -> int:
    from metadata.config import derive_seed, stamp
    from metadata.config import load as load_config

    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--key", type=Path, default=KEY)
    a = ap.parse_args(argv)
    cfg = load_config()
    if "blind" not in cfg:
        raise SystemExit("config has no blind: block; Amendment 32 must be filed first")
    if (OUT / "seal.json").exists():
        raise SystemExit("data/blind/seal.json exists: the set is sealed once")
    outside_repo(a.key)
    rng = random.Random(derive_seed(cfg["blind"]["seal_seed"], cfg))
    bom = [json.loads(ln) for ln in CHUNKS.read_text().splitlines()]
    b = cfg["blind"]
    bom = [c for c in bom if c["scheme"] in b["sealed_schemes"] and c["chunk_words"]
           in b["sealed_sizes"] and not c["partial"]]  # fmt: skip
    pool = decoy_pool(cfg)
    cand_need, ctrl_need = split_need(need_for(bom, b["decoy_ratio"]), b["candidate_share"])
    decoys = pick_decoys({a: t for a, t in pool.items() if not a.startswith("control:")},
                         cand_need, rng, keep=cfg["candidates"]["min_masked_words"])  # fmt: skip
    decoys += pick_decoys({a: t for a, t in pool.items() if a.startswith("control:")},
                          ctrl_need, rng)  # fmt: skip
    rows, key = seal(bom, decoys, rng)
    doc = write(rows, key, decoys, a.key, SEALED, OUT, stamp())
    print(f"sealed {doc['sealed_ids']} ids ({doc['bom_chunks']} chunks, {doc['decoys']} decoys); "
          f"key -> {a.key} (sha256 {doc['key_sha256'][:12]}); commit data/blind/")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main())
