"""BOM-129: New Testament phrases the Book of Mormon uses in a new sense, against period usage.

A reader noted that "a few stripes" (Luke 12:47-48, a servant who did not know his master's will)
is used in 2 Nephi 28 for a sinner who expects light punishment and final salvation, an argument
of the Universalism debate. When the book uses a King James New Testament phrase in a sense its
verse does not have, does print of 1780-1829 use the phrase in that sense more than print of
1640-1779? Step 1: a model reads each New Testament-only phrase of BOM-124 found in the
pre-Christian parts (outside the formal quotation chapters) against its verse and answers SAME or
NEW sense, with the sense in a line. Step 2: for each NEW-sense phrase held by at least 10 library
works in each era, up to 40 uses per era (one per work, seeded) are read, and a model answers
whether each carries the book's sense (YES/NO). Step 3: for "a few stripes", "eat, drink, and be
merry" and NEW-sense phrases on punishment or salvation, the model also codes the use's side on
endless punishment (FOR / AGAINST / NEITHER). The same steps run on *The Late War* and on 20
sermons of the 1650s (decoys). Every model reading is **simulated judging by an AI model**
(``lab.judge``), run by the owner's queue, never by this module. The judge's known-answer check
(60 hand-made items; sonnet against opus on 100 real items) gates the scoring. The test card,
written first, is ``data/private/lab/owner/2026-11-27-new-senses/card.md``; settings are
``lab.new_senses``. Jobs, answers and passages are private; the public result holds phrases (King
James text), ids and counts.

Usage::

    python -m lab.newsenses phrases   # the phrases of the book and the decoys (2 minutes)
    python -m lab.newsenses scan      # library uses of every phrase by era (about an hour; resumes)
    python -m lab.newsenses jobs      # check, step-1 and agreement jobs (private)
    python -m lab.newsenses jobs2     # step-2 library-use jobs from the step-1 answers (gated)
    python -m lab.newsenses score     # check, agreement, then the verdicts -> result.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from lab import door, joined, ntwording
from lab.paths import FAST, NOTES, REGISTRY, out
from lab.wherefore import QUOTED
from metadata import config

OUT = REGISTRY / "reruns" / "new_senses"
WORK = FAST / "new_senses"
CARD = NOTES / "owner" / "2026-11-27-new-senses"
PHRASES = CARD / "phrases.jsonl"  # private: carries the book's passages
CHECK_ITEMS = CARD / "check_items.json"
JOBS = {
    "check": CARD / "jobs_check.jsonl",
    "step1": CARD / "jobs_step1.jsonl",
    "step1_sermons": CARD / "jobs_step1_sermons.jsonl",
    "agree": CARD / "jobs_agree_opus.jsonl",
    "step2": CARD / "jobs_step2.jsonl",
}
ANSWERS = {k: CARD / v.name.replace("jobs_", "answers_") for k, v in JOBS.items()}
EDITION = Path("data/bom/1830/edition_1830.jsonl")
LABELS = Path("data/bom/segments/paragraph_labels.jsonl")
KJV = Path("data/kjv/kjv.jsonl")
WORD = re.compile(r"[a-z]+")
BREAK = 100


def settings(cfg: dict) -> dict:
    return cfg["lab"]["new_senses"]


def _load(path: Path) -> list[dict]:
    return (
        [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []
    )


def _write(path: Path, rows: list[dict]) -> None:
    out(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


# ------------------------------------------------------------------------ documents


class Doc:
    """A text, its words and each word's character span (for passages with a phrase marked)."""

    def __init__(self, name: str, text: str):
        self.name, self.text = name, text
        low = text.lower()
        self.spans = [(m.start(), m.end()) for m in WORD.finditer(low)]
        self.words = [low[a:b] for a, b in self.spans]

    def passage(self, s: int, e: int, k: int) -> str:
        """Words ``s``..``e`` in square brackets, ``k`` words each side, as printed."""
        a = self.spans[max(0, s - k)][0]
        b = self.spans[min(len(self.spans), e + k) - 1][1]
        ps, pe = self.spans[s][0], self.spans[e - 1][1]
        t = self.text
        return " ".join(f"{t[a:ps]}[{t[ps:pe]}]{t[pe:b]}".split())


def bom_docs(w124: dict) -> list[Doc]:
    """The 1830 pre-Christian chapters outside the formal quotation chapters, one doc each."""
    labels = {
        r["seq"]: r for r in map(json.loads, LABELS.read_text().splitlines()) if r["kind"] == "body"
    }
    books = set(w124["before_books"]) | set(w124["ether_books"])
    chap: dict[tuple, list[str]] = {}
    for r in map(json.loads, EDITION.read_text().splitlines()):
        lab = labels.get(r["seq"])
        if lab is None or r["book"] not in books:
            continue
        key = (r["book"], lab["chapter_1830"])
        if key in QUOTED:
            continue
        chap.setdefault(key, []).append(r["text"])
    return [Doc(f"{b} {c}", "\n".join(ps)) for (b, c), ps in chap.items()]


# ------------------------------------------------------------------------ BOM-124's phrases


def nt_universe(cfg: dict) -> tuple:
    """BOM-124's New Testament-only n-grams and its rarity filter at its primary threshold."""
    w = cfg["lab"]["new_testament_wording"]
    sizes = w["ngram_sizes"]
    kjv = ntwording.Kjv([json.loads(x) for x in KJV.read_text().splitlines()])
    uni = ntwording.Universe(kjv, ntwording.build_grams(kjv, sizes))
    bg_rows = ntwording.draw(
        ntwording.eligible(
            cfg,
            lambda r: (
                w["bg_year_min"] <= r["year"] <= w["bg_year_max"]
                and (r["words"] or 0) >= w["bg_min_words"]
            ),
        ),
        w["bg_sample"],
        w["bg_seed"],
        set(),
    )
    bg = ntwording.scan_rows(bg_rows, uni, sizes, w["max_words_per_work"], "background")
    df = [0] * len(uni.grams)
    for _n, matches, _y in bg["done"].values():
        for gid in {g for _p, _n2, g in matches}:
            df[gid] += 1
    n_bg = max(len(bg["done"]), 1)
    allowed = [x / n_bg <= w["bg_max_share"] for x in df]
    return uni, allowed, sizes


def nt_runs(words: list[str], uni, allowed: list[bool], sizes: list[int]) -> list[tuple]:
    """BOM-124's hits in a word list: maximal runs of allowed New Testament-only n-grams."""
    items = []
    for pos, n, gid in ntwording.scan(words, uni, sizes):
        m = uni.masks[gid]
        if allowed[gid] and m & uni.NT and not m & uni.OT:
            items.append((pos, pos + n, gid))
    return [(s, e) for s, e, _g in ntwording.merge_runs(items)]


def find_phrase(words: list[str], phrase: tuple) -> list[int]:
    n = len(phrase)
    return [i for i in range(len(words) - n + 1) if tuple(words[i : i + n]) == phrase]


def collect(source: str, docs: list[Doc], uni, allowed, sizes, d: dict, named: list) -> list:
    """One record per distinct phrase of a source: first place, count, passage (private)."""
    seen: dict[tuple, dict] = {}
    for doc in docs:
        for s, e in nt_runs(doc.words, uni, allowed, sizes):
            p = tuple(doc.words[s:e])
            if p in seen:
                seen[p]["count"] += 1
                continue
            seen[p] = {"source": source, "phrase": " ".join(p), "count": 1, "at": doc.name,
                       "passage": doc.passage(s, e, d["context_words"]),
                       "named": False}  # fmt: skip
    for nm in named:
        p = tuple(nm["book_form"].split())
        for doc in docs:
            hits = find_phrase(doc.words, p)
            if hits:
                rec = seen.setdefault(
                    tuple(nm["library_form"].split()),
                    {"source": source, "phrase": nm["library_form"], "count": 0, "at": doc.name,
                     "passage": doc.passage(hits[0], hits[0] + len(p), d["context_words"])},
                )  # fmt: skip
                rec["count"] += len(hits)
                rec["named"] = True
                rec["refs_given"] = nm["refs"]
    return list(seen.values())


def decoy_docs(d: dict, rows: list[dict]) -> dict[str, list[tuple[dict, Doc]]]:
    """The Late War (file) and the 1650s sermons (library, seeded); each with its own-copy spec."""
    res: dict[str, list] = {}
    lw = d["late_war"]
    text = Path(lw["file"]).read_text(encoding="utf-8", errors="replace")
    res["late_war_1816"] = [({"name": "late_war_1816", **lw}, Doc("late_war_1816", text))]
    pool = sorted(
        (
            r
            for r in rows
            if d["sermons_years"][0] <= r["year"] <= d["sermons_years"][1]
            and "sermon_devotional" in (r["genre"] or "").split(",")
            and (r["words"] or 0) >= d["sermons_min_words"]
        ),
        key=lambda r: r["work_id"],
    )
    random.Random(d["seed"]).shuffle(pool)
    got = []
    for r in pool:
        try:
            got.append((r, Doc(r["work_id"], door.text_of(r))))
        except OSError:
            continue  # unreadable: not attempted
        if len(got) == d["sermons"]:
            break
    res["sermons_1650s"] = got
    return res


def bible_refs(bible: joined.Bible, phrase: tuple, nt_codes: set[str]) -> list[str]:
    """The New Testament verses holding the phrase (its first 4 words if the whole is split)."""
    refs = {bible.refs[v] for v in bible.verses(phrase)}
    if not refs:
        refs = {bible.refs[v] for v in bible.verses(phrase[:4])}
    return sorted(r for r in refs if r.rsplit(" ", 1)[0] in nt_codes) or sorted(refs)


def phrases(cfg: dict) -> dict:
    d, w124 = settings(cfg), cfg["lab"]["new_testament_wording"]
    t0 = time.time()
    uni, allowed, sizes = nt_universe(cfg)
    print(f"BOM-124 sets ready ({time.time() - t0:.0f} s)", flush=True)
    rows = joined.library_rows(d)
    recs = collect("book_of_mormon", bom_docs(w124), uni, allowed, sizes, d, d["named"])
    sermon_ids = []
    for name, items in decoy_docs(d, rows).items():
        docs = [doc for _b, doc in items]
        if name == "sermons_1650s":
            sermon_ids = [b["work_id"] for b, _doc in items]
            for b, doc in items:  # each sermon's phrases, each with its own copies left out later
                for r in collect(name, [doc], uni, allowed, sizes, d, d["named"]):
                    r["work_id"] = b["work_id"]
                    recs.append(r)
        else:
            recs += collect(name, docs, uni, allowed, sizes, d, d["named"])
    bible = joined.Bible([json.loads(x) for x in KJV.read_text().splitlines()], [])
    nt_names = {
        json.loads(x)["book_name"]
        for x in KJV.read_text().splitlines()
        if json.loads(x)["section"] == "NT"
    }
    verse_text = {json.loads(x)["ref"]: json.loads(x)["text"] for x in KJV.read_text().splitlines()}
    for r in recs:
        refs = r.get("refs_given") or bible_refs(bible, tuple(r["phrase"].split()), nt_names)
        r["refs"] = refs[: d["max_verses"]]
        r["verses"] = [verse_text[x] for x in r["refs"] if x in verse_text]
        r["pid"] = hashlib.sha256(f"{r['source']}|{r.get('work_id', '')}|{r['phrase']}".encode()
                                  ).hexdigest()[:12]  # fmt: skip
    _write(PHRASES, recs)
    by = Counter(r["source"] for r in recs)
    res = {"phrases_by_source": dict(by), "sermons_1650s": sermon_ids,
           "distinct_phrases": len({r["phrase"] for r in recs})}  # fmt: skip
    out(OUT / "phrases.json").write_text(json.dumps(res | config.stamp(), indent=1) + "\n")
    return res


# ------------------------------------------------------------------------ library uses


_TABLE: dict = {}


def _init(table: dict) -> None:
    global _TABLE
    _TABLE = table


def first_uses(words: list[str], table: dict) -> dict[int, int]:
    """Phrase id -> its first position in ``words``. ``table``: a phrase's first 4 words (its
    first 2 when shorter) -> [(id, phrase)]."""
    got: dict[int, int] = {}
    n = len(words)
    for i in range(n - 1):
        for k in (4, 2):
            if i + k > n:
                continue
            for pid, p in table.get(tuple(words[i : i + k]), ()):
                if pid not in got and len(p) >= k and tuple(words[i : i + len(p)]) == p:
                    got[pid] = i
    return got


def phrase_table(plist: list[str]) -> dict[tuple, list]:
    table: dict[tuple, list] = defaultdict(list)
    for i, p in enumerate(plist):
        t = tuple(p.split())
        table[t[:4] if len(t) >= 4 else t[:2]].append((i, t))
    return dict(table)


def _scan(row: dict) -> tuple[str, dict | None]:
    try:
        words = joined.tokens(door.text_of(row))
    except OSError:
        return row["work_id"], None
    return row["work_id"], first_uses(words, _TABLE)


def scan(cfg: dict) -> dict:
    d = settings(cfg)
    recs = _load(PHRASES)
    if not recs:
        raise SystemExit("no phrases yet: run `python -m lab.newsenses phrases`")
    plist = sorted({r["phrase"] for r in recs})
    table = phrase_table(plist)
    rows = sorted(joined.library_rows(d), key=lambda r: r["work_id"])
    digest = hashlib.sha256(json.dumps([plist, len(rows)]).encode()).hexdigest()[:12]
    folder = WORK / f"scan_{digest}"
    parts = [rows[i : i + d["part_size"]] for i in range(0, len(rows), d["part_size"])]
    t0 = time.time()
    print(f"{len(plist):,} phrases, {len(rows):,} works, {len(parts)} parts", flush=True)
    with ProcessPoolExecutor(d["workers"], initializer=_init, initargs=(table,)) as pool:
        for k, part in enumerate(parts):
            f = folder / f"part_{k:04d}.jsonl"
            if f.exists():
                continue
            lines = []
            for wid, got in pool.map(_scan, part, chunksize=16):
                if got is None:
                    lines.append({"work_id": wid, "state": "unreadable"})
                elif got:
                    lines.append({"work_id": wid, "uses": {plist[i]: p for i, p in got.items()}})
            tmp = out(folder / f".part_{k:04d}.tmp")
            tmp.write_text("".join(json.dumps(x) + "\n" for x in lines))
            tmp.rename(f)
            print(f"  part {k + 1}/{len(parts)} ({time.time() - t0:.0f} s)", flush=True)
    out(WORK / "latest.json").write_text(json.dumps({"folder": str(folder), "works": len(rows)}))
    return {"folder": str(folder), "works": len(rows), "phrases": len(plist)}


def load_uses() -> tuple[dict[str, dict[str, int]], list[str], int]:
    """phrase -> {work id: first position}; unreadable work ids; works read."""
    meta = json.loads((WORK / "latest.json").read_text())
    uses: dict[str, dict[str, int]] = defaultdict(dict)
    bad = []
    for f in sorted(Path(meta["folder"]).glob("part_*.jsonl")):
        for r in _load(f):
            if r.get("state") == "unreadable":
                bad.append(r["work_id"])
                continue
            for p, pos in r["uses"].items():
                uses[p][r["work_id"]] = pos
    return uses, bad, meta["works"]


def era_of(year: int, d: dict) -> str | None:
    for name, (a, b) in d["eras"].items():
        if a <= year <= b:
            return name
    return None


def own_spec(rec: dict, d: dict, meta: dict) -> dict:
    if rec["source"] == "book_of_mormon":
        return {"exclude_title": d["bom_exclude_title"]}
    if rec["source"] == "late_war_1816":
        return d["late_war"]
    m = meta[rec["work_id"]]
    return {k: m[k] for k in ("work_id", "author", "title", "group")}


def eligible_uses(rec: dict, uses: dict, rows: list[dict], meta: dict, d: dict, cache: dict):
    """era -> sorted work ids holding the phrase, the source's own copies left out."""
    key = rec["source"] + "|" + rec.get("work_id", "")
    if key not in cache:
        cache[key] = joined.own_copies(own_spec(rec, d, meta), rows, d)
    skip = cache[key]
    by: dict[str, list[str]] = defaultdict(list)
    for w in uses.get(rec["phrase"], {}):
        if w in skip or w not in meta:
            continue
        e = era_of(meta[w]["year"], d)
        if e:
            by[e].append(w)
    return {e: sorted(ws) for e, ws in by.items()}


def enough(by: dict, d: dict) -> bool:
    return all(len(by.get(e, [])) >= d["min_uses_per_era"] for e in d["eras"])


# ------------------------------------------------------------------------ prompts


def step1_prompt(phrase: str, refs: list[str], verses: list[str], passage: str) -> str:
    bible = "\n".join(f"{r}: {v}" for r, v in zip(refs, verses, strict=False))
    return (
        "This is a question about how a phrase of the King James Bible is used in another book.\n\n"
        f'The phrase: "{phrase}"\n\nKing James Bible:\n{bible}\n\n'
        f"Passage from the other book (the phrase is in square brackets):\n{passage}\n\n"
        "Is the bracketed phrase used in the passage in the SAME sense as in the Bible verse, or "
        "in a NEW sense the verse does not give it? Quoting or applying the verse with its own "
        "meaning is SAME. NEW means the phrase is made to mean something else, or to support a "
        "claim the verse does not make.\n\nReply in exactly three lines:\nSAME or NEW\n"
        "SENSE: one short sentence saying what the phrase means or claims in the passage\n"
        "TOPIC: AFTERLIFE if the passage is about punishment after death or final salvation, "
        "otherwise OTHER"
    )


def step2_prompt(phrase: str, sense: str, passage: str, side: bool) -> str:
    q = (
        "This is a question about how a phrase is used in a printed passage.\n\n"
        f'The phrase: "{phrase}"\nThe sense asked about: {sense}\n\n'
        f"Passage (the phrase is in square brackets):\n{passage}\n\n"
        "Does the passage use the bracketed phrase in the sense asked about? Answer YES or NO on "
        "the first line."
    )
    if side:
        q += (
            "\nOn a second line write SIDE: FOR if the passage holds that the punishment of the "
            "wicked after death is endless, AGAINST if it holds that such punishment ends or that "
            "all will finally be saved, NEITHER if it takes no side."
        )
    return q


def parse1(reply: str | None) -> dict | None:
    if not reply:
        return None
    m = (
        re.search(r"\b(SAME|NEW)\b", reply.strip().splitlines()[0].upper())
        if reply.strip()
        else None
    )
    if not m:
        return None
    sense = re.search(r"SENSE\s*:\s*(.+)", reply, re.I)
    topic = re.search(r"TOPIC\s*:\s*\**\s*(AFTERLIFE|OTHER)", reply, re.I)
    return {"answer": m.group(1), "sense": sense.group(1).strip() if sense else None,
            "topic": topic.group(1).upper() if topic else None}  # fmt: skip


def parse2(reply: str | None) -> dict | None:
    if not reply or not reply.strip():
        return None
    m = re.match(r"\W*(YES|NO)\b", reply.strip(), re.I)
    if not m:
        return None
    s = re.search(r"SIDE\s*:\s*\**\s*(FOR|AGAINST|NEITHER)", reply, re.I)
    return {"answer": m.group(1).upper(), "side": s.group(1).upper() if s else None}


# ------------------------------------------------------------------------ jobs


def check_jobs(kjv: dict[str, str], d: dict) -> list[dict]:
    items = json.loads(CHECK_ITEMS.read_text())
    jobs = []
    for i, it in enumerate(items["same"]):
        v = kjv[it["ref"]]
        jobs.append({"id": f"check|same|{i}", "expected": "SAME",
                     "prompt": step1_prompt(it["phrase"], [it["ref"]], [v],
                                            mark(v, it["phrase"]))})  # fmt: skip
    for i, it in enumerate(items["new"]):
        jobs.append({"id": f"check|new|{i}", "expected": "NEW",
                     "prompt": step1_prompt(it["phrase"], [it["ref"]], [kjv[it["ref"]]],
                                            mark(it["passage"], it["phrase"]))})  # fmt: skip
    for i, it in enumerate(items["use"]):
        jobs.append({"id": f"check|use|{i}", "expected": it["expected"], "side": it["side"],
                     "prompt": step2_prompt(it["phrase"], it["sense"],
                                            mark(it["passage"], it["phrase"]), True)})  # fmt: skip
    return jobs


def mark(text: str, phrase: str) -> str:
    """The text with the phrase's first occurrence (punctuation between words allowed) bracketed."""
    pat = r"\b" + r"[\W_]+".join(WORD.findall(phrase.lower())) + r"\b"
    m = re.search(pat, text, re.I)
    if not m:
        raise ValueError(f"phrase not in its passage: {phrase}")
    return " ".join(f"{text[: m.start()]}[{text[m.start() : m.end()]}]{text[m.end() :]}".split())


def jobs(cfg: dict) -> dict:
    d = settings(cfg)
    kjv = {json.loads(x)["ref"]: json.loads(x)["text"] for x in KJV.read_text().splitlines()}
    recs = _load(PHRASES)
    uses, _bad, _n = load_uses()
    rows = joined.library_rows(d)
    meta = {r["work_id"]: r for r in rows}
    cache: dict = {}
    step1, kept = [], Counter()
    for r in recs:
        by = eligible_uses(r, uses, rows, meta, d, cache)
        if not (r.get("named") or enough(by, d)):
            continue
        kept[r["source"]] += 1
        step1.append({"id": f"s1|{r['pid']}", "source": r["source"],
                      "prompt": step1_prompt(r["phrase"], r["refs"], r["verses"],
                                             r["passage"])})  # fmt: skip
    chk = check_jobs(kjv, d)
    bom = [j for j in step1 if j["source"] == "book_of_mormon"]
    rng = random.Random(d["seed"])
    agree = rng.sample(bom, min(d["agreement_items"], len(bom)))
    _write(JOBS["check"], [{"id": j["id"], "prompt": j["prompt"]} for j in chk])
    sermons = [j for j in step1 if j["source"] == "sermons_1650s"]
    _write(JOBS["step1"], [{"id": j["id"], "prompt": j["prompt"]} for j in step1
                           if j["source"] != "sermons_1650s"])  # fmt: skip
    _write(JOBS["step1_sermons"], [{"id": j["id"], "prompt": j["prompt"]} for j in sermons])
    _write(JOBS["agree"], [{"id": j["id"], "prompt": j["prompt"]} for j in agree])
    _write(CARD / "check_key.jsonl", [{k: v for k, v in j.items() if k != "prompt"} for j in chk])
    res = {"check": len(chk), "step1": len(step1), "step1_by_source": dict(kept),
           "agreement_opus": len(agree),
           "phrases_by_source": dict(Counter(r["source"] for r in recs))}  # fmt: skip
    out(OUT / "jobs.json").write_text(json.dumps(res | config.stamp(), indent=1) + "\n")
    return res


def answers(name: str) -> dict[str, str]:
    names = [name, "step1_sermons"] if name == "step1" else [name]
    return {r["id"]: r["reply"] for n in names for r in _load(ANSWERS[n])}


def kappa(a: list[str], b: list[str]) -> float | None:
    """Cohen's kappa of two raters' labels on the same items."""
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    labs = set(a) | set(b)
    pe = sum((a.count(k) / n) * (b.count(k) / n) for k in labs)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else None


def check_result(d: dict) -> dict:
    """The judge's check: 90% right on each kind; sonnet and opus kappa on the real items."""
    key = {r["id"]: r for r in _load(CARD / "check_key.jsonl")}
    got = answers("check")
    res: dict = {"kinds": {}}
    for kind in ("same", "new", "use"):
        ids = [i for i in key if i.startswith(f"check|{kind}|")]
        open_ = [i for i in ids if i not in got]
        parsed = {i: (parse2 if kind == "use" else parse1)(got.get(i)) for i in ids if i in got}
        right = sum(1 for i, p in parsed.items() if p and p["answer"] == key[i]["expected"])
        k = {"items": len(ids), "not_yet_answered": len(open_),
             "unparsed": sum(1 for p in parsed.values() if p is None), "right": right,
             "share": round(right / len(ids), 4) if ids else None}  # fmt: skip
        if kind == "use":
            sides = [(p["side"], key[i]["side"]) for i, p in parsed.items() if p]
            k["side_right"] = sum(a == b for a, b in sides)
            k["side_items"] = len(sides)
        res["kinds"][kind] = k
    s1, op = answers("step1"), answers("agree")
    pairs = [(parse1(s1.get(i)), parse1(op[i])) for i in op if i in s1]
    pairs = [(a["answer"], b["answer"]) for a, b in pairs if a and b]
    agree_ids = [j["id"] for j in _load(JOBS["agree"])]
    res["agreement"] = {"items": len(agree_ids), "both_answered": len(pairs),
                        "kappa": kappa([a for a, _ in pairs], [b for _, b in pairs]),
                        "bar": d["kappa_bar"]}  # fmt: skip
    res["bar"] = d["check_bar"]
    complete = all(k["not_yet_answered"] == 0 for k in res["kinds"].values())
    agree_done = len(pairs) >= d["agreement_min_answered"] * len(agree_ids)
    res["attempted"] = complete
    res["items_passed"] = complete and all(
        k["share"] is not None and k["share"] >= d["check_bar"] for k in res["kinds"].values()
    )
    kap = res["agreement"]["kappa"]
    res["agreement_passed"] = agree_done and kap is not None and kap >= d["kappa_bar"]
    res["passed"] = res["items_passed"] and res["agreement_passed"]
    return res


def step2_sources(d: dict) -> list[dict]:
    """The step-1 records answered NEW, each with its parsed sense and topic."""
    s1 = answers("step1")
    recs = {r["pid"]: r for r in _load(PHRASES)}
    got = []
    for jid, reply in s1.items():
        p = parse1(reply)
        r = recs.get(jid.split("|", 1)[1])
        if p and r and p["answer"] == "NEW" and p["sense"]:
            got.append(r | {"sense": p["sense"], "topic": p["topic"]})
    return got


def jobs2(cfg: dict, force_unchecked: bool = False) -> dict:
    """Library-use questions for every NEW-sense phrase with enough uses in each era."""
    d = settings(cfg)
    chk = check_result(d)
    if not chk["passed"] and not force_unchecked:
        raise SystemExit("the judge's check or agreement is not passed (or not complete): "
                         "no step-2 jobs")  # fmt: skip
    uses, _bad, _n = load_uses()
    rows = joined.library_rows(d)
    meta = {r["work_id"]: r for r in rows}
    cache: dict = {}
    plan, docs = [], {}
    side_names = {n["library_form"] for n in d["named"]}
    for r in step2_sources(d):
        by = eligible_uses(r, uses, rows, meta, d, cache)
        if not enough(by, d):
            continue
        side = r["phrase"] in side_names or r.get("topic") == "AFTERLIFE"
        for era, ws in by.items():
            rng = random.Random(f"{d['seed']}|{r['pid']}|{era}")
            for w in rng.sample(ws, min(d["uses_per_era"], len(ws))):
                plan.append((r, era, w, side))
                docs.setdefault(w, None)
    print(f"{len(plan):,} uses to read from {len(docs):,} works", flush=True)
    jobs_, missing = [], 0
    for w in sorted(docs):
        try:
            docs[w] = Doc(w, door.text_of(meta[w]))
        except OSError:
            docs[w] = None
    for r, era, w, side in plan:
        doc = docs[w]
        p = tuple(r["phrase"].split())
        pos = uses[r["phrase"]][w]
        if doc is None or tuple(doc.words[pos : pos + len(p)]) != p:
            missing += 1  # unreadable or changed since the scan: not attempted
            continue
        jobs_.append({"id": f"s2|{r['pid']}|{era}|{w}",
                      "prompt": step2_prompt(r["phrase"], r["sense"],
                                             doc.passage(pos, pos + len(p), d["context_words"]),
                                             side)})  # fmt: skip
    _write(JOBS["step2"], jobs_)
    return {"step2": len(jobs_), "not_attempted": missing,
            "phrases": len({j["id"].split("|")[1] for j in jobs_})}  # fmt: skip


# ------------------------------------------------------------------------ score


def boot_ci(xs: list[float], n: int, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choice(xs) for _ in xs) for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def verdict(diffs: list[float], d: dict) -> dict:
    if not diffs:
        return {"phrases": 0, "verdict": "cannot tell"}
    mean = statistics.fmean(diffs)
    lo, hi = boot_ci(diffs, d["boot"], d["seed"])
    if mean >= d["period_points"] and lo > 0:
        v = "period sense"
    elif abs(mean) <= d["older_points"] or mean < 0:
        v = "older sense"
    else:
        v = "cannot tell"
    return {"phrases": len(diffs), "mean_difference": round(mean, 4),
            "ci95": [round(lo, 4), round(hi, 4)], "verdict": v}  # fmt: skip


def score(cfg: dict) -> dict:
    d = settings(cfg)
    res: dict = {
        "judging": "simulated judging by an AI model (lab.judge; step 1 and 2 by "
        f"{d['model']}, agreement by {d['agreement_model']})",
        "card": str(CARD / "card.md"),
        **config.stamp(),
    }
    chk = check_result(d)
    res["known_answer"] = chk
    if not chk["passed"]:
        res["stopped"] = "the judge's check or the agreement is not passed: nothing is scored"
        return res
    s1 = {i: parse1(r) for i, r in answers("step1").items()}
    recs = {r["pid"]: r for r in _load(PHRASES)}
    step1 = defaultdict(Counter)
    for i, p in s1.items():
        src = recs[i.split("|", 1)[1]]["source"]
        step1[src][p["answer"] if p else "unparsed"] += 1
    res["step1"] = {k: dict(v) for k, v in step1.items()}
    s2 = {i: parse2(r) for i, r in answers("step2").items()}
    asked = [j["id"] for j in _load(JOBS["step2"])]
    res["step2_open"] = len([i for i in asked if i not in s2])
    per: dict[str, dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
    for i in asked:
        _s, pid, era, _w = i.split("|", 3)
        p = s2.get(i)
        c = per[pid][era]
        c["asked"] += 1
        if p is None:
            c["open_or_unparsed"] += 1
            continue
        c["answered"] += 1
        c[p["answer"]] += 1
        if p["side"]:
            c[f"side_{p['side']}"] += 1
            if p["answer"] == "YES":
                c[f"yes_side_{p['side']}"] += 1
    eras = list(d["eras"])
    rows, by_src = [], defaultdict(list)
    for pid, ec in per.items():
        r = recs[pid]
        sh = {e: ec[e]["YES"] / ec[e]["answered"] if ec[e]["answered"] else None for e in eras}
        row = {"source": r["source"], "work_id": r.get("work_id"), "phrase": r["phrase"],
               "refs": r["refs"], "by_era": {e: dict(ec[e]) for e in eras},
               "yes_share": {e: None if v is None else round(v, 4)
                             for e, v in sh.items()}}  # fmt: skip
        if all(v is not None for v in sh.values()):
            row["difference"] = round(sh[eras[1]] - sh[eras[0]], 4)
            by_src[r["source"]].append(row["difference"])
        rows.append(row)
    res["phrases"] = sorted(rows, key=lambda x: (x["source"], x["phrase"]))
    res["verdicts"] = {s: verdict(v, d) for s, v in by_src.items()}
    res["named"] = [x for x in rows if x["phrase"] in {n["library_form"] for n in d["named"]}]
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["phrases", "scan", "jobs", "jobs2", "score"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "phrases":
        print(json.dumps(phrases(cfg), indent=1))
    elif a.cmd == "scan":
        print(json.dumps(scan(cfg), indent=1))
    elif a.cmd == "jobs":
        print(json.dumps(jobs(cfg), indent=1))
    elif a.cmd == "jobs2":
        print(json.dumps(jobs2(cfg), indent=1))
    else:
        res = score(cfg)
        out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: v for k, v in res.items() if k != "phrases"}, indent=1)[:5000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
