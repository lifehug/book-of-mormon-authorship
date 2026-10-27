"""Rejoin words that OCR delivery broke into fragments (BOM-14).

NYS Historic Newspapers' text view delivers the *Wayne Sentinel* with words split at random:
``h a s r ec e n tly b een``, ``re -e le cted``. ``ocr_fix.score`` measured 30% of its tokens as
lone letters against 4% in Chronicling America (``data/ocr_quality/SOURCES.md``). A 4-gram over
that is noise, and BOM-23, BOM-24 and BOM-33 read the Sentinel at n-gram level.

A line is treated as fragmented when at least ``FRAGMENT_SHARE`` of its alphabetic tokens are
short fragments (``FRAGMENT_LEN`` letters or fewer and not a common short word). Its alphabetic
stretches are then joined and re-split into words by dynamic programming, each word costing the
negative log of its token frequency in the period lexicon (``ocr_fix.lexicon``) and anything outside
the lexicon a steep per-letter cost, so the split prefers a few common words over many rare
ones. Lines that are not fragmented are returned unchanged.

What this cannot fix: interleaved columns, where two stories alternate within a line. Reading
order needs the page layout -- word coordinates from ALTO or the page image -- which is BOM-50.

Measured, not assumed: ``evaluate`` breaks clean keyed text at random the way the Sentinel is
broken and reports how many words come back exactly (``data/ocr_quality/defragment_eval.json``).
Thresholds are listed in ``pending_amendment`` (``ocr_fix.defragment``).

Usage::

    python -m ocr_fix.defragment evaluate
    python -m ocr_fix.defragment run data/newspapers/wayne_sentinel/text \
        -o data/newspapers/wayne_sentinel/cleaned

``run`` re-segments, then applies ``ocr_fix.clean`` (hyphens, long s; no header pass, since each
file is one newspaper page). The newspapers are public, so their cleaned text is committed
beside the original.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from metadata.config import load as load_config
from metadata.config import sha256_of_config
from ocr_fix import lexicon

EVAL = Path("data/ocr_quality/defragment_eval.json")

# pending_amendment: ocr_fix.defragment
FRAGMENT_LEN = 2
FRAGMENT_SHARE = 0.3
MAX_WORD = 20
UNKNOWN_PER_LETTER = 12.0

COMMON_SHORT = set(
    "a i o an as at be by do go he if in is it me my no of on or so to up us we am ah ye".split()
)
_ALPHA_RUN = re.compile(r"[A-Za-z]+(?:[ -]+[A-Za-z]+)*")
_TOKEN = re.compile(r"[A-Za-z]+")


class Segmenter:
    def __init__(self, lex: dict[str, int]):
        total = sum(lex.values()) + len(lex)
        self.cost = {w: math.log(total / (n + 1)) for w, n in lex.items()}
        self.unknown = math.log(total) + UNKNOWN_PER_LETTER

    def known_share(self, words: list[str]) -> float:
        """Share of letters that fall in known words (length-weighted, so fragments of
        known words cannot score by being words themselves, like ``a`` or ``in``)."""
        total = sum(len(w) for w in words)
        known = sum(len(w) for w in words if len(w) > 2 and w.lower() in self.cost)
        return known / total if total else 0.0

    def _word_cost(self, w: str) -> float:
        c = self.cost.get(w.lower())
        return c if c is not None else self.unknown + UNKNOWN_PER_LETTER * len(w)

    def split(self, s: str) -> list[str]:
        """Minimum-cost split of a string with no spaces into words."""
        n = len(s)
        best = [0.0] + [math.inf] * n
        back = [0] * (n + 1)
        for i in range(1, n + 1):
            for j in range(max(0, i - MAX_WORD), i):
                c = best[j] + self._word_cost(s[j:i])
                if c < best[i]:
                    best[i], back[i] = c, j
        out, i = [], n
        while i > 0:
            out.append(s[back[i] : i])
            i = back[i]
        return out[::-1]


def fragmented(line: str) -> bool:
    toks = _TOKEN.findall(line)
    if len(toks) < 3:
        return False
    short = sum(1 for t in toks if len(t) <= FRAGMENT_LEN and t.lower() not in COMMON_SHORT)
    return short / len(toks) >= FRAGMENT_SHARE


def repair_line(line: str, seg: Segmenter) -> str:
    if not fragmented(line):
        return line

    def sub(m: re.Match) -> str:
        joined = re.sub(r"[ -]+", "", m.group(0))
        new = seg.split(joined)
        # keep the split only if it raises the share of known words: a run of genuine OCR
        # garbage would otherwise come back as plausible-looking pieces ("thr", "ngs")
        if seg.known_share(new) > seg.known_share(_TOKEN.findall(m.group(0))):
            return " ".join(new)
        return m.group(0)

    return _ALPHA_RUN.sub(sub, line)


def repair(text: str, seg: Segmenter) -> tuple[str, int]:
    lines = text.split("\n")
    out = [repair_line(ln, seg) for ln in lines]
    return "\n".join(out), sum(a != b for a, b in zip(lines, out, strict=True))


def _break(words: list[str], rng: random.Random) -> str:
    """Break words the way the Sentinel is broken: spaces inside about half of them."""
    out = []
    for w in words:
        if len(w) > 2 and rng.random() < 0.5:
            cuts = sorted(rng.sample(range(1, len(w)), rng.randint(1, min(3, len(w) - 1))))
            parts = [w[i:j] for i, j in zip([0, *cuts], [*cuts, len(w)], strict=True)]
            out.append(" ".join(parts))
        else:
            out.append(w)
    return " ".join(out)


def evaluate(n_lines: int = 2000) -> int:
    """Word recovery on keyed 1820s text broken at random, scored word by word."""
    import pyarrow.parquet as pq

    rng = random.Random(load_config()["seed"])
    seg = Segmenter(lexicon.load_tokens())
    rows = pq.read_table(
        "data/catalog/catalog.parquet", columns=["source", "genre_src", "year", "text_path"]
    ).to_pylist()
    paths = [r["text_path"] for r in rows if r["source"] == "tcp" and r["genre_src"] == "evans"]
    rng.shuffle(paths)
    lines: list[list[str]] = []
    for p in paths:
        for ln in Path(p).read_text(encoding="utf-8", errors="replace").splitlines():
            words = _TOKEN.findall(ln.replace("ſ", "s"))
            if 8 <= len(words) <= 16:
                lines.append(words)
        if len(lines) >= n_lines:
            break

    def agree(a: list[str], b: list[str]) -> int:
        sm = SequenceMatcher(a=[w.lower() for w in a], b=[w.lower() for w in b])
        return sum(m.size for m in sm.get_matching_blocks())

    exact = before = total = 0
    for words in lines[:n_lines]:
        broken = _break(words, rng)
        total += len(words)
        before += agree(words, broken.split())
        exact += agree(words, repair_line(broken, seg).split())
    result = {
        "lines": min(n_lines, len(lines)),
        "words": total,
        "words_intact_before": before,
        "words_recovered": exact,
        "rate_before": before / total if total else None,
        "recovery_rate": exact / total if total else None,
        "config_sha256": sha256_of_config(),
    }
    EVAL.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0


def run(root: Path, out_dir: Path) -> int:
    from ocr_fix import clean as cleaner

    seg = Segmenter(lexicon.load_tokens())
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = changed = 0
    for p in sorted(root.glob("*.txt")):
        text, n = repair(p.read_text(encoding="utf-8", errors="replace"), seg)
        text, _ = cleaner.clean(text, headers=False)
        (out_dir / p.name).write_text(text, encoding="utf-8")
        pages += 1
        changed += n
    print(f"{pages:,} pages, {changed:,} lines re-segmented -> {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("evaluate")
    r = sub.add_parser("run")
    r.add_argument("root", type=Path)
    r.add_argument("-o", "--out", type=Path, required=True)
    a = ap.parse_args(argv)
    return evaluate() if a.cmd == "evaluate" else run(a.root, a.out)


if __name__ == "__main__":
    sys.exit(main())
