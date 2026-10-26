"""Propose signed items in the church periodicals for the candidate samples (BOM-13).

Implements the proposal step of the "Selection rule for signed periodical items" in
``docs/candidates.md`` (rules 11-16). For every line in the OCR of a periodical run that looks
like a candidate's signature, it proposes the item's span: back from the signature to the
nearest heading, dateline or salutation, never past the previous signature. Lines next to
other signatures, or carrying a chairman/clerk title, are proposed as rejections.

Proposals are written to ``data/candidates/signed_items.json`` with ``checked: false``. A person
(or the session doing BOM-13) reads each span and sets ``checked: true``, corrects ``start``, or
sets ``admit: false`` with a reason. ``ingest.candidate_words`` counts only checked, admitted
items. Re-running this script keeps every checked entry and only adds new proposals.

Usage::

    python -m ingest.signed_items            # propose, keeping checked entries
    python -m ingest.signed_items --show 12  # print one proposal's span for checking
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ingest.candidates import PUBLIC_DIR

OUT = Path("data/candidates/signed_items.json")
SOURCES = ("oc-messenger-advocate", "wwp-evening-morning-star")
SIGNERS = {
    "Oliver Cowdery": r"o(?:liver)?\.? ?c ?o ?w ?d ?e ?r ?y",
    "W. W. Phelps": r"w\. ?w\. ?p ?h ?e ?l ?p ?s",
    "Sidney Rigdon": r"s(?:idney)?\.? ?r ?i ?g ?d ?o ?n",
    "Parley P. Pratt": r"p(?:arley)?\.? ?p\.? ?p ?r ?a ?t ?t",
    "Joseph Smith": r"joseph smith,? (?:jr|jun)",
}
OFFICE = r"ch'?n|chairman|clerk|sec'?y|secretary|moderator|pres't"
OFFICE_RE = re.compile(rf"\b({OFFICE})\b", re.I)
# A name alone on its line (letters excluded after it, so "Cowdery wrote" is not one), or a
# name followed by an office title ("W. W. PHELPS, Ch'n."), which is listed and rejected.
SIG_RE = {
    name: re.compile(rf"^\s*[^a-z]{{0,4}}{pat}([^a-z]{{0,25}}|[ ,.]+({OFFICE})\b.{{0,15}})$", re.I)
    for name, pat in SIGNERS.items()
}
# Any all-capitals name line, to spot a signature that is one of several.
NAME_LINE_RE = re.compile(r"^\s*[A-Z][A-Z. ]{3,30}[A-Z][.,]?\s*$")
HEADING_RE = re.compile(r"^\s*(LETTER\b|[A-Z][A-Z ,.'’-]{6,60}$)")
SALUTE_RE = re.compile(
    r"^\s*(Dear|Beloved|Respected|Brother|Brethren|Sir|Dearly|My dear|To the)\b.{0,40}[,:!]\s*$"
)
DATELINE_RE = re.compile(r"^\s*[A-Z][A-Za-z .]+,.*\b1[83]\d\d\b.{0,10}$")
RUNNING_HEAD_RE = re.compile(r"MESSENGER AND ADVOCATE|EVENING AND (THE )?MORNING STAR", re.I)
MAX_BACK = 1500


def _signer(line: str) -> str | None:
    for name, rx in SIG_RE.items():
        if rx.match(line):
            return name
    return None


def propose(sid: str, lines: list[str]) -> list[dict]:
    sigs = [(i, s) for i, line in enumerate(lines) if (s := _signer(line))]
    out = []
    prev_end = 0
    for i, signer in sigs:
        near = [j for j, _ in sigs if j != i and abs(j - i) <= 3]
        around = lines[max(0, i - 2) : i + 3]
        others = [x for x in around if NAME_LINE_RE.match(x) and not _signer(x)]
        reason = None
        if signer == "Joseph Smith":
            reason = "rule 13: Joseph Smith's signed items are not taken"
        elif near or others:
            reason = "rule 12: one of several signatures"
        elif OFFICE_RE.search(lines[i]) or any(OFFICE_RE.search(x) for x in around):
            reason = "rule 12: signed as an officer of a meeting"
        floor = max(prev_end, i - MAX_BACK)
        start = None
        for j in range(i - 1, floor, -1):
            line = lines[j]
            if RUNNING_HEAD_RE.search(line):
                continue
            if SALUTE_RE.match(line) or HEADING_RE.match(line) or DATELINE_RE.match(line):
                start = j
                # climb a header block (title, dateline, salutation) a few lines above
                for h in range(j - 1, max(floor, j - 5), -1):
                    if HEADING_RE.match(lines[h]) or DATELINE_RE.match(lines[h]):
                        start = h
                if SALUTE_RE.match(line) or (j < i - 20):
                    break
        end = i
        while (
            end + 1 < len(lines)
            and end - i < 3
            and lines[end + 1].strip().lower().startswith(("to ", "p.s", "ps."))
        ):
            end += 1
        out.append(
            {
                "source": sid,
                "signer": signer,
                "signature_line": i + 1,
                "signature": lines[i].strip(),
                "start": (start + 1) if start is not None else None,
                "end": end + 1,
                "opening": lines[start].strip()[:80] if start is not None else None,
                "admit": reason is None,
                "reason": reason or "rule 11",
                "checked": False,
            }
        )
        prev_end = i
    return out


def load_lines(sid: str) -> list[str]:
    return (PUBLIC_DIR / f"{sid}.txt").read_text(encoding="utf-8", errors="replace").splitlines()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--show", type=int, help="print the span of proposal N (0-based)")
    a = ap.parse_args(argv)
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    if a.show is not None:
        e = existing[a.show]
        lines = load_lines(e["source"])
        lo = (e["start"] or e["signature_line"] - 40) - 1
        for n in range(lo, e["end"]):
            print(f"{n + 1:6d}  {lines[n]}")
        return 0
    # Checked entries are kept as they are, including ones added by hand that the proposer
    # cannot find (a series letter with no signature, a name sharing a line with text).
    items = [e for e in existing if e.get("checked")]
    kept = {(e["source"], e["signature_line"]) for e in items}
    for sid in SOURCES:
        items += [
            p for p in propose(sid, load_lines(sid)) if (sid, p["signature_line"]) not in kept
        ]
    items.sort(key=lambda e: (e["source"], e["signature_line"]))
    OUT.write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(items)} signature lines; {sum(e['admit'] for e in items)} proposed admits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
