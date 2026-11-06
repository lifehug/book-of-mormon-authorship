"""Corrections in the original and printer's manuscripts, by scribe and type (BOM-34).

The Joseph Smith Papers transcripts (private: ``data/private/bom/jsp_original.jsonl`` and
``jsp_printers.jsonl``) mark what a scribe struck out (``<span class="deleted">``), what was added
(``<...>``, written between zero-width spaces) and where a new hand begins (``new-scribe-note``).
Each correction becomes an event:

- **substitution**: a deletion followed by an insertion, or by a word written straight after it on
  the line that resembles it (an immediate correction); typed by the pair of words:
  ``homophone`` (a listed same-sound pair, e.g. where/were), ``sound_alike`` (same Soundex code,
  different spelling), ``spelling`` (close in letters, not in sound), ``other``;
- **false_start**: a deleted fragment that the next word completes (``migh`` then ``mightest``);
- **deletion**: a struck word with no replacement; **insertion**: a word added with no deletion
  (an omission restored).

A word starting with a capital letter in the middle of a sentence is flagged ``name``. The
original manuscript was taken down from dictation and the printer's manuscript copied from it
(Skousen; the Papers' introductions), so ear errors should be commoner in the first and eye errors
in the second: ``summary`` compares the share of sound-based substitutions between them, overall
and on the pages whose text survives in both.

Public outputs hold ids, pages, scribes, categories and counts, never words:
``data/manuscript/corrections.csv`` and ``summary.json``. The word pairs, which are the Papers'
transcription, stay private in ``data/private/manuscript/corrections.jsonl``.

Usage::

    python -m manuscript.corrections build   # -> data/manuscript/corrections.csv, summary.json
"""

from __future__ import annotations

import argparse
import csv
import difflib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from metadata.config import stamp

SOURCES = {"original": Path("data/private/bom/jsp_original.jsonl"),
           "printers": Path("data/private/bom/jsp_printers.jsonl")}  # fmt: skip
ALIGN = {"original": Path("data/bom/align_original.jsonl"),
         "printers": Path("data/bom/align_printers.jsonl")}  # fmt: skip
OUT = Path("data/manuscript")
PRIVATE = Path("data/private/manuscript")
ZW = "​"

# Same-sound pairs common in period scribal error (both directions), from the standard lists.
HOMOPHONES = [("there", "their"), ("where", "were"), ("to", "too"), ("to", "two"),
              ("too", "two"), ("then", "than"), ("know", "no"), ("knew", "new"),
              ("write", "right"), ("rite", "right"), ("whole", "hole"), ("which", "witch"),
              ("our", "hour"), ("by", "buy"), ("by", "bye"), ("son", "sun"), ("sent", "scent"),
              ("sent", "cent"), ("seen", "scene"), ("sea", "see"), ("way", "weigh"),
              ("wait", "weight"), ("rain", "reign"), ("rain", "rein"), ("reign", "rein"),
              ("pray", "prey"), ("peace", "piece"), ("one", "won"), ("for", "four"),
              ("fore", "for"), ("fore", "four"), ("herd", "heard"), ("its", "it's"),
              ("led", "lead"), ("past", "passed"), ("threw", "through"), ("tide", "tied"),
              ("wear", "where"), ("weather", "whether"), ("would", "wood"), ("an", "and"),
              ("and", "in"), ("an", "in"), ("of", "off"), ("are", "our"), ("are", "or"),
              ("or", "ore"), ("of", "have"), ("than", "that"), ("these", "this"),
              ("faith", "fate"), ("council", "counsel"), ("course", "coarse"),
              ("straight", "strait"), ("bare", "bear"), ("bore", "boar"), ("born", "borne"),
              ("plain", "plane"), ("altar", "alter"), ("mean", "mien"), ("praise", "prays"),
              ("ceased", "seized"), ("hence", "hens"), ("descent", "dissent"),
              ("sense", "since"), ("sense", "cents"), ("flee", "flea"), ("idle", "idol"),
              ("him", "hymn"), ("lessen", "lesson"), ("meet", "meat"), ("mete", "meet"),
              ("tail", "tale"), ("vain", "vein"), ("vain", "vane"), ("wade", "weighed"),
              ("wrest", "rest"), ("waste", "waist"), ("wholly", "holy"), ("ye", "the")]  # fmt: skip
_PAIRS = {frozenset(p) for p in HOMOPHONES}
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def soundex(w: str) -> str:
    """American Soundex of a word's letters ('' for none)."""
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return ""
    codes = {ch: str(k) for k, group in enumerate(("bfpv", "cgjkqsxz", "dt", "l", "mn", "r"), 1)
             for ch in group}  # fmt: skip
    out, last = w[0].upper(), codes.get(w[0], "")
    for ch in w[1:]:
        c = codes.get(ch, "")
        if c and c != last:
            out += c
        if ch not in "hw":
            last = c
    return (out + "000")[:4]


def kind_of(a: str, b: str) -> str:
    """The type of a one-word substitution a -> b."""
    x, y = re.sub(r"[^a-z']", "", a.lower()), re.sub(r"[^a-z']", "", b.lower())
    if not x or not y or x == y:
        return "other"
    if frozenset((x, y)) in _PAIRS:
        return "homophone"
    if soundex(x) == soundex(y):
        return "sound_alike"
    if difflib.SequenceMatcher(None, x, y).ratio() >= 0.75:
        return "spelling"
    return "other"


def tokens(page_html: str) -> list[tuple[str, str]]:
    """The page as (kind, text) tokens: word, del, ins, scribe, js_start, js_end."""
    h = re.sub(r'<aside class="popup-wrapper".*?</aside>', " ", page_html, flags=re.S)
    h = re.sub(r'<div class="note-data editorial-footnote".*?</div>', " ", h, flags=re.S)
    h = re.sub(r'<span class="line-break hyphenate"></span>', "", h)

    def plain(x: str) -> str:
        return html.unescape(re.sub(r"<[^>]+>", "", x)).replace(ZW, "")

    # markers are \x01KIND\x02text\x03; insertions first, so a struck insertion stays inside its
    # deletion as plain text
    h = re.sub(f"&lt;{ZW}(.*?){ZW}&gt;", lambda m: f" \x01INS\x02{plain(m.group(1))}\x03 ", h,
               flags=re.S)  # fmt: skip

    def struck(m: re.Match) -> str:
        inner = re.sub("\x01INS\x02([^\x03]*)\x03", r"\1", m.group(1))  # a struck insertion
        return f" \x01DEL\x02{plain(inner)}\x03 "

    h = re.sub(r'<span class="deleted">(.*?)</span>', struck, h, flags=re.S)
    h = re.sub(r'<a[^>]*class="new-scribe-note[^"]*"[^>]*>', " \x01SCRIBE\x02\x03 ", h)
    h = re.sub(r'<span class="josephswriting">', " \x01JS\x02\x03 ", h)
    h = html.unescape(re.sub(r"<[^>]+>", " ", h))
    out: list[tuple[str, str]] = []
    names = {"SCRIBE": "scribe", "JS": "js", "DEL": "del", "INS": "ins"}
    for part in re.split(r"(\x01[^\x03]*\x03)", h):
        if part.startswith("\x01"):
            k, _, txt = part[1:-1].partition("\x02")
            out.append((names[k], txt))
        else:
            out += [("word", w) for w in _WORD.findall(part.replace(ZW, ""))]
    return out


def _words(s: str) -> list[str]:
    return _WORD.findall(s)


def events(page: dict, start_scribe: str) -> tuple[list[dict], str]:
    """A page's corrections and the hand at its end. ``start_scribe`` is the hand carried over
    from the previous page; each new-scribe note moves to the next hand the page lists."""
    hands = [s["name"].replace("  ", " ") for s in page.get("scribes") or []] or [start_scribe]
    toks = tokens(page["expanded_html"])
    notes = sum(k == "scribe" for k, _ in toks)
    # one hand per stretch between new-scribe notes: with as many notes as listed hands the page
    # opens in the hand carried over; otherwise it opens in the first listed hand
    seq = [start_scribe, *hands] if notes >= len(hands) else hands
    cur, k_note, js = seq[0], 0, False
    out: list[dict] = []
    prev_word = ""
    i = 0
    while i < len(toks):
        kind, txt = toks[i]
        hand = "Joseph Smith Jr." if js else cur
        if kind == "scribe":
            k_note += 1
            cur = seq[min(k_note, len(seq) - 1)]
        elif kind == "js":
            js = True
        elif kind == "del":
            nxt = toks[i + 1] if i + 1 < len(toks) else ("", "")
            d = _words(txt)
            mid = bool(prev_word) and prev_word[-1:] not in ".?!"
            name = bool(d) and d[0][:1].isupper() and mid
            if nxt[0] == "ins":
                ins = _words(nxt[1])
                typ = kind_of(d[0], ins[0]) if len(d) == 1 and len(ins) == 1 else "other"
                out.append({"event": "substitution", "type": typ, "deleted": txt,
                            "inserted": nxt[1], "scribe": hand, "name": name})  # fmt: skip
                i += 1
            elif nxt[0] == "word" and d and len(d) == 1:
                w = nxt[1]
                if w.lower().startswith(d[0].lower()) and w.lower() != d[0].lower():
                    out.append({"event": "false_start", "type": "false_start", "deleted": txt,
                                "inserted": w, "scribe": hand, "name": name})  # fmt: skip
                elif difflib.SequenceMatcher(None, d[0].lower(), w.lower()).ratio() >= 0.5 or \
                        frozenset((d[0].lower(), w.lower())) in _PAIRS:  # fmt: skip
                    out.append({"event": "substitution", "type": kind_of(d[0], w),
                                "deleted": txt, "inserted": w, "scribe": hand,
                                "name": name, "immediate": True})  # fmt: skip
                else:
                    out.append({"event": "deletion", "type": "deletion", "deleted": txt,
                                "inserted": "", "scribe": hand, "name": name})  # fmt: skip
            else:
                out.append({"event": "deletion", "type": "deletion", "deleted": txt,
                            "inserted": "", "scribe": hand, "name": name})  # fmt: skip
        elif kind == "ins":
            out.append({"event": "insertion", "type": "insertion", "deleted": "",
                        "inserted": txt, "scribe": hand, "name": False})  # fmt: skip
        elif kind == "word":
            prev_word = txt
            js = False if js and txt[-1:] in ".?!" else js
        i += 1
    return out, cur


def _pages(which: str) -> list[dict]:
    return [json.loads(ln) for ln in SOURCES[which].read_text().splitlines()]


def _para_ranges(which: str) -> dict[int, tuple[int, int]]:
    out = {}
    if ALIGN[which].exists():
        for ln in ALIGN[which].read_text().splitlines():
            r = json.loads(ln)
            if r.get("para_first") is not None:
                out[r["page"]] = (r["para_first"], r["para_last"])
    return out


def build() -> int:
    from scipy.stats import fisher_exact

    rows, private = [], []
    words: dict[str, Counter] = defaultdict(Counter)
    for which in ("original", "printers"):
        ranges = _para_ranges(which)
        cur = "Oliver Cowdery"
        for p in _pages(which):
            evs, cur_end = events(p, cur)
            n_words = len(_WORD.findall(p.get("text") or ""))
            words[which][cur] += n_words  # page words to the hand that opened it (approximate)
            cur = cur_end
            first, last = ranges.get(p["page"], (None, None))
            for k, e in enumerate(evs):
                rid = f"{which}:{p['page']}:{k}"
                rows.append({"id": rid, "manuscript": which, "page": p["page"],
                             "editorial_page": p.get("editorialPageNumber"),
                             "scribe": e["scribe"], "event": e["event"], "type": e["type"],
                             "immediate": bool(e.get("immediate")), "name": e["name"],
                             "deleted_words": len(_words(e["deleted"])),
                             "inserted_words": len(_words(e["inserted"])),
                             "para_first": first, "para_last": last})  # fmt: skip
                private.append({"id": rid, "deleted": e["deleted"], "inserted": e["inserted"]})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "corrections.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "corrections.jsonl").write_text("".join(json.dumps(r) + "\n" for r in private))

    def tally(sel: list[dict]) -> dict:
        subs = [r for r in sel if r["event"] == "substitution"]
        sound = sum(r["type"] in ("homophone", "sound_alike") for r in subs)
        return {"events": len(sel), "by_event": dict(Counter(r["event"] for r in sel)),
                "substitution_types": dict(Counter(r["type"] for r in subs)),
                "substitutions": len(subs), "sound_based": sound,
                "sound_share": sound / len(subs) if subs else None,
                "names": sum(r["name"] for r in sel)}  # fmt: skip

    def compare(a: list[dict], b: list[dict]) -> dict:
        ta, tb = tally(a), tally(b)
        table = [[ta["sound_based"], ta["substitutions"] - ta["sound_based"]],
                 [tb["sound_based"], tb["substitutions"] - tb["sound_based"]]]  # fmt: skip
        both = ta["substitutions"] and tb["substitutions"]
        odds, p = fisher_exact(table) if both else (None, None)
        # the primary contrast: listed homophones (where/were), the clearest ear errors; Soundex
        # also catches eye errors (hs/his) and is reported beside it
        ha, hb = (t["substitution_types"].get("homophone", 0) for t in (ta, tb))
        h_table = [[ha, ta["substitutions"] - ha], [hb, tb["substitutions"] - hb]]
        h_odds, h_p = fisher_exact(h_table) if both else (None, None)
        return {"original": ta, "printers": tb, "homophones": {"original": ha, "printers": hb,
                "odds_ratio": h_odds, "fisher_p": h_p}, "sound_based_odds_ratio": odds,
                "sound_based_fisher_p": p}  # fmt: skip

    om = [r for r in rows if r["manuscript"] == "original"]
    pm = [r for r in rows if r["manuscript"] == "printers"]
    om_paras = {q for r in om if r["para_first"] is not None
                for q in range(r["para_first"], r["para_last"] + 1)}  # fmt: skip
    pm_matched = [r for r in pm if r["para_first"] is not None
                  and om_paras & set(range(r["para_first"], r["para_last"] + 1))]  # fmt: skip
    by_scribe = {f"{m}|{s}": {**tally([r for r in rows if r["manuscript"] == m
                                       and r["scribe"] == s]),
                              "page_words": words[m].get(s, 0)}
                 for m, s in sorted({(r["manuscript"], r["scribe"]) for r in rows})}  # fmt: skip
    doc = {**stamp(), "pages": {m: len(_pages(m)) for m in SOURCES},
           "words": {m: sum(c.values()) for m, c in words.items()},
           "all_pages": compare(om, pm), "matched_pages": compare(om, pm_matched),
           # the same hand in both: dictation against copying with the scribe held fixed
           "same_scribe_cowdery": compare([r for r in om if r["scribe"] == "Oliver Cowdery"],
                                          [r for r in pm if r["scribe"] == "Oliver Cowdery"]),
           "by_scribe": by_scribe,
           "note": "page words are credited to the hand that opens each page (approximate); the "
                   "printer's manuscript also carries later editing (printer's marks, 1837 "
                   "revisions) that the transcript does not separate"}  # fmt: skip
    (OUT / "summary.json").write_text(json.dumps(doc, indent=1) + "\n")
    for scope in ("all_pages", "matched_pages", "same_scribe_cowdery"):
        a = doc[scope]
        h = a["homophones"]
        print(f"{scope}: original {a['original']['events']:,} corrections, "
              f"{a['original']['substitutions']} substitutions, {h['original']} homophones; "
              f"printer's {a['printers']['events']:,}, {a['printers']['substitutions']}, "
              f"{h['printers']} homophones; Fisher p {h['fisher_p']:.3g}")  # fmt: skip
    print(f"-> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["build"])
    ap.parse_args(argv)
    return build()


if __name__ == "__main__":
    sys.exit(main())
