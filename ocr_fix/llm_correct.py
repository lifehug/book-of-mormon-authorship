"""Does an LLM correct OCR, measured against keyed text? (BOM-14)

BOM-14 asks for LLM correction on a sample with its error rate measured against hand-corrected
pages. The pages are the TCP keyings (``ocr_fix.groundtruth``). For ``N`` seeded windows, one
per volume, the cleaned OCR stretch matching a keyed window is given to the model with its
print year, the model is told to fix recognition errors only and keep period spelling, and the
reply is scored against the keyed window. Before and after are the same passage.

The question this answers is whether correction is worth applying to the corpus, which would
be about 160 GB of text through a model. It is not applied here. Only scores are written:
some windows are Harvard text, which may not be redistributed.

A reply that fails transiently (an outage, a usage limit) is recorded as ``failed`` and
retried by the next run, never scored.

Usage::

    python -m ocr_fix.llm_correct run [--n 100] [--model sonnet]
    python -m ocr_fix.llm_correct report
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from metadata.genre import _TRANSIENT
from ocr_fix import clean as cleaner
from ocr_fix.groundtruth import PAIRS, _index, _windows, cer, locate, norm_keyed, norm_ocr

OUT = Path("data/ocr_quality/llm_correction.jsonl")

PROMPT = (
    "Below is OCR output of a passage from a book printed in {year}. Correct the character "
    "recognition errors only. Keep the original spelling, capitalisation and punctuation of "
    "the period; do not modernise, paraphrase, or add or remove words. The passage starts and "
    "ends mid-sentence; leave the ends as they are. Reply with the corrected passage and "
    "nothing else.\n\n{text}"
)


def _sample(n: int) -> list[dict]:
    """``n`` (pair, keyed window, OCR stretch) items, one per volume, seeded."""
    seed = load_config()["seed"]
    pairs = [json.loads(ln) for ln in PAIRS.read_text().splitlines()]
    random.Random(seed).shuffle(pairs)
    items = []
    for p in pairs:
        keyed = norm_keyed(Path(p["keyed_path"]).read_text(encoding="utf-8", errors="replace"))
        raw = Path(p["ocr_path"]).read_text(encoding="utf-8", errors="replace")
        ocr = norm_ocr(cleaner.clean(raw)[0])
        idx = _index(ocr)
        for w in _windows(keyed, f"{seed}:llm:{p['ocr_id']}"):
            hyp = locate(w, ocr, idx)
            if hyp is not None:
                items.append({**p, "keyed": w, "ocr": hyp})
                break
        if len(items) >= n:
            break
    return items


def _ask(prompt: str, model: str) -> str | None:
    try:
        done = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=180,
            stdin=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001
        return None
    text = done.stdout.strip()
    if done.returncode != 0 or not text or _TRANSIENT.search(text.lower()):
        return None
    return text


def run(n: int, model: str, workers: int) -> int:
    done = {}
    if OUT.exists():
        for ln in OUT.read_text().splitlines():
            r = json.loads(ln)
            if r["status"] == "scored":
                done[r["ocr_id"]] = r
    items = [it for it in _sample(n) if it["ocr_id"] not in done]
    print(f"{len(done)} scored already, {len(items)} to ask {model}", flush=True)

    def one(it: dict) -> dict:
        reply = _ask(PROMPT.format(year=it["year"], text=it["ocr"]), model)
        base = {"ocr_id": it["ocr_id"], "ocr_source": it["ocr_source"], "model": model}
        if reply is None:
            return {**base, "status": "failed"}
        before, lbefore = cer(it["keyed"], it["ocr"])
        after, lafter = cer(it["keyed"], reply)
        return {
            **base,
            "status": "scored",
            "cer_before": before,
            "cer_after": after,
            "letter_cer_before": lbefore,
            "letter_cer_after": lafter,
            "len_ratio": len(reply) / max(1, len(it["ocr"])),
        }

    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(one, items))
    rows = list(done.values()) + results
    stamp = sha256_of_config()
    OUT.write_text("".join(json.dumps({**r, "config_sha256": stamp}) + "\n" for r in rows))
    return report()


def report() -> int:
    rows = [json.loads(ln) for ln in OUT.read_text().splitlines()]
    ok = [r for r in rows if r["status"] == "scored"]
    print(f"{len(ok)} scored, {len(rows) - len(ok)} failed transiently (retried next run)")
    if not ok:
        return 0
    for k in ("cer", "letter_cer"):
        b = [r[f"{k}_before"] for r in ok]
        a = [r[f"{k}_after"] for r in ok]
        better = sum(x < y for x, y in zip(a, b, strict=True))
        worse = sum(x > y for x, y in zip(a, b, strict=True))
        print(
            f"{k:<11} median before {statistics.median(b):.3f} after {statistics.median(a):.3f}; "
            f"mean {statistics.fmean(b):.3f} -> {statistics.fmean(a):.3f}; "
            f"better {better}, worse {worse}, same {len(ok) - better - worse}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--n", type=int, default=100)
    r.add_argument("--model", default="sonnet")
    r.add_argument("--workers", type=int, default=4)
    sub.add_parser("report")
    a = ap.parse_args(argv)
    return run(a.n, a.model, a.workers) if a.cmd == "run" else report()


if __name__ == "__main__":
    sys.exit(main())
