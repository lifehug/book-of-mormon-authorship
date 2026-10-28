"""Mask KJV quotation in the Book of Mormon, the candidates and the controls (BOM-16).

4.4: Book of Mormon, candidate and control texts are aligned to the KJV with passim, and the
proportion of each text masked is reported. Settings are the frozen ones in
``kjv_mask.passim`` (Amendment 2, ``min_match`` selected on planted quotations, validated on
200 alignments by ``kjv_mask.validate``). This refuses to run on the Book of Mormon until that
validation has passed, because Amendment 2 freezes the settings before any Book of Mormon text
is masked.

Input is BOM-15's normalised text, or the same artifact-only normalisation applied here to
texts that never went through the corpus pipeline (the 1830 edition, the candidate samples).

passim's document-frequency cap (``max_df``) counts documents across a whole run, so a run's
size changes which phrases can seed an alignment. Texts therefore go through in batches of about
``BATCH_WORDS`` words -- the scale of the validation run -- and each batch is cached by its
contents, so the job resumes batch by batch.

**Long texts are cut into pieces.** passim's memory grows with document length: a 336,742-word
Harvard volume exhausted a 6 GB heap, and control volumes run to 2.5 million words. A text over
``PIECE_WORDS`` words is aligned as pieces of that length, each overlapping the next by
``PIECE_OVERLAP`` words, and the spans are mapped back onto the whole text's offsets (duplicates
in an overlap resolve as within a run, ``align.resolve``). Alignment is local -- matches join
across at most 100 characters -- so cutting does not change what matches; a quotation shorter
than the overlap that crosses a cut is found whole in one piece. What can shift is the
document-frequency count, since pieces count as documents; registered by Amendment 6
(``kjv_mask.passim_implementation``). Texts are read when their batch is built, not all held in
memory (the control sets are about 1.65 billion words). A batch passim cannot finish at any
heap size is aligned again with each text cut into thirds (``mask_resilient``); those batches are
listed in the report under ``split_further``.

Outputs carry offsets, verse references, classes and identities, never text, so they are
public even where the text is not (the Joseph Smith Papers samples):
``data/kjv_mask/<group>/spans.jsonl`` and ``report.json`` (share of words masked per text).

Usage::

    python -m kjv_mask.run bom
    python -m kjv_mask.run candidates
    python -m kjv_mask.run controls
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import _WORD, Span, mask, registered_params, resolve
from kjv_mask.validate import OUT as VALIDATION
from kjv_mask.validate import PASS_PRECISION
from metadata.config import sha256_of_config
from ocr_fix.normalize import artifacts

OUT = Path("data/kjv_mask")
WORK = Path("data/corpus/kjv_mask_runs")
BATCH_WORDS = 720_000
PIECE_WORDS = 150_000  # registered, Amendment 6
PIECE_OVERLAP = 500
SPLIT_PARTS, SPLIT_DEPTH = 3, 2  # registered, Amendment 6
EDITION = Path("data/bom/1830/edition_1830.jsonl")
SAMPLES = Path("data/private/candidates/samples")
CONTROLS = Path("data/controls")
_SPACE_WORD = re.compile(r"\S+")


def validation_passed() -> bool:
    if not VALIDATION.exists():
        return False
    rows = [json.loads(ln) for ln in VALIDATION.read_text().splitlines()]
    ok = [r for r in rows if r.get("review") and r["review"].get("derived") != "PARSE_FAIL"]
    if len(ok) < len(rows) or not ok:
        return False
    derived = sum(1 for r in ok if r["review"]["derived"] in ("verbatim", "paraphrase"))
    return derived / len(ok) >= PASS_PRECISION


def _in_memory(doc_id: str, text: str) -> dict:
    return {"id": doc_id, "words": len(text.split()), "load": lambda: text}


def _from_file(doc_id: str, path: Path, words: int) -> dict:
    return {"id": doc_id, "words": words, "load": lambda: path.read_text(encoding="utf-8")}


def _docs(group: str) -> list[dict]:
    """(id, word count, loader) per text; the text itself is read only when needed."""
    if group == "bom":
        return [
            _in_memory(f"bom:{r['seq']}", artifacts(r["text"])[0])
            for r in (json.loads(ln) for ln in EDITION.read_text().splitlines())
            if r["book"]
        ]
    if group == "candidates":
        # assembled Joseph Smith Papers samples, plus BOM-13's printed units as cleaned and
        # normalised by ocr_fix.candidates (already artifact-normalised)
        docs = [
            _in_memory(f"cand:{p.stem}", artifacts(p.read_text(encoding="utf-8"))[0])
            for p in sorted(SAMPLES.glob("*.txt"))
        ]
        for d in (Path("data/candidates/clean"), Path("data/private/candidates/clean")):
            docs += [
                _in_memory(f"cand:{p.stem}", p.read_text(encoding="utf-8"))
                for p in sorted(d.glob("*.txt"))
            ]
        return docs
    if group == "controls":
        from ocr_fix.normalize import norm_path

        words = {}
        for f in sorted(CONTROLS.glob("*.jsonl")):
            for ln in f.read_text().splitlines():
                m = json.loads(ln)
                words[m["work_id"]] = m["words"] or 0
        cat = pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
        ).to_pylist()
        return [
            _from_file(r["work_id"], norm_path(r), words[r["work_id"]])
            for r in cat
            if r["work_id"] in words
        ]
    raise SystemExit(f"unknown group {group}")


def piece_ranges(text: str) -> list[tuple[int, int]]:
    """Character ranges of the pieces a text is aligned as: one range unless it is long."""
    starts = [m.start() for m in _SPACE_WORD.finditer(text)]
    if len(starts) <= PIECE_WORDS:
        return [(0, len(text))]
    out = []
    for k in range(0, len(starts), PIECE_WORDS):
        end_word = k + PIECE_WORDS + PIECE_OVERLAP
        end = starts[end_word] if end_word < len(starts) else len(text)
        out.append((starts[k], end))
        if end == len(text):
            break
    return out


def _n_pieces(words: int) -> int:
    return 1 if words <= PIECE_WORDS else -(-words // PIECE_WORDS)


def _units(docs: list[dict]) -> list[tuple[dict, int, int]]:
    """(doc, piece index, approximate words) for every piece, in document order."""
    out = []
    for d in docs:
        n = _n_pieces(d["words"])
        for k in range(n):
            w = d["words"] if n == 1 else min(PIECE_WORDS, d["words"] - k * PIECE_WORDS)
            out.append((d, k, w + (PIECE_OVERLAP if k < n - 1 else 0)))
    return out


def _batches(units: list[tuple[dict, int, int]]) -> list[list[tuple[dict, int, int]]]:
    out, cur, n = [], [], 0
    for u in units:
        if cur and n + u[2] > BATCH_WORDS:
            out.append(cur)
            cur, n = [], 0
        cur.append(u)
        n += u[2]
    if cur:
        out.append(cur)
    return out


def _materialise(batch: list[tuple[dict, int, int]]) -> tuple[list[dict], dict[str, tuple]]:
    """passim documents for a batch, and piece id -> (doc id, offset into the whole text)."""
    texts: dict[str, str] = {}
    ranges: dict[str, list[tuple[int, int]]] = {}
    docs, where = [], {}
    for d, k, _ in batch:
        if d["id"] not in texts:
            texts[d["id"]] = d["load"]()
            ranges[d["id"]] = piece_ranges(texts[d["id"]])
        rs = ranges[d["id"]]
        if k >= len(rs):  # the estimate from the word count ran one piece long
            continue
        a, b = rs[k]
        pid = d["id"] if len(rs) == 1 else f"{d['id']}#p{k}"
        docs.append({"id": pid, "text": texts[d["id"]][a:b]})
        where[pid] = (d["id"], a)
    return docs, where


def _counts(text: str, spans: list[Span]) -> dict:
    total = sum(1 for _ in _WORD.finditer(text))
    masked = sum(1 for s in spans for _ in _WORD.finditer(text[s.start : s.end]))
    return {
        "words": total,
        "masked_words": masked,
        "verbatim_spans": sum(s.kind == "verbatim" for s in spans),
        "paraphrase_spans": sum(s.kind == "paraphrase" for s in spans),
    }


def _split(doc: dict, parts: int) -> list[tuple[dict, int]]:
    """``doc`` cut into ``parts`` overlapping sub-pieces, each with its offset into ``doc``."""
    text = doc["text"]
    starts = [m.start() for m in _SPACE_WORD.finditer(text)]
    size = -(-len(starts) // parts)
    out = []
    for k in range(0, len(starts), size):
        end_word = k + size + PIECE_OVERLAP
        end = starts[end_word] if end_word < len(starts) else len(text)
        out.append(({"id": f"{doc['id']}/s{k // size}", "text": text[starts[k] : end]}, starts[k]))
        if end == len(text):
            break
    return out


def mask_resilient(
    docs: list[dict], work: Path, params: dict, depth: int = 0, log: list | None = None
) -> dict[str, list[Span]]:
    """``mask``, or, if passim fails on the batch at every heap size, each text cut into thirds
    and aligned on its own (twice at most). Verse-by-verse Bible commentaries (the 1826
    *Recensio synoptica*) generate so many candidate alignments that passim's Python workers
    die whatever the heap; alignment is local, so smaller pieces find the same quotations."""
    try:
        return mask(docs, work, params)
    except RuntimeError:
        if depth >= SPLIT_DEPTH:
            raise
    if log is not None:
        log.append({"depth": depth + 1, "texts": [d["id"] for d in docs]})
    out: dict[str, list[Span]] = {d["id"]: [] for d in docs}
    for d in docs:
        for sub, offset in _split(d, SPLIT_PARTS):
            for spans in mask_resilient([sub], work, params, depth + 1, log).values():
                out[d["id"]] += [
                    replace(x, start=x.start + offset, end=x.end + offset) for x in spans
                ]
    return {k: resolve(v) for k, v in out.items()}


def run(group: str, docs_of: Callable[[str], list[dict]] = _docs) -> int:
    if not validation_passed():
        raise SystemExit("kjv_mask.validate has not passed; settings are not frozen yet")
    params = registered_params()
    docs = docs_of(group)
    out_dir = OUT / group
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = sha256_of_config()
    batches = _batches(_units(docs))
    found: dict[str, list[Span]] = {d["id"]: [] for d in docs}
    split_log: list[dict] = []
    for i, batch in enumerate(batches, 1):
        pdocs, where = _materialise(batch)
        for pid, spans in mask_resilient(pdocs, WORK / group, params, log=split_log).items():
            doc_id, offset = where[pid]
            found[doc_id] += [replace(s, start=s.start + offset, end=s.end + offset) for s in spans]
        print(f"  batch {i}/{len(batches)}", flush=True)
    report = {}
    with (out_dir / "spans.jsonl").open("w") as fh:
        for d in docs:
            ss = resolve(found[d["id"]])
            fh.write(json.dumps({"id": d["id"], "spans": [s.__dict__ for s in ss],
                                 "config_sha256": stamp}) + "\n")  # fmt: skip
            report[d["id"]] = _counts(d["load"](), ss)
    words = sum(r["words"] for r in report.values())
    masked = sum(r["masked_words"] for r in report.values())
    summary = {"group": group, "texts": len(report), "words": words, "masked_words": masked,
               "share_masked": masked / words if words else None, "params": params,
               "piece_words": PIECE_WORDS, "piece_overlap": PIECE_OVERLAP,
               "split_further": split_log,
               "config_sha256": stamp, "per_text": report}  # fmt: skip
    (out_dir / "report.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(f"{group}: {masked:,} of {words:,} words masked ({summary['share_masked']:.2%})")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__)
        return 1
    return run(args[0])


if __name__ == "__main__":
    sys.exit(main())
