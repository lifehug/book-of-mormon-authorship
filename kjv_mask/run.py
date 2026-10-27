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
import sys
from pathlib import Path

import pyarrow.parquet as pq

from kjv_mask.align import _WORD, mask, registered_params
from kjv_mask.validate import OUT as VALIDATION
from kjv_mask.validate import PASS_PRECISION
from metadata.config import sha256_of_config
from ocr_fix.normalize import artifacts

OUT = Path("data/kjv_mask")
WORK = Path("data/corpus/kjv_mask_runs")
BATCH_WORDS = 720_000
EDITION = Path("data/bom/1830/edition_1830.jsonl")
SAMPLES = Path("data/private/candidates/samples")
CONTROLS = Path("data/controls")


def validation_passed() -> bool:
    if not VALIDATION.exists():
        return False
    rows = [json.loads(ln) for ln in VALIDATION.read_text().splitlines()]
    ok = [r for r in rows if r.get("review") and r["review"].get("derived") != "PARSE_FAIL"]
    if len(ok) < len(rows) or not ok:
        return False
    derived = sum(1 for r in ok if r["review"]["derived"] in ("verbatim", "paraphrase"))
    return derived / len(ok) >= PASS_PRECISION


def _docs(group: str) -> list[dict]:
    if group == "bom":
        return [
            {"id": f"bom:{r['seq']}", "text": artifacts(r["text"])[0]}
            for r in (json.loads(ln) for ln in EDITION.read_text().splitlines())
            if r["book"]
        ]
    if group == "candidates":
        # assembled Joseph Smith Papers samples, plus BOM-13's printed units as cleaned and
        # normalised by ocr_fix.candidates (already artifact-normalised)
        docs = [
            {"id": f"cand:{p.stem}", "text": artifacts(p.read_text(encoding="utf-8"))[0]}
            for p in sorted(SAMPLES.glob("*.txt"))
        ]
        for d in (Path("data/candidates/clean"), Path("data/private/candidates/clean")):
            docs += [
                {"id": f"cand:{p.stem}", "text": p.read_text(encoding="utf-8")}
                for p in sorted(d.glob("*.txt"))
            ]
        return docs
    if group == "controls":
        from ocr_fix.normalize import norm_path

        ids = set()
        for f in sorted(CONTROLS.glob("*.txt")):
            ids |= set(f.read_text().split())
        cat = pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
        ).to_pylist()
        docs = []
        for r in cat:
            if r["work_id"] in ids:
                text = norm_path(r).read_text(encoding="utf-8")
                docs.append({"id": r["work_id"], "text": text})
        return docs
    raise SystemExit(f"unknown group {group}")


def _batches(docs: list[dict]) -> list[list[dict]]:
    out, cur, n = [], [], 0
    for d in docs:
        w = len(d["text"].split())
        if cur and n + w > BATCH_WORDS:
            out.append(cur)
            cur, n = [], 0
        cur.append(d)
        n += w
    if cur:
        out.append(cur)
    return out


def run(group: str) -> int:
    if not validation_passed():
        raise SystemExit("kjv_mask.validate has not passed; settings are not frozen yet")
    params = registered_params()
    docs = _docs(group)
    out_dir = OUT / group
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = sha256_of_config()
    report = {}
    batches = _batches(docs)
    with (out_dir / "spans.jsonl").open("w") as fh:
        for i, batch in enumerate(batches, 1):
            spans = mask(batch, WORK / group, params)
            for d in batch:
                ss = spans[d["id"]]
                fh.write(json.dumps({"id": d["id"], "spans": [s.__dict__ for s in ss],
                                     "config_sha256": stamp}) + "\n")  # fmt: skip
                total = sum(1 for _ in _WORD.finditer(d["text"]))
                masked = sum(1 for s in ss for _ in _WORD.finditer(d["text"][s.start : s.end]))
                report[d["id"]] = {
                    "words": total,
                    "masked_words": masked,
                    "verbatim_spans": sum(s.kind == "verbatim" for s in ss),
                    "paraphrase_spans": sum(s.kind == "paraphrase" for s in ss),
                }
            print(f"  batch {i}/{len(batches)}", flush=True)
    words = sum(r["words"] for r in report.values())
    masked = sum(r["masked_words"] for r in report.values())
    summary = {"group": group, "texts": len(report), "words": words, "masked_words": masked,
               "share_masked": masked / words if words else None, "params": params,
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
