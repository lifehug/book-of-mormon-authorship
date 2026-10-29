"""The Federalist Papers as a known-author set (BOM-43, BOM-21).

Text: Project Gutenberg ebook 1404 (public domain), fetched to
``data/benchmark/federalist/pg1404.txt``. Attributions are the standard ones (Mosteller and
Wallace 1964; Adair 1944), not Gutenberg's header lines, and the twelve disputed papers and the
three joint ones are left out: a benchmark needs answers that are not themselves in question.

Usage::

    python -m eval.federalist        # -> data/benchmark/federalist/papers.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DIR = Path("data/benchmark/federalist")
SOURCE = DIR / "pg1404.txt"
OUT = DIR / "papers.jsonl"


def _ranges(*spans: tuple[int, int]) -> set[int]:
    return {n for a, b in spans for n in range(a, b + 1)}


AUTHORS = {
    "hamilton": _ranges((1, 1), (6, 9), (11, 13), (15, 17), (21, 36), (59, 61), (65, 85)),
    "madison": _ranges((10, 10), (14, 14), (37, 48)),
    "jay": _ranges((2, 5), (64, 64)),
}
JOINT = _ranges((18, 20))
DISPUTED = _ranges((49, 58), (62, 63))


def papers(text: str) -> dict[int, str]:
    """Paper number -> body text (from the author line to the next paper's heading)."""
    start = text.find("*** START OF")
    end = text.find("*** END OF")
    text = text[start if start >= 0 else 0 : end if end >= 0 else len(text)]
    heads = list(re.finditer(r"(?m)^FEDERALIST No\. (\d+)\s*$", text))
    out: dict[int, str] = {}
    for i, h in enumerate(heads):
        n = int(h.group(1))
        body = text[h.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        out.setdefault(n, _strip(body))  # Gutenberg prints No. 70 twice; keep the first
    return out


def _strip(body: str) -> str:
    """The essay only: no title, newspaper line or author line above the salutation (the author's
    own name would give the answer away), and no closing PUBLIUS."""
    m = re.search(r"(?mi)^\s*To the People of the State of New York[:.]?\s*$", body)
    if m:
        body = body[m.end() :]
    return re.sub(r"(?m)^\s*PUBLIUS\.?", "", body).strip()


def build() -> int:
    ps = papers(SOURCE.read_text(encoding="utf-8"))
    who = {n: a for a, ns in AUTHORS.items() for n in ns}
    n_out = 0
    with OUT.open("w") as fh:
        for n in sorted(ps):
            if n in JOINT or n in DISPUTED or n not in who:
                continue
            fh.write(json.dumps({"paper": n, "author": who[n], "text": ps[n]}) + "\n")
            n_out += 1
    by = {a: sum(1 for n in ps if who.get(n) == a) for a in AUTHORS}
    print(f"{len(ps)} papers parsed; {n_out} with an undisputed single author {by} -> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    return build()


if __name__ == "__main__":
    sys.exit(main())
