"""Book of Mormon text inside the candidate samples: what is quotation and what is shared idiom.

Read-only analysis (2026-11-10, after unblinding; for the owner's review of Amendment 43). For
every candidate sample item, every maximal run of ``N`` or more words it shares with the 1830 Book
of Mormon's narrative books (no preface, no witnesses, as the sealed chunks) is classed by a rule
fixed before the matches were read:

1. *biblical*: every 8-word window of the run is in the King James Bible (already masked);
2. *stock*: half or more of its windows occur in the period control texts (common phrasing);
3. otherwise, by date: the item written *before* that passage was dictated (Mosiah-Moroni
   April-May 1829, 1 Nephi-Words of Mormon June 1829; ``data/bom/segments/boundaries.json``) is
   *predates the passage* (it cannot quote it); *same weeks as the passage* if within that window;
   after it, *quotation* if 20 or more words, else *short phrase, ambiguous*.

Writes numbers only to ``data/candidates/bom_overlap.json``.

Usage::

    python -m eval.bom_overlap
"""

import glob
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

N = 8


def norm(t):
    return re.findall(r"[a-z]+", t.lower())


# Book of Mormon: words with paragraph seq and book
B = [json.loads(ln) for ln in open("data/bom/1830/edition_1830.jsonl")]
bw = []
bpos = []
for r in B:
    if not r.get("book"):
        continue  # narrative books only, as the sealed chunks (no preface, no witnesses)
    for w in norm(r.get("text", "")):
        bw.append(w)
        bpos.append((r["seq"], r.get("book")))
bidx = defaultdict(list)
for i in range(len(bw) - N + 1):
    bidx[tuple(bw[i : i + N])].append(i)
kjv = norm(" ".join(json.loads(ln)["text"] for ln in open("data/kjv/kjv.jsonl")))
kset = {tuple(kjv[i : i + N]) for i in range(len(kjv) - N + 1)}
tok = Tokenizer.from_file("data/timelocked_lm/tokenizer.json")
ctrl = []
for f in glob.glob("data/corpus/alm/candidates/inputs/ctrl__*.npz"):
    ctrl += norm(tok.decode(np.load(f)["train"].ravel().tolist()))
cset = {tuple(ctrl[i : i + N]) for i in range(len(ctrl) - N + 1)}
order = json.load(open("data/bom/segments/boundaries.json"))["dictation_order"]["segments"]


def bom_when(seq):
    for s in order:
        if s["seq_first"] <= seq <= s["seq_last"]:
            return "Apr-May 1829" if s["label"] == "first" else "Jun 1829"
    return "?"


WHEN = {"Apr-May 1829": ((1829, 4), (1829, 5)), "Jun 1829": ((1829, 6), (1829, 6))}


MONTHS = (
    r"(January|February|March|April|May|June|July|August|September|October|November|"
    r"December|Spring|Summer|circa Summer)?\s*(\d{4})"
)


def item_date(title, fname):
    if "|" not in title:  # printed units: the year is in the file name, never in its line numbers
        y = re.match(r"[a-z]+-(1[78]\d\d)-", fname)
        if y:
            return (int(y.group(1)), 6), title
        if fname.startswith("oc-messenger-advocate"):
            return (1834, 10), title
        return (1831, 1), title
    title = title.split("|", 1)[-1]
    m = re.search(
        MONTHS,
        title,
    )
    mon = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
        "Spring": 4,
        "Summer": 7,
        "circa Summer": 7,
    }
    if m and m.group(2):
        return (int(m.group(2)), mon.get((m.group(1) or "").strip(), 6)), title
    y = re.match(r"[a-z]+-(1[78]\d\d)-", fname)
    if y:
        return (int(y.group(1)), 6), title
    if fname.startswith("oc-messenger-advocate"):
        return (1834, 10), title  # Messenger and Advocate, Oct 1834-1836
    return (1831, 1), title


def items():
    for f in sorted(glob.glob("data/private/candidates/samples/*.txt")):
        unit = Path(f).stem
        cur = None
        buf = []
        for ln in open(f):
            if ln.startswith("## "):
                if cur:
                    yield unit, cur, " ".join(buf)
                cur = ln[3:].strip()
                buf = []
            else:
                buf.append(ln)
        if cur:
            yield unit, cur, " ".join(buf)
    for d in ("data/candidates/clean", "data/private/candidates/clean"):
        for f in sorted(glob.glob(d + "/*.txt")):
            yield "printed:" + Path(f).stem.split("__")[0], Path(f).stem, open(f).read()


rows = []
per_unit = defaultdict(Counter)
for unit, title, text in items():
    w = norm(text)
    if not w:
        continue
    (y, mo), _ = item_date(title, title)
    hit = [i for i in range(len(w) - N + 1) if tuple(w[i : i + N]) in bidx]
    per_unit[unit]["words"] += len(w)
    # maximal runs
    i = 0
    hs = set(hit)
    while i < len(w) - N + 1:
        if i in hs:
            j = i
            while j + 1 in hs:
                j += 1
            run = w[i : j + N]
            L = len(run)
            grams = [tuple(run[k : k + N]) for k in range(L - N + 1)]
            loc = bidx[grams[0]][0]
            seq, book = bpos[loc]
            if all(g in kset for g in grams):
                cls = "biblical"
            elif sum(g in cset for g in grams) / len(grams) >= 0.5:
                cls = "stock"
            else:
                when = bom_when(seq)
                lo, hi = WHEN.get(when, ((1829, 4), (1829, 6)))
                if (y, mo) < lo:
                    cls = "predates the passage"
                elif (y, mo) <= hi:
                    cls = "same weeks as the passage"
                elif L >= 20:
                    cls = "quotation"
                else:
                    cls = "short phrase, ambiguous"
            rows.append(
                {
                    "unit": unit,
                    "item": title,
                    "date": f"{y}-{mo:02d}",
                    "words": L,
                    "class": cls,
                    "bom_book": book,
                    "bom_seq": seq,
                    "bom_when": bom_when(seq),
                    "bom_text": " ".join(bw[loc : loc + L]),
                }
            )
            per_unit[unit][cls] += L
            i = j + N
        else:
            i += 1
json.dump(
    {
        "n": N,
        "rows": [{k: v for k, v in r.items() if k != "bom_text"} for r in rows],
        "per_unit": {u: dict(c) for u, c in per_unit.items()},
    },
    open("data/candidates/bom_overlap.json", "w"),
    indent=1,
)
for u, c in sorted(per_unit.items()):
    tot = c["words"]
    sh = sum(v for k, v in c.items() if k != "words")
    if sh:
        print(
            f"{u:45s} {tot:7d} words, shared {sh / tot:5.1%}:",
            {k: v for k, v in c.items() if k != "words"},
        )
