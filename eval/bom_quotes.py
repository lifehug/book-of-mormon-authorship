"""Book of Mormon quotations in a text written after the book (Amendment 43's rule, importable).

``eval.bom_overlap`` classes every run a candidate sample shares with the Book of Mormon, using
each item's date against the dictation of the matching passage. A text written after March 1830
cannot predate any passage, so for it the rule reduces to this: every maximal run of
``candidates.bom_quotation.ngram`` or more words shared with the narrative books, unless every
window of it is in the King James Bible (biblical) or half or more of its windows occur in the
period control texts (stock phrasing); runs within ``max_gap`` words of each other form one
passage; a passage of ``min_words`` or more is a quotation. Used by BOM-73 (``eval.js_time``);
``check`` reproduces ``eval.bom_overlap``'s count on a post-1830 candidate sample.

Usage::

    python -m eval.bom_quotes check
"""

from __future__ import annotations

import glob
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

from metadata.config import load as load_config


def norm(t: str) -> list[str]:
    return re.findall(r"[a-z]+", t.lower())


@lru_cache(maxsize=1)
def _index() -> tuple[dict, set, set, dict]:
    import numpy as np
    from tokenizers import Tokenizer

    q = load_config()["candidates"]["bom_quotation"]
    n = q["ngram"]
    bw = [
        w
        for ln in Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines()
        for r in [json.loads(ln)]
        if r.get("book")  # narrative books only, as the sealed chunks
        for w in norm(r.get("text", ""))
    ]
    bset = {tuple(bw[i : i + n]) for i in range(len(bw) - n + 1)}
    kjv = norm(" ".join(json.loads(ln)["text"] for ln in open("data/kjv/kjv.jsonl")))
    kset = {tuple(kjv[i : i + n]) for i in range(len(kjv) - n + 1)}
    tok = Tokenizer.from_file("data/timelocked_lm/tokenizer.json")
    ctrl: list[str] = []
    for f in sorted(glob.glob("data/corpus/alm/candidates/inputs/ctrl__*.npz")):
        ctrl += norm(tok.decode(np.load(f)["train"].ravel().tolist()))
    cset = {tuple(ctrl[i : i + n]) for i in range(len(ctrl) - n + 1)}
    return bset, kset, cset, q


def passages(text: str) -> list[list[str]]:
    """The quotations in ``text`` (written after the book), as normalised word lists."""
    bset, kset, cset, q = _index()
    n, gap, floor = q["ngram"], q["max_gap"], q["min_words"]
    w = norm(text)
    hs = {i for i in range(len(w) - n + 1) if tuple(w[i : i + n]) in bset}
    runs, i = [], 0
    while i < len(w) - n + 1:
        if i not in hs:
            i += 1
            continue
        j = i
        while j + 1 in hs:
            j += 1
        grams = [tuple(w[k : k + n]) for k in range(i, j + 1)]
        biblical = all(g in kset for g in grams)
        stock = sum(g in cset for g in grams) / len(grams) >= 0.5
        runs.append((i, j + n, biblical or stock))
        i = j + n
    merged: list[list] = []
    for a, b, skip in runs:
        if skip:
            continue
        if merged and a - merged[-1][1] <= gap:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [w[a:b] for a, b in merged if b - a >= floor]


def check() -> int:
    """Compare with eval.bom_overlap on Pratt's Voice of Warning (1837, after the book)."""
    sid = "ppp-1837-voice-of-warning"
    text = Path(f"data/candidates/clean/{sid}.txt").read_text(encoding="utf-8")
    mine = sum(len(p) for p in passages(text))
    theirs = json.loads(Path("data/candidates/bom_overlap.json").read_text())["masked_words"]
    ref = theirs.get(f"printed:{sid}")
    print(f"{sid}: {mine} words in quotations here, {ref} in eval.bom_overlap")
    return 0 if mine == ref else 1


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args != ["check"]:
        print(__doc__)
        return 1
    return check()


if __name__ == "__main__":
    sys.exit(main())
