"""Character error rate against hand-keyed text (BOM-14).

Pre-registration 4.3 excludes volumes whose estimated OCR character error rate exceeds
``corpus.ocr_max_cer``, and BOM-14 owed "hand-corrected pages" to estimate it. The corpus
already holds them: the Text Creation Partnership keyed ECCO and Evans by hand, double-keyed to
a stated accuracy far above any OCR, and many of the same works were also OCR'd by the Internet
Archive, HathiTrust or Harvard. A keyed text and an OCR copy of the same work printed in the
same year is a hand-corrected reference that cost nobody an afternoon.

The two copies are not always the same printing, so nothing assumes they line up. For each pair
``WINDOWS`` stretches of ``WINDOW`` characters are cut from the keyed text, each is located in
the OCR text by the word 4-grams they share, and the OCR stretch is fitted by local alignment.
CER is the edit distance over the keyed length, the reference, as usual. A window that finds
no anchor is counted as unaligned, not scored; a volume's CER is the median over its aligned
windows, so a window that lands on different wording in a different printing cannot move it,
and a volume with fewer than ``MIN_ALIGNED`` aligned windows is reported as unaligned.

Each keyed window is looked up twice, in the raw OCR and in the output of ``ocr_fix.clean``,
so the two are compared on the same passages: a paired measurement of what cleaning does. (A
first version cut the windows from the OCR side; cleaning changes the OCR's length, so raw and
cleaned got different windows and the comparison was noise.)

Usage::

    python -m ocr_fix.groundtruth pairs        # -> data/ocr_quality/groundtruth_pairs.jsonl
    python -m ocr_fix.groundtruth measure      # -> data/ocr_quality/groundtruth.parquet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from rapidfuzz.distance import Levenshtein
from rapidfuzz.fuzz import partial_ratio_alignment

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from ocr_fix import clean as cleaner

CATALOG = Path("data/catalog/catalog.parquet")
OUT_DIR = Path("data/ocr_quality")
PAIRS = OUT_DIR / "groundtruth_pairs.jsonl"
OUT = OUT_DIR / "groundtruth.parquet"
OCR_SOURCES = {"internet_archive", "hathitrust", "institutional_books"}

# Measurement design, not analytic thresholds: they set how precisely CER is estimated, and no
# exclusion reads them. Changing them changes the error bars, not what is excluded.
WINDOW = 400
WINDOWS = 20
MIN_ALIGNED = 5
MIN_VOTES = 2

_WS = re.compile(r"\s+")
_KEYED_MARKS = re.compile(r"[〈〉◊•∣¦]")
_LETTERS = re.compile(r"[a-z]+")


def norm_keyed(text: str) -> str:
    """Keyed text as a reader of the print would see it: long s as s, TCP gap marks dropped."""
    return _WS.sub(" ", _KEYED_MARKS.sub("", text.replace("ſ", "s"))).strip()


def norm_ocr(text: str) -> str:
    return _WS.sub(" ", text).strip()


def find_pairs() -> int:
    """Keyed TCP text and an OCR copy with the same title, author surname and year."""
    cols = ["work_id", "source", "title_norm", "author_norm", "year", "text_path", "genre_src"]
    rows = [r for r in pq.read_table(CATALOG, columns=cols).to_pylist() if r["text_path"]]
    keyed: dict[tuple, list] = defaultdict(list)
    ocr: dict[tuple, list] = defaultdict(list)
    for r in rows:
        if not r["title_norm"] or not r["year"]:
            continue
        key = (r["title_norm"][:60], (r["author_norm"] or "").split(",")[0], r["year"])
        if r["source"] == "tcp":
            keyed[key].append(r)
        elif r["source"] in OCR_SOURCES:
            ocr[key].append(r)
    out, used = [], set()
    for key in sorted(keyed.keys() & ocr.keys()):
        ref = keyed[key][0]  # several keyed copies of one title: take the first, consistently
        for o in ocr[key]:
            if o["work_id"] in used:
                continue
            used.add(o["work_id"])
            out.append(
                {
                    "ocr_id": o["work_id"],
                    "ocr_source": o["source"],
                    "ocr_path": o["text_path"],
                    "keyed_id": ref["work_id"],
                    "keyed_path": ref["text_path"],
                    "collection": ref["genre_src"],
                    "year": key[2],
                }
            )
    PAIRS.write_text("".join(json.dumps(p) + "\n" for p in out))
    print(f"{len(out):,} pairs -> {PAIRS}: {dict(Counter(p['ocr_source'] for p in out))}")
    return 0


def _grams(text: str) -> list[tuple[str, int]]:
    """Lowercase word 4-grams with the character offset of their first word."""
    words = [(m.group(0), m.start()) for m in _LETTERS.finditer(text.lower())]
    return [(" ".join(w for w, _ in words[i : i + 4]), words[i][1]) for i in range(len(words) - 3)]


def _index(text: str) -> dict[str, int]:
    idx: dict[str, int] = {}
    dup: set[str] = set()
    for g, off in _grams(text):
        if g in idx:
            dup.add(g)
        else:
            idx[g] = off
    for g in dup:  # a repeated 4-gram cannot say where a window belongs
        del idx[g]
    return idx


def letters(text: str) -> str:
    """Lowercase letters and single spaces only: what word-level features actually read."""
    return _WS.sub(" ", re.sub(r"[^a-z\s]", "", text.lower())).strip()


def window_cer(win: str, target: str, idx: dict[str, int]) -> tuple[float, float] | None:
    """(CER, letters-only CER) of the stretch of ``target`` that best matches ``win``.

    Plain CER counts every difference from the keying -- punctuation, capitals, ``&`` for
    ``and``, wording that differs between printings -- so it bounds OCR error from above.
    Letters-only CER drops case and punctuation, which is what word features see."""
    votes: Counter = Counter()
    for g, off in _grams(win):
        if g in idx:
            votes[(idx[g] - off) // 50] += 1
    if not votes:
        return None
    bin_, n = votes.most_common(1)[0]
    if n < MIN_VOTES:
        return None
    start = max(0, bin_ * 50 - WINDOW // 2)
    span = target[start : start + 2 * WINDOW + 100]
    al = partial_ratio_alignment(win, span)
    if al is None:
        return None
    lo = start + al.dest_start
    best, n_best = min(
        (Levenshtein.distance(win, target[lo : lo + n_]), n_)
        for n_ in range(int(len(win) * 0.9), int(len(win) * 1.1) + 1, 4)
    )
    lw = letters(win)
    lt = letters(target[lo : lo + n_best])
    return best / len(win), Levenshtein.distance(lw, lt) / max(1, len(lw))


def _windows(text: str, seed: str) -> list[str]:
    rng = random.Random(seed)
    lo, hi = int(len(text) * 0.05), int(len(text) * 0.95) - WINDOW
    if hi <= lo:
        return []
    return [text[s : s + WINDOW] for s in sorted(rng.randrange(lo, hi) for _ in range(WINDOWS))]


def _measure(pair: dict) -> dict:
    cfg_seed = load_config()["seed"]
    seed = f"{cfg_seed}:{hashlib.sha256(pair['ocr_id'].encode()).hexdigest()[:12]}"
    raw = Path(pair["ocr_path"]).read_text(encoding="utf-8", errors="replace")
    keyed = norm_keyed(Path(pair["keyed_path"]).read_text(encoding="utf-8", errors="replace"))
    cleaned, counts = cleaner.clean(raw)
    result = {**{k: pair[k] for k in ("ocr_id", "ocr_source", "keyed_id", "collection", "year")}}
    wins = _windows(keyed, seed)
    for label, text in (("raw", norm_ocr(raw)), ("clean", norm_ocr(cleaned))):
        idx = _index(text)
        cers, lcers = [], []
        for w in wins:
            got = window_cer(w, text, idx)
            if got is not None:
                cers.append(got[0])
                lcers.append(got[1])
        enough = len(cers) >= MIN_ALIGNED
        result[f"aligned_{label}"] = len(cers)
        result[f"cer_{label}"] = statistics.median(cers) if enough else None
        result[f"letter_cer_{label}"] = statistics.median(lcers) if enough else None
    result.update(cleaner.proxies(raw))  # the same function the cleaning run applies
    result.update({f"fix_{k}": v for k, v in counts.items()})
    return result


PROXY = cleaner.PROXY
SCHEMA = pa.schema(
    [
        ("ocr_id", pa.string()),
        ("ocr_source", pa.string()),
        ("keyed_id", pa.string()),
        ("collection", pa.string()),
        ("year", pa.int32()),
        ("aligned_raw", pa.int32()),
        ("cer_raw", pa.float64()),
        ("letter_cer_raw", pa.float64()),
        ("aligned_clean", pa.int32()),
        ("cer_clean", pa.float64()),
        ("letter_cer_clean", pa.float64()),
        *[(k, pa.float64()) for k in PROXY],
        ("period_lexicon_rate", pa.float64()),
        ("fix_header_lines", pa.int64()),
        ("fix_hyphens", pa.int64()),
        ("fix_long_s", pa.int64()),
    ]
)


def measure(workers: int, limit: int | None) -> int:
    pairs = [json.loads(ln) for ln in PAIRS.read_text().splitlines()]
    if limit:
        pairs = pairs[:limit]
    rows = []
    with ProcessPoolExecutor(workers) as pool:
        for i, r in enumerate(pool.map(_measure, pairs, chunksize=4), 1):
            rows.append(r)
            if i % 250 == 0:
                print(f"  {i:,}/{len(pairs):,}", flush=True)
    table = pa.Table.from_pylist(rows, schema=SCHEMA)
    pq.write_table(table.replace_schema_metadata({"config_sha256": sha256_of_config()}), OUT)
    ok = [r for r in rows if r["cer_raw"] is not None]
    print(f"{len(rows):,} pairs, {len(ok):,} aligned -> {OUT}")
    if ok:
        raw = statistics.median(r["cer_raw"] for r in ok)
        both = [r for r in ok if r["cer_clean"] is not None]
        cl = statistics.median(r["cer_clean"] for r in both) if both else float("nan")
        print(f"median CER raw {raw:.3f}, cleaned {cl:.3f}")
        lr = statistics.median(r["letter_cer_raw"] for r in ok)
        lc = statistics.median(r["letter_cer_clean"] for r in both) if both else float("nan")
        print(f"median letters-only CER raw {lr:.3f}, cleaned {lc:.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pairs")
    m = sub.add_parser("measure")
    m.add_argument("--workers", type=int, default=6)
    m.add_argument("--limit", type=int)
    a = ap.parse_args(argv)
    return find_pairs() if a.cmd == "pairs" else measure(a.workers, a.limit)


if __name__ == "__main__":
    sys.exit(main())
