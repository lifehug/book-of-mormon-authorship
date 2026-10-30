"""Who is speaking: the 1830 Book of Mormon labelled by speaker, for Larsen et al. (1980) (BOM-22).

Larsen, Rencher and Layton assigned every quoted segment of the book to its originator by hand
and published only the word count per speaker (their Appendix B). This rebuilds that labelling
with a model (simulated, labelled as such): each chapter is cut into numbered units of
``UNIT_WORDS`` words, and the model says from which unit each speaker begins. The rule is
Larsen's: words belong to whoever originally speaks them, the innermost speaker of a quotation
within a quotation ("the Lord" quoted by Isaiah is the category ``lord quoted by isaiah``).

The labelling is checked against Appendix B: each speaker's total word count should come out
close to theirs (``LARSEN_COUNTS``). Only the Book of Mormon text is involved (the replication
exception of 4.2); nothing here feeds a calibration.

States per chapter, as the project's long jobs keep them: ``DONE``, ``RETRY`` (a transient
failure: rerun picks it up), ``PARSE_FAIL`` (the reply could not be read; raw text logged).

Usage::

    python -m eval.speakers label [--model sonnet]   # resumable -> larsen_speakers.jsonl
    python -m eval.speakers check                    # totals against Appendix B
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

CHAPTERS = Path("data/benchmark/replication/chapters_1830.jsonl")
OUT = Path("data/benchmark/replication/larsen_speakers.jsonl")
UNIT_WORDS = 15
# Larsen, Rencher and Layton (1980), Appendix B: words per speaker (24 with about 1,000 or more)
LARSEN_COUNTS = {
    "mormon": 97777, "nephi": 29320, "alma": 19777, "moroni": 19408, "lord": 12200,
    "jesus": 9654, "jacob": 8493, "isaiah": 6478, "helaman": 5121, "lehi": 4634,
    "lord quoted by isaiah": 4355, "zenos": 4230, "benjamin": 4204, "amulek": 3158,
    "samuel the lamanite": 3068, "captain moroni": 2970, "abinadi": 2767, "ammon": 2417,
    "nephi son of helaman": 2214, "angel": 2083, "zeniff": 1811, "mosiah": 1167, "enos": 967,
    "father": 961,
}  # fmt: skip

PROMPT = """You are labelling who is speaking in a chapter of the 1830 Book of Mormon, for a \
replication of Larsen, Rencher and Layton (1980). The text has been cut into numbered units of \
about {n} words.

Rule: every word belongs to the person who originally speaks it. Narration belongs to the \
narrator (for example Mormon, Nephi, Jacob, Moroni). Quoted speech belongs to the person quoted. \
If a quotation contains another quotation, the innermost speaker gets those words. When Isaiah \
is quoted and Isaiah in turn quotes the Lord, those words are "lord quoted by isaiah".

Use exactly one of these labels, or "other: <name>" for anyone else:
{labels}

Notes: "alma" is Alma the younger (use "other: alma the elder" for his father); "captain moroni" \
is the military leader in Alma, not the narrator Moroni; "nephi son of helaman" is the Nephi of \
Helaman and 3 Nephi; "jesus" is the resurrected Christ speaking in 3 Nephi; "lord" is the Lord \
speaking anywhere else; "father" is God the Father speaking; "angel" is an angel speaking.

Chapter: {book} {chapter}.

{units}

Reply with JSON only, no other text: one list of objects {{"from": <unit number>, "speaker": \
<label>}} in order, the first starting at unit 1. A speaker continues until the next object. \
Unit numbers must strictly increase: if the speaker changes inside a unit, give that unit to \
whoever speaks most of it, and never use a unit number twice. Give the list once, with no \
corrections or commentary."""


def chapters() -> list[dict]:
    return [json.loads(ln) for ln in CHAPTERS.read_text().splitlines()]


def units(text: str) -> list[list[str]]:
    w = text.split()
    return [w[i : i + UNIT_WORDS] for i in range(0, len(w), UNIT_WORDS)]


def _key(c: dict) -> str:
    return f"{c['book']} {c['chapter']}"


def _parse(text: str, n_units: int) -> list[dict] | None:
    """The last complete JSON list in the reply (a reply that corrects itself ends with its final
    answer), checked: units in range, strictly increasing, starting at 1."""
    segs = None
    for m in re.finditer(r"\[\s*\{.*?\}\s*\]", text, re.S):
        try:
            segs = json.loads(m.group(0))
        except json.JSONDecodeError:
            continue
    if segs is None:
        return None
    out = []
    for s in segs:
        if not isinstance(s, dict) or "from" not in s or "speaker" not in s:
            return None
        f = int(s["from"])
        if not 1 <= f <= n_units:
            return None
        out.append({"from": f, "speaker": str(s["speaker"]).strip().lower()})
    if (
        not out
        or out[0]["from"] != 1
        or any(b["from"] <= a["from"] for a, b in zip(out, out[1:], strict=False))
    ):
        return None
    return out


def _ask(prompt: str, model: str) -> tuple[str, str]:
    from metadata.genre import _TRANSIENT, _log_parse_failure

    try:
        done = subprocess.run(
            ["claude", "-p", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=600,
            stdin=subprocess.DEVNULL,
        )
    except Exception as exc:  # noqa: BLE001
        _log_parse_failure(model, f"<{type(exc).__name__}: {exc}>")
        return "RETRY", ""
    text = done.stdout.strip()
    if not text or _TRANSIENT.search(text) or done.returncode != 0:
        _log_parse_failure(model, text or f"<rc={done.returncode}>")
        return "RETRY", text
    return "OK", text


def _done() -> dict[str, dict]:
    if not OUT.exists():
        return {}
    last = {}
    for ln in OUT.read_text().splitlines():
        r = json.loads(ln)
        last[r["chapter"]] = r
    return last


def label(model: str) -> int:
    from metadata.config import stamp
    from metadata.genre import _log_parse_failure

    labels = "\n".join(f"- {k}" for k in LARSEN_COUNTS)
    done = _done()
    todo = [c for c in chapters() if done.get(_key(c), {}).get("state") != "DONE"]
    print(f"{len(todo)} chapters to label", flush=True)
    st = stamp()
    for i, c in enumerate(todo, 1):
        us = units(c["text"])
        body = "\n".join(f"[{k}] {' '.join(u)}" for k, u in enumerate(us, 1))
        prompt = PROMPT.format(
            n=UNIT_WORDS, labels=labels, book=c["book"], chapter=c["chapter"], units=body
        )
        state, text = _ask(prompt, model)
        rec = {"chapter": _key(c), "model": model, "units": len(us), "state": state}
        if state == "OK":
            segs = _parse(text, len(us))
            if segs is None:
                _log_parse_failure(model, text)
                rec.update(state="PARSE_FAIL", raw=text[:4000])
            else:
                rec.update(state="DONE", segments=segs)
        rec["config_sha256"] = st["config_sha256"]
        with OUT.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"  {i}/{len(todo)} {_key(c)} {rec['state']}", flush=True)
        if state == "RETRY":
            time.sleep(60)
    return 0


def speaker_words() -> dict[str, list[str]]:
    """Every chapter's words grouped by speaker, in book order (labelled chapters only)."""
    done = _done()
    by: dict[str, list[str]] = {}
    for c in chapters():
        r = done.get(_key(c))
        if not r or r["state"] != "DONE":
            continue
        us = units(c["text"])
        segs = r["segments"]
        for s, nxt in zip(segs, [*segs[1:], {"from": len(us) + 1}], strict=True):
            for u in us[s["from"] - 1 : nxt["from"] - 1]:
                by.setdefault(s["speaker"], []).extend(u)
    return by


def check() -> int:
    by = speaker_words()
    done = _done()
    states = Counter(r["state"] for r in done.values())
    print(f"chapters: {dict(states)} of {len(chapters())}")
    total = sum(len(v) for v in by.values())
    pub_total = 267_957  # Larsen et al., Appendix A: the engravers' counts summed (the whole book)
    print(f"{'speaker':24s} {'ours':>7s} {'Larsen':>7s}  ratio  (ours scaled to their book size)")
    for k, pub in LARSEN_COUNTS.items():
        ours = len(by.get(k, []))
        scaled = ours * pub_total / total if total else 0
        print(f"{k:24s} {ours:7d} {pub:7d}  {scaled / pub:5.2f}")
    other = Counter({k: len(v) for k, v in by.items() if k not in LARSEN_COUNTS})
    print("largest other labels:", other.most_common(8))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    lab = sub.add_parser("label")
    lab.add_argument("--model", default="sonnet")
    sub.add_parser("check")
    a = ap.parse_args(argv)
    return label(a.model) if a.cmd == "label" else check()


if __name__ == "__main__":
    sys.exit(main())
