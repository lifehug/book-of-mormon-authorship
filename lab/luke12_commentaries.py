"""BOM-131: does the book's use of Luke 12 follow Henry's or Clarke's reading of the verse?

A reader proposed that 2 Nephi 28 depends on Luke 12 as the commentaries of the day read it,
naming Matthew Henry and Adam Clarke. This test asks, for every verse of Luke 12 whose wording the
1830 text reuses (and later the other New Testament verses BOM-129 finds used in a new sense), and
for each of a dozen New Testament commentaries in the library, whether the book's use follows that
commentary's note on the verse. Every answer is **simulated judging by an AI model**
(``lab.judge``); this module writes the questions and scores the answers, and calls no model.

1. **Verses.** A verse is reused where the 1830 text shares with it a word 4-gram, or a pair of
   adjacent content words, that occurs in no other verse of the King James Bible (outside the
   verse's own chapter), the pair's rarer word being rare in the King James Bible. Matches inside a
   King James quotation the study masked (BOM-16) are left out: there the book quotes, it does not
   reuse. ``extra_verses`` adds verses by reference (BOM-129's list goes there).
2. **Notes located.** Each commentary is a list of candidate volumes; in each, every verse of the
   chapter is located by overlapping three-word sequences (BOM-122's lesson: a garbled scan hides
   the King James line, so whole-line matching misses notes), inside the region around the median
   located verse; the volume that locates most verses stands for the commentary. Coverage per
   commentary is reported; a commentary is asked only where its note was located.
3. **The judge's check.** Made-up uses written to follow one commentary's note and not a differing
   note cannot be made without a writer, so a first job file asks a model (``generator_model``) to
   say whether two notes on a verse differ and, if they do, to write such a use; ``check-jobs``
   turns the first ``check_items`` that differ into judge questions (expected YES for the note
   followed, NO for the other).
4. **Score.** Nothing is counted unless the check reaches ``bar_check``. Then each commentary's
   YES rate over its asked verses, and the card's rule.

The test card, written first, is ``data/private/lab/owner/2026-11-27-luke12-commentaries/card.md``;
settings are ``lab.luke12_commentaries``. Questions quote text and stay private; the public files
hold ids, references and counts.

Usage::

    python -m lab.luke12_commentaries jobs        # verses, notes located, the job files
    python -m lab.luke12_commentaries check-jobs  # after the generation answers: the check's jobs
    python -m lab.luke12_commentaries score       # -> .../luke12_commentaries/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from lab.isaiah_judge import fisher_greater, locate, parse, shingle_index
from lab.paths import NOTES, REGISTRY, out
from metadata import config

CARD = NOTES / "owner" / "2026-11-27-luke12-commentaries"
OUT = REGISTRY / "reruns" / "luke12_commentaries"
KJV = Path("data/kjv/kjv.jsonl")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
MASK = Path("data/kjv_mask/bom/spans.jsonl")
FILES = {
    "verses": CARD / "verses.json",
    "gen": CARD / "jobs_gen.jsonl",
    "gen_answers": CARD / "answers_gen.jsonl",
    "check": CARD / "jobs_check.jsonl",
    "check_answers": CARD / "answers_check.jsonl",
    "real": CARD / "jobs_real.jsonl",
    "real_answers": CARD / "answers_real.jsonl",
    "decoy": CARD / "jobs_decoy.jsonl",
    "decoy_answers": CARD / "answers_decoy.jsonl",
    "located": OUT / "located.json",
    "result": OUT / "result.json",
}
WORD = re.compile(r"[a-z]+")
OUR = re.compile(r"^([a-z]{2,})our(s?)$")  # honour/honor: spelling (as lab.isaiah)


def settings(cfg: dict) -> dict:
    return cfg["lab"]["luke12_commentaries"]


def _load(path: Path) -> list[dict]:
    return (
        [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []
    )


def tokens_at(text: str) -> list[tuple[str, int]]:
    """Words (lower case, letters only, lab.isaiah's spelling rule) with their character offsets."""
    return [(OUR.sub(r"\1or\2", m.group(0)), m.start())
            for m in WORD.finditer(text.lower().replace("ſ", "s"))]  # fmt: skip


def tokens(text: str) -> list[str]:
    return [w for w, _ in tokens_at(text)]


# ---------------------------------------------------------------------------------- verses
class Bible:
    """The King James Bible by verse: words, plain text, and which chapters each n-gram is in."""

    def __init__(self, path: Path = KJV) -> None:
        self.words: dict[tuple[str, int, int], list[str]] = {}
        self.text: dict[tuple[str, int, int], str] = {}
        self.ref: dict[tuple[str, int, int], str] = {}
        self.freq: Counter = Counter()
        for line in path.read_text(encoding="utf-8").splitlines():
            v = json.loads(line)
            k = (v["book"], v["chapter"], v["verse"])
            self.words[k] = tokens(v["text"])
            self.text[k] = v["text"]
            self.ref[k] = v["ref"]
            self.freq.update(self.words[k])

    def chapter(self, book: str, ch: int) -> dict[int, list[str]]:
        return {k[2]: w for k, w in self.words.items() if k[0] == book and k[1] == ch}

    def gram_chapters(self, n: int, stop: set[str], pairs: bool) -> dict[tuple, set]:
        out_: dict[tuple, set] = defaultdict(set)
        for k, w in self.words.items():
            seq = [x for x in w if x not in stop] if pairs else w
            for i in range(len(seq) - n + 1):
                out_[tuple(seq[i : i + n])].add(k[:2])
        return out_


def distinctive(
    verse: list[str], chapter: tuple, grams: dict, pair_grams: dict, freq: Counter, d: dict
) -> list[tuple[str, tuple]]:
    """The verse's word 4-grams (at least ``min_content`` content words) and adjacent content-word
    pairs (rarer word at most ``max_pair_word_freq`` in the King James Bible) found in no chapter
    of the Bible but its own."""
    stop = set(d["stop_words"])
    n = d["ngram"]
    res = []
    for i in range(len(verse) - n + 1):
        g = tuple(verse[i : i + n])
        if grams.get(g, set()) <= {chapter} and sum(w not in stop for w in g) >= d["min_content"]:
            res.append(("ngram", g))
    content = [w for w in verse if w not in stop]
    for i in range(len(content) - 1):
        g = tuple(content[i : i + 2])
        if (
            pair_grams.get(g, set()) <= {chapter}
            and min(freq[w] for w in g) <= d["max_pair_word_freq"]
        ):
            res.append(("pair", g))
    return res


def find_uses(
    words: list[str], gram_list: list[tuple[str, tuple]], stop: set[str]
) -> list[tuple[int, str]]:
    """Positions in ``words`` where any of the grams occurs (pairs ignore stop words between)."""
    hits = []
    ng = {g for kind, g in gram_list if kind == "ngram"}
    pr = {g for kind, g in gram_list if kind == "pair"}
    for g in ng:
        n = len(g)
        for i in range(len(words) - n + 1):
            if tuple(words[i : i + n]) == g:
                hits.append((i, " ".join(g)))
    content = [(i, w) for i, w in enumerate(words) if w not in stop]
    for j in range(len(content) - 1):
        g = (content[j][1], content[j + 1][1])
        if g in pr and content[j + 1][0] - content[j][0] <= 4:
            hits.append((content[j][0], " ".join(g)))
    return sorted(set(hits))


def masked_ranges() -> dict[int, list[tuple[int, int]]]:
    res: dict[int, list[tuple[int, int]]] = {}
    for ln in MASK.read_text().splitlines():
        r = json.loads(ln)
        res[int(r["id"].split(":")[1])] = [(s["start"], s["end"]) for s in r["spans"]]
    return res


def book_uses(bible: Bible, refs: list[tuple[str, int, int]], d: dict) -> list[dict]:
    """Each (verse, 1830 paragraph) where the book reuses the verse's distinctive wording."""
    stop = set(d["stop_words"])
    grams = bible.gram_chapters(d["ngram"], stop, pairs=False)
    pairs = bible.gram_chapters(2, stop, pairs=True)
    mask = masked_ranges()
    paras = []
    for ln in EDITION.read_text().splitlines():
        r = json.loads(ln)
        if r["book"]:
            paras.append(r)
    res = []
    for k in refs:
        gl = distinctive(bible.words[k], k[:2], grams, pairs, bible.freq, d)
        if not gl:
            continue
        for p in paras:
            ta = tokens_at(p["text"])
            words = [w for w, _ in ta]
            for pos, g in find_uses(words, gl, stop):
                off = ta[pos][1]
                if any(a <= off < b for a, b in mask.get(p["seq"], [])):
                    continue
                res.append({"ref": bible.ref[k], "key": list(k), "seq": p["seq"], "book": p["book"],
                            "chapter_1830": p["chapter"], "at": pos, "gram": g})  # fmt: skip
    return res


def group_uses(uses: list[dict]) -> list[dict]:
    """One use per (verse, paragraph): the first match, with every matched gram listed."""
    by: dict[tuple, dict] = {}
    for u in uses:
        k = (u["ref"], u["seq"])
        if k not in by:
            by[k] = {**u, "grams": [u["gram"]]}
        elif u["gram"] not in by[k]["grams"]:
            by[k]["grams"].append(u["gram"])
    for v in by.values():
        v.pop("gram")
    return sorted(by.values(), key=lambda u: (u["key"], u["seq"]))


def extra_refs(d: dict, bible: Bible) -> list[tuple[str, int, int]]:
    """Verses added by reference (``extra_verses``, and ``extra_verses_file`` when it exists)."""
    items = list(d.get("extra_verses") or [])
    f = d.get("extra_verses_file")
    if f and Path(f).exists():
        items += [json.loads(x) for x in Path(f).read_text().splitlines() if x.strip()]
    res = []
    for x in items:
        k = (x["book"], int(x["chapter"]), int(x["verse"]))
        if k not in bible.words:
            raise SystemExit(f"extra verse not in the King James Bible: {x}")
        res.append(k)
    return res


# --------------------------------------------------------------------------------- notes
def chapter_region(idx: dict, verses: dict[int, list[str]], g: dict) -> tuple[int, int] | None:
    """Words around the median located verse of the chapter (``region_words`` each side)."""
    starts = sorted(loc["start"] for w in verses.values() if (loc := locate(w, idx, g)))
    if len(starts) < g["min_anchor_verses"]:
        return None
    m = int(statistics.median(starts))
    return max(0, m - g["region_words"]), m + g["region_words"]


def locate_chapter(text: list[str], verses: dict[int, list[str]], g: dict) -> dict[int, dict]:
    """Verse number -> {start, share} for every verse of the chapter located in ``text``."""
    idx = shingle_index(text, g["shingle"])
    reg = chapter_region(idx, verses, g)
    if reg is None:
        return {}
    lo, hi = reg
    res = {}
    for v, w in verses.items():
        loc = locate(w, idx, g, lo, hi)
        if loc is not None:
            res[v] = {"start": loc["start"], "share": loc["share"]}
    return res


_REG: dict[str, dict] = {}


def volume_text(work_id: str) -> list[str] | None:
    import pyarrow.compute as pc

    from lab import door, registry

    cat = door.catalog({work_id})
    if work_id not in cat:
        return None
    if work_id not in _REG:
        t = registry.load()
        rows = t.filter(pc.equal(t["work_id"], work_id)).to_pylist()
        _REG[work_id] = rows[0] if rows else {}
    try:
        return tokens(door.text_of(cat[work_id] | _REG[work_id]))
    except OSError:
        return None  # unreadable: not attempted


def note_window(text: list[str], start: int, d: dict) -> str:
    return " ".join(text[max(0, start - d["note_before"]) : start + d["note_after"]])


# ---------------------------------------------------------------------------------- prompts
def judge_prompt(ref: str, verse_text: str, use: str, note: str) -> str:
    """The one question of BOM-131 (simulated judging by an AI model)."""
    return (
        "Simulated judging by an AI model (lab test BOM-131). "
        f"{ref} in the King James Bible reads: '{verse_text}'\n"
        "(A) is a passage of a book printed before 1831 that uses wording from this verse. "
        "(B) is words from a commentary printed before 1830 around where it prints the verse; "
        "its note on the verse usually follows, sometimes after the text of the next verses, and "
        "sometimes a note on the verses before covers it (lower-cased, punctuation removed). "
        "Does passage (A) use the verse's words in the sense, or with the reading, that this "
        "commentary's note gives the verse? Answer on the first line YES, NO or UNCLEAR, then "
        "one sentence.\n\n(A) " + use + "\n\n(B) " + note
    )


_GEN = """Below are words from two commentaries printed before 1830, each around where it
prints the verse; the note on the verse usually follows it, sometimes a note on the verses before
covers it (lower-cased, punctuation removed). First line: DIFFERENT if the two notes give this
verse different readings (what it means, whom it is about, what it teaches), SAME if they agree or
either note is not about this verse. If DIFFERENT, write after a line 'PASSAGE:' a passage of two
to four sentences in the style of early nineteenth-century scripture that uses words of the verse
in the sense note A gives it and plainly not in the sense of note B. Do not name either
commentary."""


def gen_prompt(ref: str, verse_text: str, note_a: str, note_b: str) -> str:
    """Asks a model to write a made-up use following note A and not note B (simulated)."""
    return (
        "Simulated writing by an AI model, for a known-answer check (lab test BOM-131). "
        f"{ref} in the King James Bible reads: '{verse_text}'\n"
        + " ".join(_GEN.split())
        + "\n\n(A) "
        + note_a
        + "\n\n(B) "
        + note_b
    )


def parse_gen(reply: str) -> str | None:
    """The made-up passage of a DIFFERENT reply; None for SAME or a reply without one."""
    if not re.match(r"\W*DIFFERENT\b", reply.strip(), re.I):
        return None
    m = re.search(r"PASSAGE:\s*(.+)", reply, re.S | re.I)
    text = " ".join(m.group(1).split()) if m else ""
    return text or None


# ------------------------------------------------------------------------------------ jobs
def located_table(commentaries: dict, chapters: dict, g: dict, read=None) -> tuple[dict, dict]:
    """commentary -> chapter -> chosen volume and its located verses (most located wins; the
    first listed volume on a tie), and the chosen volumes' words. Volumes are read one at a
    time and only the chosen ones are kept."""
    read = read or volume_text
    res: dict = {}
    keep: dict[str, list[str]] = {}
    for key, ids in commentaries.items():
        res[key] = {ch: {"work_id": None, "located": {}, "tried": []} for ch in chapters}
        for w in ids:
            t = read(w)
            for ch, verses in chapters.items():
                e = res[key][ch]
                if t is None:
                    e["tried"].append({"work_id": w, "status": "unreadable or not held"})
                    continue
                loc = locate_chapter(t, verses, g)
                e["tried"].append({"work_id": w, "located": len(loc)})
                if e["work_id"] is None or len(loc) > len(e["located"]):
                    e["work_id"], e["located"] = w, loc
            if t is not None and any(res[key][ch]["work_id"] == w for ch in chapters):
                keep[w] = t
        chosen = {res[key][ch]["work_id"] for ch in chapters}
        for w in [w for w in keep if w in ids and w not in chosen]:
            del keep[w]
    return res, keep


def build(cfg: dict) -> dict:
    d = settings(cfg)
    bible = Bible()
    luke = [("LUK", 12, v) for v in sorted(bible.chapter("LUK", 12))]
    found = group_uses(book_uses(bible, luke, d))
    extra = extra_refs(d, bible)
    if extra:
        found += group_uses(book_uses(bible, extra, d | {"max_pair_word_freq": 10**9,
                                                         "min_content": 1}))  # fmt: skip
    asked_refs = sorted({tuple(u["key"]) for u in found})
    chapters = {f"{b} {c}": bible.chapter(b, c) for b, c in sorted({k[:2] for k in asked_refs})}
    if "LUK 12" not in chapters:
        chapters["LUK 12"] = bible.chapter("LUK", 12)
    g = d["locator"]
    loc, texts = located_table({k: v["volumes"] for k, v in d["commentaries"].items()}, chapters, g)

    # the book's passages
    paras = {json.loads(x)["seq"]: json.loads(x) for x in EDITION.read_text().splitlines()}

    def use_text(u: dict) -> str:  # noqa: E306
        w = tokens(paras[u["seq"]]["text"])
        return " ".join(w[max(0, u["at"] - d["use_before"]) : u["at"] + d["use_after"]])

    real = []
    asked = Counter()
    for u in found:
        k = tuple(u["key"])
        ch = f"{k[0]} {k[1]}"
        for key, by in loc.items():
            entry = by[ch]
            if k[2] not in entry["located"]:
                continue
            note = note_window(texts[entry["work_id"]], entry["located"][k[2]]["start"], d)
            prompt = judge_prompt(u["ref"], bible.text[k], use_text(u), note)
            real.append({"id": f"{key}|{u['ref']}|{u['seq']}", "prompt": prompt})
            asked[key] += 1

    # decoy: The Late War's uses of the same verses' wording
    lw = volume_text(d["decoy_work"]) or []
    stop = set(d["stop_words"])
    grams = bible.gram_chapters(d["ngram"], stop, pairs=False)
    pair_g = bible.gram_chapters(2, stop, pairs=True)
    decoy_uses = []
    for k in asked_refs:
        gl = distinctive(bible.words[k], k[:2], grams, pair_g, bible.freq, d)
        for pos, gram in find_uses(lw, gl, stop):
            decoy_uses.append({"ref": bible.ref[k], "key": list(k), "at": pos, "grams": [gram],
                               "by": "reuse rule"})  # fmt: skip
    for x in d.get("decoy_phrases") or []:
        k = (x["book"], int(x["chapter"]), int(x["verse"]))
        ph = tokens(x["phrase"])
        for pos in range(len(lw) - len(ph) + 1):
            if lw[pos : pos + len(ph)] == ph:
                decoy_uses.append({"ref": bible.ref[k], "key": list(k), "at": pos,
                                   "grams": [x["phrase"]], "by": "decoy_phrases"})  # fmt: skip
    decoy = []
    for u in decoy_uses:
        k = tuple(u["key"])
        use = " ".join(lw[max(0, u["at"] - d["use_before"]) : u["at"] + d["use_after"]])
        for key, by in loc.items():
            entry = by.get(f"{k[0]} {k[1]}", {"located": {}})
            if k[2] in entry["located"]:
                note = note_window(texts[entry["work_id"]], entry["located"][k[2]]["start"], d)
                prompt = judge_prompt(u["ref"], bible.text[k], use, note)
                decoy.append({"id": f"decoy|{key}|{u['ref']}|{u['at']}", "prompt": prompt})

    # generation jobs for the check: pairs of commentaries located at the same Luke 12 verse
    pool = []
    keys = sorted(loc)
    for v in sorted(chapters["LUK 12"]):
        have = [key for key in keys if v in loc[key]["LUK 12"]["located"]]
        for i, a in enumerate(have):
            for b in have[i + 1 :]:
                pool.append((v, a, b))
    rng = random.Random(d["seed"])
    rng.shuffle(pool)
    gen = []
    for n, (v, a, b) in enumerate(pool[: d["gen_items"]]):
        if rng.random() < 0.5:
            a, b = b, a
        na = note_window(
            texts[loc[a]["LUK 12"]["work_id"]], loc[a]["LUK 12"]["located"][v]["start"], d
        )
        nb = note_window(
            texts[loc[b]["LUK 12"]["work_id"]], loc[b]["LUK 12"]["located"][v]["start"], d
        )
        k = ("LUK", 12, v)
        gen.append({"id": f"gen|{n}|{bible.ref[k]}|{a}|{b}",
                    "prompt": gen_prompt(bible.ref[k], bible.text[k], na, nb)})  # fmt: skip

    for name, js in (("real", real), ("decoy", decoy), ("gen", gen)):
        out(FILES[name]).write_text("".join(json.dumps(j) + "\n" for j in js))
    private = {"what": "BOM-131 working file (quotes the 1830 text's matched words); private",
               "uses": found, "decoy_uses": decoy_uses}  # fmt: skip
    out(FILES["verses"]).write_text(json.dumps(private, indent=1) + "\n")

    luke_n = len(chapters["LUK 12"])
    cov = {}
    for key, by in loc.items():
        e = by["LUK 12"]
        n_loc = len(e["located"])
        used = [tuple(u["key"]) for u in found]
        cov[key] = {
            "work_id": e["work_id"], "label": d["commentaries"][key]["label"],
            "luke12_verses_located": n_loc, "luke12_verses": luke_n,
            "luke12_coverage": round(n_loc / luke_n, 4),
            "meets_bar": n_loc / luke_n >= d["bar_located"],
            "asked_verses_located": sum(1 for k in set(used)
                                        if k[2] in loc[key][f"{k[0]} {k[1]}"]["located"]),
            "real_questions": asked[key],
            "located_verses": sorted(e["located"]),
            "median_share": (round(statistics.median(x["share"] for x in e["located"].values()), 4)
                             if e["located"] else None),
            "tried": e["tried"],
            "other_chapters": {ch: {"work_id": x["work_id"], "located": len(x["located"])}
                               for ch, x in by.items() if ch != "LUK 12"},
        }  # fmt: skip
    pub = {
        "what": "BOM-131: notes located per commentary (ids and counts, no text); questions "
        "are for simulated judging by an AI model, not yet asked",
        "bar_located": d["bar_located"],
        "verses_reused": sorted({u["ref"] for u in found}, key=lambda r: [int(x) for x in
                                                                          r.split()[-1].split(":")]),
        "uses": [{"ref": u["ref"], "seq": u["seq"], "book": u["book"],
                  "chapter_1830": u["chapter_1830"], "grams": u["grams"]} for u in found],
        "decoy": {"work_id": d["decoy_work"], "read": bool(lw),
                  "uses": [{"ref": u["ref"], "at": u["at"], "grams": u["grams"]}
                           for u in decoy_uses]},
        "commentaries": cov,
        "commentaries_meeting_bar": sum(c["meets_bar"] for c in cov.values()),
        "jobs": {"real": len(real), "decoy": len(decoy), "generation": len(gen),
                 "check_to_come": 2 * d["check_items"]},
        "config_sha256": config.sha256_of_config(),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                 text=True).stdout.strip(),
    }  # fmt: skip
    out(FILES["located"]).write_text(json.dumps(pub, indent=1) + "\n")
    return pub


def check_jobs(cfg: dict) -> dict:
    """From the generation answers: the first ``check_items`` made-up uses, each asked about the
    note it follows (expected YES) and the differing note (expected NO)."""
    d = settings(cfg)
    gen = {j["id"]: j for j in _load(FILES["gen"])}
    ans = {r["id"]: r["reply"] for r in _load(FILES["gen_answers"])}
    open_ = [i for i in gen if i not in ans]
    items = []
    for i in gen:  # in the shuffled order the generation jobs were written
        if i not in ans:
            continue
        p = parse_gen(ans[i])
        if p:
            items.append((i, p))
    if len(items) < d["check_items"] and open_:
        raise SystemExit(f"{len(items)} made-up uses so far, {len(open_)} generation jobs open")
    jobs_ = []
    for i, passage in items[: d["check_items"]]:
        _, n, ref, a, b = i.split("|")
        prompt = gen[i]["prompt"]
        verse = re.search(r"reads: '(.*?)'\n", prompt).group(1)
        na = prompt.split("\n\n(A) ", 1)[1].split("\n\n(B) ", 1)[0]
        nb = prompt.split("\n\n(B) ", 1)[1]
        jobs_ += [
            {"id": f"check|{n}|{a}|yes", "prompt": judge_prompt(ref, verse, passage, na)},
            {"id": f"check|{n}|{b}|no", "prompt": judge_prompt(ref, verse, passage, nb)},
        ]
    out(FILES["check"]).write_text("".join(json.dumps(j) + "\n" for j in jobs_))
    return {"made_up_uses": len(items), "used": len(jobs_) // 2, "check_jobs": len(jobs_),
            "generation_open": len(open_)}  # fmt: skip


# ----------------------------------------------------------------------------------- score
def check_of(ids: list[str], ans: dict[str, str | None], bar: float, need: int) -> dict:
    """An item is right when its YES question is answered YES and its NO question NO."""
    items: dict[str, dict] = defaultdict(dict)
    for i in ids:
        _, n, _key, exp = i.split("|")
        items[n][exp] = ans.get(i)
    done = {n: v for n, v in items.items() if v.get("yes") and v.get("no")}
    right = sum(v["yes"] == "YES" and v["no"] == "NO" for v in done.values())
    res = {"items": len(items), "answered": len(done), "right": right,
           "rate": round(right / len(done), 4) if done else None, "bar": bar,
           "yes_right": sum(v.get("yes") == "YES" for v in done.values()),
           "no_right": sum(v.get("no") == "NO" for v in done.values())}  # fmt: skip
    res["attempted"] = len(items) >= need and len(done) == len(items)
    res["passed"] = bool(res["attempted"] and res["rate"] >= bar)
    return res


def rates(ans: dict[str, str | None], ids: list[str]) -> dict[str, dict]:
    by: dict[str, Counter] = defaultdict(Counter)
    verses: dict[str, set] = defaultdict(set)
    for i in ids:
        parts = i.split("|")
        key, ref = (parts[1], parts[2]) if parts[0] == "decoy" else (parts[0], parts[1])
        a = ans.get(i)
        if a is None:
            by[key]["open_or_unparsed"] += 1
            continue
        by[key]["asked"] += 1
        by[key][a.lower()] += 1
        verses[key].add(ref)
    return {k: {**c, "verses": len(verses[k]),
                "rate": round(c["yes"] / c["asked"], 4) if c["asked"] else None}
            for k, c in by.items()}  # fmt: skip


def verdict(r: dict[str, dict], named: list[str], d: dict) -> dict:
    """The card's rule: a named commentary is the answer if its YES rate is the highest and at
    least ``lead_points`` above the median commentary, on at least ``min_verses`` verses; neither
    if every named commentary sits inside the middle half; otherwise cannot tell."""
    scored = {k: v for k, v in r.items() if v.get("rate") is not None}
    if len(scored) < d["min_commentaries"]:
        return {"verdict": "cannot tell", "why": f"{len(scored)} commentaries scored"}
    vals = sorted(v["rate"] for v in scored.values())
    med = statistics.median(vals)
    q1, _, q3 = statistics.quantiles(vals, n=4, method="inclusive")
    top = max(scored, key=lambda k: scored[k]["rate"])
    tied = [k for k in scored if scored[k]["rate"] == scored[top]["rate"]]
    res = {"median": med, "middle_half": [q1, q3], "highest": sorted(tied)}
    for k in named:
        if k not in scored:
            continue
        v = scored[k]
        if (tied == [k] and v["rate"] - med >= d["lead_points"] / 100
                and v["verses"] >= d["min_verses"]):  # fmt: skip
            return res | {"verdict": k}
    if all(k in scored and q1 <= scored[k]["rate"] <= q3 for k in named):
        return res | {"verdict": "neither"}
    return res | {"verdict": "cannot tell"}


def score(cfg: dict) -> dict:
    d = settings(cfg)
    a_chk = {r["id"]: parse(r["reply"]) for r in _load(FILES["check_answers"])}
    chk = check_of([j["id"] for j in _load(FILES["check"])], a_chk, d["bar_check"],
                   d["check_items"])  # fmt: skip
    res: dict = {
        "judging": f"simulated judging by an AI model (lab.judge, model {d['judge_model']}); "
        f"made-up uses written by {d['generator_model']} (simulated)",
        "known_answer": chk,
        "located": json.loads(FILES["located"].read_text())["commentaries"]
        if FILES["located"].exists() else None,
    }  # fmt: skip
    if res["located"]:
        res["located"] = {k: {x: v[x] for x in ("work_id", "luke12_coverage", "meets_bar",
                                                 "real_questions")}
                          for k, v in res["located"].items()}  # fmt: skip
    if not chk["passed"]:
        res["stopped"] = "the judge's known-answer check is not passed or not complete"
        return res
    real_ids = [j["id"] for j in _load(FILES["real"])]
    a_real = {r["id"]: parse(r["reply"]) for r in _load(FILES["real_answers"])}
    res["real"] = rates(a_real, real_ids)
    res["real_open"] = sum(i not in a_real for i in real_ids)
    res["verdict"] = verdict(res["real"], d["named"], d)
    if res["real_open"]:
        res["verdict"] = {"verdict": "not attempted", "why": f"{res['real_open']} questions open"}
    dec_ids = [j["id"] for j in _load(FILES["decoy"])]
    a_dec = {r["id"]: parse(r["reply"]) for r in _load(FILES["decoy_answers"])}
    res["decoy"] = rates(a_dec, dec_ids) if dec_ids else "no decoy passage"
    if dec_ids:
        res["decoy_verdict"] = verdict(res["decoy"], d["named"], d | {"min_verses": 1})
    for k in d["named"]:
        if k in res["real"] and res["real"][k]["asked"]:
            mine = res["real"][k]
            oth = Counter()
            for o, v in res["real"].items():
                if o != k:
                    oth.update({"yes": v.get("yes", 0), "asked": v.get("asked", 0)})
            res.setdefault("fisher_above_others", {})[k] = fisher_greater(
                mine.get("yes", 0), mine["asked"] - mine.get("yes", 0),
                oth["yes"], oth["asked"] - oth["yes"])  # fmt: skip
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["jobs", "check-jobs", "score"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "jobs":
        res = build(cfg)
        print(json.dumps({k: v for k, v in res.items() if k != "commentaries"}
                         | {"coverage": {k: [v["work_id"], v["luke12_verses_located"],
                                             v["real_questions"]]
                                         for k, v in res["commentaries"].items()}},
                         indent=1))  # fmt: skip
    elif a.cmd == "check-jobs":
        print(json.dumps(check_jobs(cfg), indent=1))
    else:
        res = score(cfg)
        res["config_sha256"] = config.sha256_of_config()
        out(FILES["result"]).write_text(json.dumps(res, indent=1) + "\n")
        print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
