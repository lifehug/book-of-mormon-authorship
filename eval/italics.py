"""The King James italics test (BOM-62; Amendment 11).

Plan, registered before any count: ``docs/italics-plan.md``. Within every King James span the
registered masking found (4.4), each King James word is kept, changed or dropped by the text; the
shares of italic (translator-supplied) and roman words kept are compared.

``ranges`` records, from each independent translation's layout, the character ranges that hold
its translation text, before any italic word in it is counted: notes and dissertations quote the
King James text and would make an independent translation look dependent (Amendment 11).

``check`` is Amendment 11's check of the italics themselves: ``italics.check_words`` italic
words, drawn with ``italics.check_seed`` from the King James chapters the Book of Mormon
parallels, are looked up in page images of the 1828 Phinney Bible (the Smith family's edition) by
an AI model, a **simulated** check (Amendment 1). The answer per word is ITALIC, ROMAN or
NOT_ON_PAGE; pages are tried best first by how many of the verse's words their OCR holds.
Answers are written as they come and a rerun resumes; an outage reply is never an answer.

``measure`` is the test: inside each span the text's words are re-aligned to the King James
chapter with its italics (``difflib``, as in masking), over the chapter range between the first
and last unbroken match of at least passim's n-gram order (the masking anchor, 4.4); each King
James word there is kept, changed or dropped. R_i, R_r and D = R_r - R_i are pooled per group,
with 95% intervals by bootstrap over spans.

Usage::

    python -m eval.italics ranges   # -> data/italics/translation_ranges.json
    python -m eval.italics check    # -> data/italics/phinney_check.jsonl (model-assisted)
    python -m eval.italics measure  # -> data/italics/measure.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import load as load_config
from metadata.config import stamp

OUT = Path("data/italics")

# How each volume's translation is found, read from its layout (headings), not from its content.
LAYOUT = {
    "internet_archive:isaiahnewtransla01lowt": (
        "volume 1 holds the preliminary dissertation, then the translation from the heading "
        "'ISAIAH.' before 'THE VISION OF ISAIAH' to the end of the volume",
        "from_vision",
    ),
    "internet_archive:isaiahnewtransla02lowt": (
        "volume 2 holds only the notes ('NOTES ON ISAIAH'); no translation text",
        "none",
    ),
    "internet_archive:bim_eighteenth-century_a-new-translation-of-isa_1790": (
        "the translation runs from its first 'SECTION I' to the heading 'NOTES on ISAIAH'; "
        "short textual footnotes on its pages stay in (they cannot be cut from the OCR)",
        "section_to_notes",
    ),
    "institutional_books:AH5KIN": (
        "each psalm runs from its heading 'PSALM <n>.' to the following 'NOTES.' heading",
        "psalm_blocks",
    ),
}
# Gilbert Wakefield's Matthew (1782), listed in Amendment 11, is left out before any count: its
# OCR interleaves translation, Greek notes and scrambled columns line by line, so no range
# holds translation alone (docs/italics-plan.md, deviations before counting).


def _text(wid: str) -> str:
    from ocr_fix.normalize import norm_path

    row = next(
        r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
        ).to_pylist()
        if r["work_id"] == wid
    )
    return norm_path(row).read_text(encoding="utf-8", errors="replace")


def _ranges(rule: str, s: str) -> list[list[int]]:
    if rule == "none":
        return []
    if rule == "from_vision":
        m = re.search(r"ISAIAH\.\s+I\s*S\s*A\s*I\s*A\s*H\.\s+\S*\s*HE\s+VISION", s)
        return [[m.start(), len(s)]] if m else []
    if rule == "section_to_notes":
        a = re.search(r"(?m)^\s*SECTION\s+I\b", s)
        b = re.search(r"NOTES\s+on\s*'?\s*IS", s)
        return [[a.start(), b.start()]] if a and b else []
    if rule == "psalm_blocks":
        heads = [m.start() for m in re.finditer(r"(?m)^\W*PSALM\s+[IVXLC]+\.", s)]
        notes = [m.start() for m in re.finditer(r"(?m)^\s*NOTES\.", s)]
        out = []
        for h in heads:
            nxt = [x for x in notes if x > h]
            following = [x for x in heads if x > h]
            end = min(nxt[0] if nxt else len(s), following[0] if following else len(s))
            out.append([h, end])
        return out
    raise ValueError(rule)


def ranges() -> int:
    cfg = load_config()
    result = {**stamp(), "volumes": {}}
    for wid in cfg["italics"]["independent"]:
        if wid not in LAYOUT:
            result["volumes"][wid] = {"rule": "left out before counting", "ranges": []}
            print(f"{wid}: left out (layout cannot be cut)")
            continue
        how, rule = LAYOUT[wid]
        s = _text(wid)
        rs = _ranges(rule, s)
        chars = sum(b - a for a, b in rs)
        result["volumes"][wid] = {"rule": how, "ranges": rs, "chars": chars, "of": len(s)}
        print(f"{wid}: {len(rs)} ranges, {chars:,} of {len(s):,} characters")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "translation_ranges.json").write_text(json.dumps(result, indent=1) + "\n")
    return 0


PHINNEY = OUT / "phinney"
ITEM = "holybiblecontain00cann"
CHECK = OUT / "phinney_check.jsonl"
UA = "bom-authorship-study/1.0 (https://github.com/lifehug/book-of-mormon-authorship)"
CHECK_MODEL = "sonnet"
PAGES_TRIED = 4  # pages shown in turn until the verse is found


def _kjv() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for ln in Path("data/kjv/kjv.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(ln)
        out.setdefault(f"kjv:{r['book']}.{r['chapter']}", []).append(r)
    return out


def sample_italics(cfg: dict) -> list[dict]:
    """The italic words to check: every italic word in the chapters the Book of Mormon parallels
    (BOM-16's spans name the chapters, nothing else is read), sampled with the registered seed."""
    import random

    from metadata.config import derive_seed

    refs = set()
    for ln in Path("data/kjv_mask/bom/spans.jsonl").read_text().splitlines():
        refs.update(s["ref"] for s in json.loads(ln)["spans"])
    kjv = _kjv()
    pool = []
    for ref in sorted(refs):
        for v in kjv.get(ref, []):
            for k, m in enumerate(re.finditer(r"\[([^\]]+)\]", v["text_marked"])):
                pool.append({"ref": v["ref"], "chapter": ref, "verse": v["verse"],
                             "phrase": m.group(1), "nth": k, "text_marked": v["text_marked"],
                             "text": v["text"]})  # fmt: skip
    rng = random.Random(derive_seed(cfg["italics"]["check_seed"], cfg))
    return rng.sample(pool, cfg["italics"]["check_words"])


def _pages() -> list[str]:
    import gzip

    st = gzip.open(PHINNEY / f"{ITEM}_hocr_searchtext.txt.gz", "rt").read()
    pi = json.load(gzip.open(PHINNEY / f"{ITEM}_hocr_pageindex.json.gz", "rt"))
    return [st[a:b].lower() for a, b, _, _ in pi]


def _best_pages(item: dict, kjv: dict, pages: list[str]) -> list[int]:
    """Pages ranked by how many distinct words of 4+ letters from the verse and its neighbours
    their OCR holds (the scan is two-column, so the OCR interleaves columns)."""
    vs = kjv[item["chapter"]]
    i = next(k for k, v in enumerate(vs) if v["verse"] == item["verse"])
    words = set()
    for v in vs[max(0, i - 1) : i + 2]:
        words |= {w for w in re.findall(r"[a-z]+", v["text"].lower()) if len(w) >= 4}
    sets = [set(re.findall(r"[a-z]+", p)) for p in pages]
    scored = sorted(((len(words & s), k) for k, s in enumerate(sets)), reverse=True)
    best = scored[0][1]
    # a verse's neighbours often spill onto the facing page, so the best page's neighbours come
    # next, then the runner-up
    order = [best, best - 1, best + 1] + [k for _, k in scored[1:3]]
    out = []
    for k in order:
        if 0 <= k < len(pages) and k not in out:
            out.append(k)
    return out[:PAGES_TRIED]


def _leaf_images() -> dict[int, int]:
    """Scan leaf -> the n of its page image. The OCR page index counts every leaf; the image URL
    counts only leaves shown to readers (scandata ``addToAccessFormats``), so the two drift apart
    after each hidden leaf: by one from the cover, by five after the leaves before the New
    Testament."""
    import xml.etree.ElementTree as ET

    root = ET.parse(PHINNEY / f"{ITEM}_scandata.xml").getroot()
    shown = [int(pg.get("leafNum")) for pg in root.iter("page")
             if (pg.findtext("addToAccessFormats") or "true") == "true"]  # fmt: skip
    return {leaf: n for n, leaf in enumerate(shown)}


def _page_image(n: int) -> Path:
    """The page image (kept as downloaded) and a copy resized to 2,000 pixels for the model;
    ``n`` is the image number, not the leaf."""
    import subprocess

    full = PHINNEY / "pages" / f"n{n}.full.jpg"
    out = PHINNEY / "pages" / f"n{n}.jpg"
    if not full.exists():
        full.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://archive.org/download/{ITEM}/page/n{n}.jpg"
        # a dropped download is transient: retried, never recorded as an answer
        cmd = ["curl", "-sfL", "--retry", "5", "--retry-all-errors", "--retry-delay", "10",
               "-A", UA, "--max-time", "300", "-o", str(full), url]  # fmt: skip
        subprocess.run(cmd, check=True)
    if not out.exists():
        subprocess.run(["sips", "-Z", "2000", str(full), "--out", str(out)],
                       check=True, capture_output=True)  # fmt: skip
    return out


def _ask_image(prompt: str, image: Path) -> tuple[str, str]:
    import subprocess

    from metadata.genre import _TRANSIENT, _log_parse_failure

    # the prompt goes first: --allowedTools takes a list and would swallow it
    try:
        done = subprocess.run(
            ["claude", "-p", f"Read the image file {image.resolve()} and answer.\n\n{prompt}",
             "--model", CHECK_MODEL, "--allowedTools", "Read"],
            capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL,
        )  # fmt: skip
    except Exception as exc:  # noqa: BLE001
        _log_parse_failure(CHECK_MODEL, f"<{type(exc).__name__}: {exc}>")
        return "RETRY", ""
    text = done.stdout.strip()
    if not text or _TRANSIENT.search(text) or done.returncode != 0:
        _log_parse_failure(CHECK_MODEL, text or f"<rc={done.returncode}>")
        return "RETRY", text
    return "OK", text


def check() -> int:
    import time

    cfg = load_config()
    items = sample_italics(cfg)
    kjv, pages, images = _kjv(), _pages(), _leaf_images()
    done = {}
    if CHECK.exists():
        for ln in CHECK.read_text().splitlines():
            r = json.loads(ln)
            done[(r["ref"], r["nth"])] = r
    for k, it in enumerate(items, 1):
        key = (it["ref"], it["nth"])
        # NOT_FOUND from before the leaf mapping was fixed was the wrong page, not an answer
        final = ("ITALIC", "ROMAN") + (("NOT_FOUND",) if done.get(key, {}).get("leaves") else ())
        if key in done and done[key]["answer"] in final:
            continue
        context = re.sub(r"\[([^\]]+)\]", r"\1", it["text_marked"])
        answer, tried, raw = "NOT_FOUND", [], ""
        for leaf in _best_pages(it, kjv, pages):
            if leaf not in images:
                continue
            tried.append(leaf)
            prompt = (
                "This is a page from an 1828 printing of the King James Bible, set in two "
                f'columns. Find {it["ref"]}, which reads: "{context}"\n'
                f'In that verse, look at the words "{it["phrase"]}" (occurrence '
                f"{it['nth'] + 1} of the supplied words in the verse). Are they printed in "
                "italic type or in ordinary roman type?\n"
                "Reply with exactly one word: ITALIC, ROMAN, or NOT_ON_PAGE (if the verse is "
                "not on this page)."
            )
            state, raw = "RETRY", ""
            for wait in (0, 60, 300, 900):
                time.sleep(wait)
                state, raw = _ask_image(prompt, _page_image(images[leaf]))
                if state == "OK":
                    break
            if state != "OK":
                answer = "RETRY"  # failed transiently: picked up by the next run
                break
            m = re.findall(r"\b(ITALIC|ROMAN|NOT_ON_PAGE)\b", raw.upper())
            if not m:
                answer = "UNPARSED"
                break
            if m[-1] != "NOT_ON_PAGE":
                answer = m[-1]
                break
        rec = {**{x: it[x] for x in ("ref", "verse", "phrase", "nth")}, "answer": answer,
               "leaves": tried, "raw": raw[-300:], "model": CHECK_MODEL}  # fmt: skip
        with CHECK.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"{k}/{len(items)} {it['ref']} [{it['phrase']}]: {answer} (leaves {tried})",
              flush=True)  # fmt: skip
    last = {}
    for ln in CHECK.read_text().splitlines():
        r = json.loads(ln)
        last[(r["ref"], r["nth"])] = r
    counts: dict[str, int] = {}
    for r in last.values():
        counts[r["answer"]] = counts.get(r["answer"], 0) + 1
    judged = counts.get("ITALIC", 0) + counts.get("ROMAN", 0)
    print(f"answers: {counts}; italic in the 1828 printing: "
          f"{counts.get('ITALIC', 0)}/{judged}")  # fmt: skip
    return 0


def _kjv_marked() -> dict[str, list[tuple[str, bool]]]:
    """KJV chapter -> its words with an italic flag (translators' words are bracketed)."""
    from kjv_mask.align import _WORD, norm_token

    out: dict[str, list[tuple[str, bool]]] = {}
    for ref, verses in _kjv().items():
        words = []
        for v in verses:
            for k, part in enumerate(re.split(r"[\[\]]", v["text_marked"])):
                words += [(norm_token(m.group(0)), k % 2 == 1) for m in _WORD.finditer(part)]
        out[ref] = words
    return out


def span_counts(text: str, ref: str, chapters: dict, seed: int) -> dict[str, int] | None:
    """Kept / changed / dropped counts for italic and roman King James words in one span."""
    from difflib import SequenceMatcher

    from kjv_mask.align import _WORD, norm_token

    kw = chapters.get(ref)
    if not kw:
        return None
    tw = [norm_token(m.group(0)) for m in _WORD.finditer(text)]
    sm = SequenceMatcher(a=[w for w, _ in kw], b=tw, autojunk=False)
    anchors = [b for b in sm.get_matching_blocks() if b.size >= seed]
    if not anchors:
        return None
    a0, a1 = anchors[0].a, anchors[-1].a + anchors[-1].size
    b0, b1 = anchors[0].b, anchors[-1].b + anchors[-1].size
    c = {f"{f}_{x}": 0 for f in ("italic", "roman") for x in ("kept", "changed", "dropped")}
    sub = SequenceMatcher(a=[w for w, _ in kw[a0:a1]], b=tw[b0:b1], autojunk=False)
    for op, i0, i1, _, _ in sub.get_opcodes():
        x = {"equal": "kept", "replace": "changed", "delete": "dropped"}.get(op)
        if x:
            for _, it in kw[a0 + i0 : a0 + i1]:
                c[f"{'italic' if it else 'roman'}_{x}"] += 1
    return c


def _group_spans(group: str, ids: set[str] | None = None) -> list[tuple[str, str, str]]:
    """(doc id, span text, KJV chapter) for every masked span of a group's documents."""
    import gzip

    from kjv_mask.run import _docs

    path = Path(f"data/kjv_mask/{group}/spans.jsonl")
    if group == "controls":
        path = path.with_suffix(".jsonl.gz")
    opener = gzip.open if path.suffix == ".gz" else open
    spans = {}
    with opener(path, "rt") as fh:
        for ln in fh:
            r = json.loads(ln)
            if r["spans"] and (ids is None or r["id"] in ids):
                spans[r["id"]] = r["spans"]
    out = []
    for d in _docs(group):
        if d["id"] in spans:
            text = d["load"]()
            out += [(d["id"], text[s["start"] : s["end"]], s["ref"]) for s in spans[d["id"]]]
    return out


def _rates(rows: list[dict]) -> dict[str, float]:
    tot = {k: sum(r[k] for r in rows) for k in rows[0]} if rows else {}
    ni = sum(v for k, v in tot.items() if k.startswith("italic"))
    nr = sum(v for k, v in tot.items() if k.startswith("roman"))
    ri = tot.get("italic_kept", 0) / ni if ni else float("nan")
    rr = tot.get("roman_kept", 0) / nr if nr else float("nan")
    return {"R_i": ri, "R_r": rr, "D": rr - ri, "italic_words": ni, "roman_words": nr}


def _bootstrap(rows: list[dict], n: int, seed: int) -> dict[str, list[float]]:
    """Percentile 95% intervals, resampling spans with replacement ``n`` times."""
    import numpy as np

    keys = list(rows[0])
    m = np.array([[r[k] for k in keys] for r in rows], dtype=float)
    rng = np.random.default_rng(seed)
    tot = np.stack([m[rng.integers(0, len(rows), len(rows))].sum(0) for _ in range(n)])
    col = {k: tot[:, i] for i, k in enumerate(keys)}
    ni = col["italic_kept"] + col["italic_changed"] + col["italic_dropped"]
    nr = col["roman_kept"] + col["roman_changed"] + col["roman_dropped"]
    with np.errstate(invalid="ignore", divide="ignore"):
        ri, rr = col["italic_kept"] / ni, col["roman_kept"] / nr
    out = {}
    for k, v in (("R_i", ri), ("R_r", rr), ("D", rr - ri)):
        v = v[~np.isnan(v)]
        out[k] = [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] if len(v) else None
    return out


def measure() -> int:
    """Amendment 11's test on the Book of Mormon, the sermons control, the independent
    translations and Amendment 9's texts; counts and rates only, no text."""
    from metadata.config import derive_seed

    cfg = load_config()
    ic, seed = cfg["italics"], cfg["kjv_mask"]["passim"]["ngram"]
    chapters = _kjv_marked()
    lines = Path("data/controls/sermons_1820s.jsonl").read_text().splitlines()
    sermons = {json.loads(ln)["work_id"] for ln in lines}
    ka = {v["work_id"]: json.loads(ln)["key"]
          for ln in Path("data/known_answer/set.jsonl").read_text().splitlines()
          for v in json.loads(ln)["volumes"]}  # fmt: skip
    groups: dict[str, list[dict]] = {}
    texts: dict[str, list[dict]] = {}
    for group, ids, name in (("bom", None, lambda d: "bom"),
                             ("controls", sermons, lambda d: "sermons"),
                             ("italics", None, lambda d: "independent"),
                             ("known_answer", None, lambda d: ka[d])):  # fmt: skip
        for doc, text, ref in _group_spans(group, ids):
            c = span_counts(text, ref, chapters, seed)
            if c is None:
                continue
            g = name(doc)
            groups.setdefault(g, []).append(c)
            texts.setdefault(doc.split("#")[0], []).append(c)
    boot_seed = derive_seed(ic["bootstrap_seed"], cfg)
    out = {"groups": {}, "volumes": {}}
    for g in ["bom", "sermons", "independent"] + sorted(set(ka.values())):
        rows = groups.get(g, [])
        res = {"spans": len(rows), **(_rates(rows) if rows else {})}
        scored = (
            g in ("bom", "sermons", "independent")
            or res.get("italic_words", 0) >= ic["min_italic_words"]
        )
        if rows and scored:
            res["ci95"] = _bootstrap(rows, ic["bootstrap"], boot_seed)
        res["scored"] = bool(rows) and scored
        out["groups"][g] = res
        if rows:
            ci = res.get("ci95") or {}
            print(f"{g:18} spans {len(rows):5}  italic {res['italic_words']:6}  "
                  f"R_i {res['R_i']:.3f} {ci.get('R_i')}  R_r {res['R_r']:.3f}  "
                  f"D {res['D']:+.3f} {ci.get('D')}")  # fmt: skip
    for v, rows in texts.items():
        if v in set(ic["independent"]):
            out["volumes"][v] = {"spans": len(rows), **_rates(rows)}
    a, b = out["groups"]["independent"].get("ci95"), out["groups"]["sermons"].get("ci95")
    if a and b:
        out["shown_to_work"] = a["R_i"][1] < b["R_i"][0] and (
            a["D"][1] < b["D"][0] or b["D"][1] < a["D"][0]
        )
        print(f"shown to work (Amendment 11): {out['shown_to_work']}")
    (OUT / "measure.json").write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"-> {OUT / 'measure.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["ranges"]:
        return ranges()
    if args[:1] == ["check"]:
        return check()
    if args[:1] == ["measure"]:
        return measure()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
