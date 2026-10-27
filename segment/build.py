"""Segments, fixed-length chunks and the discovery/confirmation split (BOM-17).

Pre-registration 4.5: the Book of Mormon is segmented three ways -- by internal narrator, by
dictation order and by scribe -- each also cut into fixed 2,000- and 5,000-word chunks
(``segmentation.chunk_words``). Before the blind run, 5,000-word chunks are assigned to a
*discovery* or a *confirmation* half by a seeded draw stratified by narrator
(``segmentation.split``); the assignment file and its SHA-256 are committed before any Book of
Mormon scoring.

Text: the 1830 edition (4.1's first printing), its KJV spans removed by BOM-16 (attribution and
dating read original spans only, 4.4), with artifact-only normalisation (``ocr_fix.normalize``;
the 1830 text is post-1780). Boundaries: ``data/bom/segments/boundaries.json`` (BOM-17, with its
published SHA-256). Words are counted with Amendment 2's tokenisation.

Chunking walks each segment's original-span words in text order and cuts every ``n`` words. A
final remainder shorter than ``n`` is kept as a ``partial`` chunk and is never drawn into the
split. The ``dictation_order`` scheme walks paragraphs in dictation order rather than printed
order, which is the point of it.

The split: within each narrator, that narrator's full 5,000-word chunks are shuffled with
``random.Random(seed)`` -- one generator, narrators taken in alphabetical order, chunks in
printed order before shuffling -- and the first half (rounded down) goes to discovery, the
rest to confirmation. A narrator with a single full chunk sends it to confirmation, so the
sweep never sees a narrator's only sample.

Usage::

    python -m segment.build --masks data/kjv_mask/bom/spans.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

from kjv_mask.align import _WORD
from metadata.config import load as load_config
from metadata.config import sha256_of_config
from ocr_fix.normalize import artifacts

EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
BOUNDARIES = Path("data/bom/segments/boundaries.json")
OUT = Path("data/bom/segments")


def original_words(text: str, spans: list[dict]) -> list[str]:
    """Words of ``text`` outside every masked span, artifact-normalised."""
    keep, pos = [], 0
    for s in sorted(spans, key=lambda s: s["start"]):
        keep.append(text[pos : s["start"]])
        pos = max(pos, s["end"])
    keep.append(text[pos:])
    clean, _ = artifacts(" ".join(keep))
    return [m.group(0) for m in _WORD.finditer(clean)]


def chunk(words: list[tuple[int, str]], n: int) -> list[dict]:
    """Cut (paragraph seq, word) pairs into n-word chunks; the remainder is a partial chunk."""
    out = []
    for i in range(0, len(words), n):
        part = words[i : i + n]
        out.append(
            {
                "seq_first": part[0][0],
                "seq_last": part[-1][0],
                "words": len(part),
                "partial": len(part) < n,
                "text": " ".join(w for _, w in part),
            }
        )
    return out


def split(chunks: list[dict], seed: int) -> dict[str, str]:
    rng = random.Random(seed)
    by_narrator: dict[str, list[dict]] = {}
    for c in chunks:
        if not c["partial"]:
            by_narrator.setdefault(c["label"], []).append(c)
    assign = {}
    for narrator in sorted(by_narrator):
        cs = sorted(by_narrator[narrator], key=lambda c: c["seq_first"])
        rng.shuffle(cs)
        half = len(cs) // 2
        for i, c in enumerate(cs):
            assign[c["chunk_id"]] = "discovery" if i < half else "confirmation"
    return assign


def build(masks: Path) -> int:
    cfg = load_config()
    seg = cfg["segmentation"]
    spans = {}
    for ln in masks.read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    text = {
        r["seq"]: r["text"]
        for r in (json.loads(ln) for ln in EDITION.read_text().splitlines())
        if r["book"]
    }
    labels = [json.loads(ln) for ln in LABELS.read_text().splitlines()]
    words = {
        x["seq"]: original_words(text[x["seq"]], spans.get(f"bom:{x['seq']}", [])) for x in labels
    }
    total = sum(len(text[x["seq"]].split()) for x in labels)
    kept = sum(len(w) for w in words.values())

    chunks: list[dict] = []
    for scheme in seg["ways"]:
        key = {"narrator": "narrator", "dictation_order": "dictation_phase", "scribe": "scribe"}[
            scheme
        ]
        order = sorted(
            labels,
            key=(lambda x: x["dictation_position"]) if scheme == "dictation_order"
            else (lambda x: x["seq"]),
        )  # fmt: skip
        runs: list[tuple[str, list[tuple[int, str]]]] = []
        for x in order:
            ws = [(x["seq"], w) for w in words[x["seq"]]]
            if runs and runs[-1][0] == x[key]:
                runs[-1][1].extend(ws)
            else:
                runs.append((x[key], ws))
        for ri, (label, ws) in enumerate(runs):
            for n in seg["chunk_words"]:
                for ci, c in enumerate(chunk(ws, n)):
                    chunks.append({"chunk_id": f"{scheme}:{ri:03d}:{label}:{n}:{ci:03d}",
                                   "scheme": scheme, "label": label, "run": ri,
                                   "chunk_words": n, **c})  # fmt: skip

    sp = seg["split"]
    eligible = [
        c for c in chunks if c["scheme"] == sp["stratify_by"]
        and c["chunk_words"] == sp["applies_to_chunk_words"]
    ]  # fmt: skip
    assign = split(eligible, sp["seed"])
    for c in chunks:
        c["half"] = assign.get(c["chunk_id"])

    stamp = sha256_of_config()
    with (OUT / "chunks.jsonl").open("w") as fh:
        for c in chunks:
            fh.write(json.dumps({**c, "config_sha256": stamp}, ensure_ascii=False) + "\n")
    body = json.dumps(
        {"seed": sp["seed"], "stratify_by": sp["stratify_by"],
         "boundaries_sha256": hashlib.sha256(BOUNDARIES.read_bytes()).hexdigest(),
         "assignment": dict(sorted(assign.items()))},
        indent=1,
    ) + "\n"  # fmt: skip
    (OUT / "split.json").write_text(body)
    print(f"original words {kept:,} of {total:,} ({1 - kept / total:.1%} masked as KJV)")
    print(f"{len(chunks):,} chunks; split of {len(assign)} 5,000-word narrator chunks: "
          f"{sum(v == 'discovery' for v in assign.values())} discovery")  # fmt: skip
    print(f"split.json sha256 {hashlib.sha256(body.encode()).hexdigest()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--masks", type=Path, required=True)
    a = ap.parse_args(argv)
    return build(a.masks)


if __name__ == "__main__":
    sys.exit(main())
