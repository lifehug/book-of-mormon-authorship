"""BOM-134: anachronisms in genuine ancient texts, read the Book of Mormon's way.

A claim the owner met: "if the Book of Mormon were ancient, it would have zero anachronisms."
BOM-113's controls were all 1800s books set in antiquity; no genuine ancient text was read the
same way. Here genuine ancient texts in period English translation (the King James Genesis to
Kings, Whiston's Josephus *Antiquities* I-XI, Pope's Iliad and Odyssey, Beloe's Herodotus, Sale's
Koran, the Mesoamerican native texts of BOM-111/113), decoys presented as ancient but modern
(Macpherson's Ossian, *Chronicles of Eri*, Spalding's manuscript), *The Late War* (Bible style,
set in its own time) and the Book of Mormon are each cut into passages of ``passage_words`` words
and an equal seeded sample is read in two steps, **simulated judging by an AI model**
(``lab.judge``): (1) a model lists the concrete things in a passage; (2) a model codes each thing
against the text's OWN claimed setting (``lab.ancient_anachronisms.texts``): ATTESTED /
NOT_ATTESTED_THERE_THEN / CANNOT_TELL, and for an anachronism IN_THE_STORY or TRANSLATION_WORD.
Rates per 10,000 words per text, both kinds, with bootstrap intervals over passages.

The check comes first and gates the score: (a) 40 planted anachronisms found; (b) the textbook
cases caught (camels and Philistines with the patriarchs, Ur of the Chaldees, Dan at Gen 14:14,
KJV "steel" and "Easter" as translation words, Homer's iron); (c) a second model agrees on at
least 100 item codes; (d) BOM-113's 12-item reader check still passes. Card:
``data/private/lab/owner/2026-11-27-ancient-anachronisms/card.md``. Jobs and answers quote text
and stay in the card's folder; public files hold names, sizes, ids, short item names, codes and
counts.

Usage::

    python -m lab.ancient_anachronisms texts          # sizes and settings -> .../texts.json
    python -m lab.ancient_anachronisms jobs           # reader, check-list and main-list jobs
    python -m lab.ancient_anachronisms jobs2 --stage check   # coding + agreement jobs (check)
    python -m lab.ancient_anachronisms check          # the four checks -> .../check.json
    python -m lab.ancient_anachronisms jobs2 --stage main    # coding jobs from the main lists
    python -m lab.ancient_anachronisms score          # check, then rates -> .../result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter
from math import ceil
from pathlib import Path

from lab import anachronisms as a113
from lab import door
from lab.numbers import _file, bom_text, gutenberg
from lab.paths import FAST, LOGS, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "ancient_anachronisms"
CARD = NOTES / "owner" / "2026-11-27-ancient-anachronisms"
NAMES = FAST / "sources" / "names"
KJV = Path("data/kjv/kjv.jsonl")
CODES = ("ATTESTED", "NOT_ATTESTED_THERE_THEN", "CANNOT_TELL")
KINDS = ("IN_THE_STORY", "TRANSLATION_WORD")
ANACH = "NOT_ATTESTED_THERE_THEN"
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-134). "
FILES = {  # stage -> (jobs, answers) in the card folder
    "reader": ("jobs_reader.jsonl", "answers_reader.jsonl"),
    "check_list": ("jobs_check_list.jsonl", "answers_check_list.jsonl"),
    "check_code": ("jobs_check_code.jsonl", "answers_check_code.jsonl"),
    "agree": ("jobs_agree.jsonl", "answers_agree.jsonl"),
    "list": ("jobs_list.jsonl", "answers_list.jsonl"),
    "code": ("jobs_code.jsonl", "answers_code.jsonl"),
}


def settings(cfg: dict) -> dict:
    return cfg["lab"]["ancient_anachronisms"]


# ------------------------------------------------------------------------------ the texts


def clean(text: str) -> str:
    """Long s read as s, line-end hyphens joined; nothing else changed."""
    text = text.replace("ſ", "s")
    return re.sub(r"(\w)-[ \t]*\n\s*(\w)", r"\1\2", text)


def cut(text: str, keep: list | None) -> str:
    """Keep every segment from a ``start`` match to the next ``stop`` match (or the end)."""
    if not keep:
        return text
    start, stop = keep
    res, pos = [], 0
    while True:
        m = re.compile(start).search(text, pos)
        if not m:
            break
        e = re.compile(stop).search(text, m.end()) if stop else None
        end = e.start() if e else len(text)
        res.append(text[m.start() : end])
        if not e:
            break
        pos = e.end()
    return "\n".join(res)


def kjv_rows() -> list[dict]:
    raw = _file(KJV)
    return [] if raw is None else [json.loads(x) for x in raw.splitlines() if x.strip()]


def load_text(name: str, t: dict, cfg: dict) -> str | None:
    """A text's cleaned words as a string; None if not held (never scored as zero)."""
    k = t["kind"]
    if k == "kjv":
        rows = kjv_rows()
        got = "\n".join(r["text"] for r in rows if r["book"] in set(t["books"]))
        return got or None
    if k == "josephus":
        from lab.ntwording import josephus_parts

        raw = _file(NAMES / "josephus_antiquities_whiston.txt")
        split = cfg["lab"]["new_testament_wording"]["josephus_split"]
        return None if raw is None else clean(josephus_parts(raw, split)["old_testament_times"])
    if k == "names":
        raw = _file(NAMES / t["file"])
        return None if raw is None else clean(cut(gutenberg(raw), t.get("keep")))
    if k == "library":
        cat = door.catalog(set(t["ids"]))
        parts = []
        for i in t["ids"]:
            if i not in cat:
                return None
            try:
                parts.append(cut(door.text_of(cat[i]), t.get("keep")))
            except OSError:
                return None
        return clean("\n".join(parts))
    if k == "control":
        raw = a113.control_text(t["spec"])
        return None if raw is None else clean(raw)
    if k == "native":
        from lab import inventory as inv

        rows = inv.named_texts(cfg)
        got = [x for n, w, r, x in rows if w == "mesoamerica" and r == "native"]
        return None if not got or any(x is None for x in got) else clean("\n".join(got))
    if k == "bom":
        return bom_text(False)
    raise ValueError(f"unknown text kind {k!r}")


def all_texts(cfg: dict) -> dict[str, str | None]:
    return {n: load_text(n, t, cfg) for n, t in settings(cfg)["texts"].items()}


# ------------------------------------------------------------------------------ passages


def windows(text: str, size: int) -> list[str]:
    """Consecutive non-overlapping windows of ``size`` whitespace words (a short tail dropped)."""
    w = text.split()
    return [" ".join(w[i : i + size]) for i in range(0, len(w) - size + 1, size)]


def sample(name: str, text: str, cfg: dict) -> list[tuple[int, str]]:
    """The seeded equal sample of a text: (window index, passage), in text order."""
    s = settings(cfg)
    ws = windows(text, s["passage_words"])
    n = min(s["passages_per_text"], len(ws))
    pick = sorted(random.Random(f"{s['seed']}-{name}").sample(range(len(ws)), n))
    return [(i, ws[i]) for i in pick]


def plant(passage: str, sentence: str) -> str:
    """Insert ``sentence`` after the sentence end nearest the middle of the passage."""
    w = passage.split()
    mid = len(w) // 2
    ends = [i for i, x in enumerate(w) if x.endswith((".", ";", "?", "!", ":"))]
    at = min(ends, key=lambda i: abs(i - mid)) + 1 if ends else mid
    return " ".join(w[:at] + sentence.split() + w[at:])


def around(words: list[str], at: int, size: int) -> str:
    lo = max(0, min(at - size // 2, len(words) - size))
    return " ".join(words[lo : lo + size])


def kjv_passage(ref: str, size: int, rows: list[dict] | None = None) -> str | None:
    """``size`` words of the King James text centred on a verse ("GEN 12:16")."""
    rows = rows if rows is not None else kjv_rows()
    book, cv = ref.split()
    ch, v = map(int, cv.split(":"))
    sel = [r for r in rows if r["book"] == book]
    words, at = [], None
    for r in sel:
        if r["chapter"] == ch and r["verse"] == v:
            at = len(words)
        words += r["text"].split()
    return None if at is None else around(words, at, size)


def phrase_passage(text: str, phrase: str, size: int) -> str | None:
    words = text.split()
    p = phrase.split()
    for i in range(len(words) - len(p) + 1):
        if [x.strip(",.;:()").lower() for x in words[i : i + len(p)]] == [x.lower() for x in p]:
            return around(words, i, size)
    return None


# ------------------------------------------------------------------------------ prompts


def list_prompt(passage: str) -> str:
    return (
        SIMULATED + "Read this passage from a book and list the concrete things in it.\n\n"
        f"Passage: ...{passage}...\n\n"
        "List every concrete thing the passage's own text names: objects, animals, plants, "
        "foods, metals, materials, technologies, buildings, institutions, offices and titles, "
        "and places named. Each once, as a short name (one to four words) in the passage's own "
        "wording. Leave out abstract ideas, feelings, people's personal names, and anything in "
        "footnotes, editor's notes, page headings or front matter.\n"
        "Also say whether the passage is mainly the book's own text (yes) or mainly something "
        "else: footnotes, an editor's notes or essay, a preface, an index, a title page (no).\n"
        'Reply with one line of JSON only: {"own_text": "yes|no", "items": ["...", "..."]}'
    )


def code_prompt(setting: str, passage: str, items: list[str]) -> str:
    listed = "\n".join(f"{i + 1}. {x}" for i, x in enumerate(items))
    return (
        SIMULATED + "You are coding possible anachronisms. A book claims this setting (its "
        f"own region and period): {setting}.\n"
        "Judge each item against the place and time in which this passage's own events happen, "
        "within that setting.\n\n"
        f"Passage: ...{passage}...\n\nItems listed from the passage:\n{listed}\n\n"
        "For each item, as the passage uses it, give a code:\n"
        "ATTESTED = attested (by archaeology or contemporary record) in that place at that time;\n"
        "NOT_ATTESTED_THERE_THEN = not attested in that place at that time (an anachronism);\n"
        "CANNOT_TELL = the evidence does not decide, or the item is not a thing that could be "
        "attested.\n"
        "For NOT_ATTESTED_THERE_THEN also give the kind: IN_THE_STORY = the thing itself is in "
        "the narrative as the text stands; TRANSLATION_WORD = the English is a translator's word "
        "for an original-language word that is known (an extant original) and meant something "
        "period-correct (for example King James 'steel' for a word meaning bronze). Where no "
        "original-language text is extant, use IN_THE_STORY. For other codes the kind is null.\n"
        'Reply with one line of JSON only: {"codes": [{"n": 1, "code": "...", "kind": '
        '"IN_THE_STORY|TRANSLATION_WORD|null", "basis": "a few words"}, ...]} with one entry for '
        "every item, in order."
    )


# ------------------------------------------------------------------------------ parsing


def _json(reply: str | None):
    s = (reply or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b < a:
        return None
    try:
        r = json.loads(s[a : b + 1])
    except json.JSONDecodeError:
        return None
    return r if isinstance(r, dict) else None


def parse_list(reply: str | None) -> dict | None:
    """{"own_text": bool, "items": [unique short names]} or None if unreadable."""
    r = _json(reply)
    if r is None:
        return None
    own = str(r.get("own_text", "")).strip().lower()
    items = r.get("items")
    if own not in ("yes", "no") or not isinstance(items, list):
        return None
    seen, keep = set(), []
    for x in items:
        if not isinstance(x, str):
            return None
        k = " ".join(x.split())
        if k and k.lower() not in seen:
            seen.add(k.lower())
            keep.append(k)
    return {"own_text": own == "yes", "items": keep}


def parse_code(reply: str | None, n: int) -> list[dict] | None:
    """One {"code", "kind"} per item, in order; None unless all ``n`` are readable."""
    r = _json(reply)
    if r is None or not isinstance(r.get("codes"), list):
        return None
    got: dict[int, dict] = {}
    for e in r["codes"]:
        if not isinstance(e, dict):
            return None
        try:
            i = int(e.get("n"))
        except (TypeError, ValueError):
            return None
        code = str(e.get("code", "")).strip().upper()
        kind = e.get("kind")
        kind = None if kind in (None, "", "null", "None") else str(kind).strip().upper()
        if code not in CODES:
            return None
        if code == ANACH and kind not in KINDS:
            return None
        got[i] = {"code": code, "kind": kind if code == ANACH else None}
    if sorted(got) != list(range(1, n + 1)):
        return None
    return [got[i] for i in range(1, n + 1)]


def _load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def read_stage(stage: str, parse) -> dict:
    """Answers of one stage by id (parsed), with open and unreadable ids apart. An unreadable
    reply is logged with its raw text and never counted; ``parse(reply, job)`` reads one."""
    jp, ap = (CARD / f for f in FILES[stage])
    jobs = {j["id"]: j for j in _load(jp)} if jp.exists() else {}
    got: dict[str, object] = {}
    bad: dict[str, str] = {}
    if ap.exists():
        for r in _load(ap):
            if r["id"] not in jobs:
                continue
            p = parse(r.get("reply"), jobs[r["id"]])
            if p is None:
                bad[r["id"]] = r.get("reply")
            else:
                got[r["id"]] = p
    unread = sorted(set(bad) - set(got))
    if unread:
        out(LOGS / f"ancient_anachronisms_unparsed_{stage}.jsonl").write_text(
            "".join(
                json.dumps({"id": i, "reply": bad[i]}, ensure_ascii=False) + "\n" for i in unread
            )  # fmt: skip
        )
    left = [i for i in jobs if i not in got and i not in bad]
    return {"jobs": jobs, "answers": got, "open": left, "unreadable": unread}


def state(r: dict) -> dict:
    return {"jobs": len(r["jobs"]), "answered": len(r["answers"]), "open": len(r["open"]),
            "unreadable": len(r["unreadable"])}  # fmt: skip


# ------------------------------------------------------------------------------ jobs


def _write(stage: str, jobs: list[dict]) -> dict:
    path = out(CARD / FILES[stage][0])
    path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in jobs))
    return {"path": str(path), "questions": len(jobs)}


def setting_of(cfg: dict, name: str) -> str:
    return settings(cfg)["texts"][name]["setting"]


def planted_jobs(cfg: dict, samples: dict[str, list[tuple[int, str]]]) -> list[dict]:
    """Check (a): one planted sentence in each of ``per_kind`` x kinds seeded genuine passages."""
    s = settings(cfg)
    pool = [(n, i, p) for n, t in s["texts"].items() if t["group"] == "genuine"
            for i, p in samples.get(n, [])]  # fmt: skip
    kinds = list(s["planted"]["kinds"])
    k = s["planted"]["per_kind"]
    pick = random.Random(f"{s['seed']}-planted").sample(pool, k * len(kinds))
    res = []
    for j, (n, i, p) in enumerate(pick):
        kind = kinds[j // k]
        res.append({"id": f"plant|{kind}|{n}|{i}", "text": n,
                    "passage": plant(p, s["planted"]["kinds"][kind]["sentence"])})  # fmt: skip
    return res


def textbook_jobs(cfg: dict, texts: dict[str, str | None]) -> tuple[list[dict], list[str]]:
    """Check (b): a passage around each textbook case; (jobs, passages not found)."""
    s = settings(cfg)
    size = s["passage_words"]
    rows = kjv_rows()
    res, missing = [], []
    for case, c in s["textbook"].items():
        for where in c["passages"]:
            src, _, ref = where.partition(":")
            if src == "kjv":
                p = kjv_passage(ref, size, rows)
            else:
                t = texts.get(src)
                p = None if t is None else phrase_passage(t, ref, size)
            if p is None:
                missing.append(where)
                continue
            setting = c.get("setting", {}).get(ref) or setting_of(cfg, c["text"])
            res.append({"id": f"case|{case}|{ref}", "text": c.get("text"), "passage": p,
                        "setting": setting})  # fmt: skip
    return res, missing


def reader_jobs() -> list[dict]:
    """Check (d): BOM-113's 12-item reader check, the same prompts (from its card folder)."""
    path = a113.PRIVATE / "jobs_known.jsonl"
    return [{"id": j["id"], "prompt": j["prompt"]} for j in _load(path)]


def make_jobs(cfg: dict) -> dict:
    texts = all_texts(cfg)
    missing = [n for n, t in texts.items() if t is None]
    if missing:
        raise SystemExit(f"texts not held: {missing}; nothing written")
    samples = {n: sample(n, t, cfg) for n, t in texts.items()}
    planted = planted_jobs(cfg, samples)
    cases, not_found = textbook_jobs(cfg, texts)
    if not_found:
        raise SystemExit(f"textbook passages not found: {not_found}; nothing written")
    check = [{**{k: v for k, v in j.items() if k != "passage"},
              "prompt": list_prompt(j["passage"]), "passage": j["passage"]}
             for j in planted + cases]  # fmt: skip
    main = [{"id": f"main|{n}|{i}", "text": n, "passage": p, "prompt": list_prompt(p)}
            for n, ps in samples.items() for i, p in ps]  # fmt: skip
    return {"reader": _write("reader", reader_jobs()), "check_list": _write("check_list", check),
            "list": _write("list", main),
            "label": "simulated judging by an AI model; prepared, not run"}  # fmt: skip


def code_jobs(cfg: dict, stage: str) -> dict:
    """Step 2 from step 1's answers: one coding question per passage that is the book's own text
    and lists at least one item. Unreadable or open step-1 answers are reported, not written."""
    lst = "check_list" if stage == "check" else "list"
    r = read_stage(lst, lambda reply, job: parse_list(reply))
    jobs = []
    skipped = Counter()
    for i, job in r["jobs"].items():
        got = r["answers"].get(i)
        if got is None:
            continue
        if not got["own_text"]:
            skipped["not_own_text"] += 1
            continue
        if not got["items"]:
            skipped["no_items"] += 1
            continue
        setting = job.get("setting") or setting_of(cfg, job["text"])
        jobs.append({"id": i, "text": job.get("text"), "items": got["items"],
                     "prompt": code_prompt(setting, job["passage"], got["items"])})  # fmt: skip
    res = {"step1": state(r), "skipped": dict(skipped),
           "code": _write("check_code" if stage == "check" else "code", jobs)}  # fmt: skip
    if stage == "check":
        s = settings(cfg)
        order = sorted(jobs, key=lambda j: j["id"])
        random.Random(f"{s['seed']}-agree").shuffle(order)
        pick, n = [], 0
        for j in order:
            if n >= s["agreement_items"]:
                break
            pick.append(j)
            n += len(j["items"])
        res["agree"] = {**_write("agree", pick), "items": n, "model": s["second_coder_model"]}
    return res


# ------------------------------------------------------------------------------ scoring


def kappa(a: list[str], b: list[str]) -> float | None:
    """Cohen's kappa of two raters' labels over the same items."""
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def _matches(item: str, words: list[str], exact: bool = False) -> bool:
    low = item.lower()
    if exact:
        return any(w in re.findall(r"[a-z]+", low) for w in words)
    return any(w in low for w in words)


def found(items: list[str], codes: list[dict], words: list[str], kind: str | None = None,
          exact: bool = False) -> bool:  # fmt: skip
    """An item matching ``words`` coded as an anachronism (of ``kind`` when given)."""
    return any(_matches(it, words, exact) and c["code"] == ANACH and (kind is None
               or c["kind"] == kind) for it, c in zip(items, codes, strict=True))  # fmt: skip


def code_parser(reply, job):
    return parse_code(reply, len(job["items"]))


def run_check(cfg: dict) -> dict:
    """The four checks from the answers so far; refused while any check answer is open."""
    s = settings(cfg)
    stages = {"reader": read_stage("reader", lambda reply, job: a113.parse_judged(reply)),
              "check_list": read_stage("check_list", lambda reply, job: parse_list(reply)),
              "check_code": read_stage("check_code", code_parser),
              "agree": read_stage("agree", code_parser)}  # fmt: skip
    st = {k: state(v) for k, v in stages.items()}
    if not stages["check_code"]["jobs"] or not stages["agree"]["jobs"]:
        return {"refused": "run jobs2 --stage check first", "answers": st}
    if any(v["open"] or v["unreadable"] for v in stages.values()):
        return {"refused": "check answers still open or unreadable; nothing scored", "answers": st}
    kn = stages["reader"]["answers"]
    hit = sum(kn.get(f"known|{k}", {}).get("code") == v for k, v in a113.KNOWN_JUDGE.items())
    reader = {"matched": hit, "of": len(a113.KNOWN_JUDGE), "bar": s["reader_bar"],
              "passed": hit / len(a113.KNOWN_JUDGE) >= s["reader_bar"]}  # fmt: skip
    lists, codes = stages["check_list"]["answers"], stages["check_code"]["answers"]
    cjobs = stages["check_code"]["jobs"]

    def got(i: str) -> tuple[list[str], list[dict]]:
        if i not in codes:
            return [], []
        return cjobs[i]["items"], codes[i]

    pk = s["planted"]["kinds"]
    plants = {}
    for i in stages["check_list"]["jobs"]:
        if i.startswith("plant|"):
            kind = i.split("|")[1]
            items, cs = got(i)
            plants[i] = {"kind": kind, "listed": any(_matches(x, pk[kind]["match"]) for x in
                                                     lists[i]["items"]),
                         "found": found(items, cs, pk[kind]["match"])}  # fmt: skip
    share = sum(p["found"] for p in plants.values()) / len(plants) if plants else 0.0
    planted = {"plants": len(plants), "found": sum(p["found"] for p in plants.values()),
               "listed": sum(p["listed"] for p in plants.values()), "share": round(share, 3),
               "bar": s["bar_planted"], "passed": bool(plants) and share >= s["bar_planted"],
               "by_kind": {k: [sum(p["found"] for p in plants.values() if p["kind"] == k),
                               sum(p["kind"] == k for p in plants.values())] for k in pk},
               "missed": sorted(i for i, p in plants.items() if not p["found"])}  # fmt: skip
    cases = {}
    for case, c in s["textbook"].items():
        per = {}
        for i in stages["check_list"]["jobs"]:
            if i.startswith(f"case|{case}|"):
                items, cs = got(i)
                ex = c.get("exact", False)
                cap = s["max_items_public"]
                pairs = [(x, y) for x, y in zip(items, cs, strict=True)
                         if _matches(x, c["match"], ex)]  # fmt: skip
                hits = [{"item": " ".join(x.lower().split()[:cap]), "code": y["code"],
                         "kind": y["kind"]} for x, y in pairs]  # fmt: skip
                per[i.split("|", 2)[2]] = {
                    "caught": found(items, cs, c["match"], c.get("kind"), c.get("exact", False)),
                    "matching_items": hits,
                }
        cases[case] = {"caught": any(v["caught"] for v in per.values()),
                       "kind_wanted": c.get("kind"), "passages": per}  # fmt: skip
    caught = sum(v["caught"] for v in cases.values())
    textbook = {"caught": caught, "of": len(cases), "bar": s["bar_textbook"],
                "passed": caught >= s["bar_textbook"], "cases": cases}  # fmt: skip
    a, b = [], []
    for i, cs in stages["agree"]["answers"].items():
        if i in codes:
            a += [c["code"] for c in codes[i]]
            b += [c["code"] for c in cs]
    k = kappa(a, b)
    agree = {"items": len(a), "need": s["agreement_items"], "kappa": None if k is None else
             round(k, 3), "raw_agreement": round(sum(x == y for x, y in zip(a, b, strict=True))
                                                 / len(a), 3) if a else None,
             "bar": s["kappa_bar"], "first": s["code_model"], "second": s["second_coder_model"],
             "passed": len(a) >= s["agreement_items"] and k is not None
             and k >= s["kappa_bar"]}  # fmt: skip
    passed = reader["passed"] and planted["passed"] and textbook["passed"] and agree["passed"]
    return {"label": "simulated judging by an AI model", "answers": st, "passed": passed,
            "a_planted": planted, "b_textbook": textbook, "c_agreement": agree,
            "d_reader": reader}  # fmt: skip


def boot(per: list[tuple[int, int]], words: int, n: int, seed: str) -> list[float] | None:
    """95% interval of sum(k)/sum(words) per 10,000 words, resampling passages."""
    if not per:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        draw = [per[rng.randrange(len(per))] for _ in per]
        vals.append(sum(k for k, _ in draw) * 1e4 / sum(w for _, w in draw))
    vals.sort()
    return [round(vals[int(0.025 * n)], 2), round(vals[min(n - 1, int(0.975 * n))], 2)]


def score(cfg: dict) -> dict:
    s = settings(cfg)
    chk = run_check(cfg)
    if "refused" in chk or not chk["passed"]:
        return {"refused": chk.get("refused", "the check missed: the texts are not scored"),
                "check": chk}  # fmt: skip
    lst = read_stage("list", lambda reply, job: parse_list(reply))
    code = read_stage("code", code_parser)
    st = {"list": state(lst), "code": state(code)}
    if not code["jobs"]:
        return {"refused": "run jobs2 --stage main first", "answers": st}
    if any(r["open"] or r["unreadable"] for r in (lst, code)):
        return {"refused": "answers still open or unreadable; nothing scored", "answers": st}
    need = {i for i, x in lst["answers"].items() if x["own_text"] and x["items"]}
    if need - set(code["jobs"]):
        return {"refused": "coding jobs are older than the list answers: rerun jobs2 --stage "
                "main", "answers": st}  # fmt: skip
    size, cap = s["passage_words"], s["max_items_public"]
    per_text: dict[str, dict] = {}
    for i, job in lst["jobs"].items():
        name = job["text"]
        row = per_text.setdefault(name, {"passages": 0, "not_own_text": 0, "rows": [],
                                         "items": Counter(), "codes": Counter()})  # fmt: skip
        row["passages"] += 1
        got = lst["answers"][i]
        if not got["own_text"]:
            row["not_own_text"] += 1
            continue
        items = code["jobs"][i]["items"] if i in code["jobs"] else []
        cs = code["answers"].get(i, [])
        k = {"story": 0, "translation": 0}
        for it, c in zip(items, cs, strict=True):
            row["codes"][c["code"]] += 1
            if c["code"] == ANACH:
                k["story" if c["kind"] == "IN_THE_STORY" else "translation"] += 1
                row["items"][(" ".join(it.lower().split()[:cap]), c["kind"])] += 1
        row["rows"].append((k["story"], k["translation"], len(items)))
    res = {}
    for name, row in per_text.items():
        n = len(row["rows"])
        words = n * size
        st_ = [(x[0], size) for x in row["rows"]]
        tr_ = [(x[1], size) for x in row["rows"]]
        al_ = [(x[0] + x[1], size) for x in row["rows"]]
        story, trans = sum(x[0] for x in row["rows"]), sum(x[1] for x in row["rows"])

        def r10(k: int, words: int = words) -> float | None:
            return round(k * 1e4 / words, 2) if words else None

        res[name] = {
            "group": s["texts"][name]["group"], "setting": s["texts"][name]["setting"],
            "passages_sampled": row["passages"], "passages_not_own_text": row["not_own_text"],
            "passages_scored": n, "words_scored": words,
            "items_coded": sum(x[2] for x in row["rows"]), "codes": dict(row["codes"]),
            "anachronisms": {"in_the_story": story, "translation_word": trans,
                             "all": story + trans},
            "per_10k": {"in_the_story": r10(story), "translation_word": r10(trans),
                        "all": r10(story + trans)},
            "ci95_per_10k": {"in_the_story": boot(st_, words, s["bootstrap"], f"{name}-s"),
                             "translation_word": boot(tr_, words, s["bootstrap"], f"{name}-t"),
                             "all": boot(al_, words, s["bootstrap"], f"{name}-a")},
            "passages_with_any": sum(1 for x in row["rows"] if x[0] + x[1]),
            "top_items": [{"item": it, "kind": kd, "n": c} for (it, kd), c in
                          row["items"].most_common(15)],
        }  # fmt: skip
    return {"label": "simulated judging by an AI model (" + s["list_model"] + " lists, "
            + s["code_model"] + " codes)", "answers": st, "check": chk,
            "texts": res, "comparison": compare(res, s), "bom113": bom113()}  # fmt: skip


def compare(res: dict, s: dict) -> dict:
    """The book's place among genuine texts and decoys, and whether the decoys stand apart."""

    def med(xs: list[float]) -> float | None:
        return (xs[(len(xs) - 1) // 2] + xs[len(xs) // 2]) / 2 if xs else None

    def rate(n: str, key: str = "all") -> float:
        return res[n]["per_10k"][key] or 0.0

    gen = [n for n in res if res[n]["group"] == "genuine"]
    dec = [n for n in s["pseudo_ancient"] if n in res]
    out_ = {}
    for key in ("all", "in_the_story"):
        g = sorted(rate(n, key) for n in gen)
        d = sorted(rate(n, key) for n in dec)
        book = rate("book_of_mormon", key) if "book_of_mormon" in res else None
        verdict = ("not attempted" if not g or not d else
                   "the decoys stand apart: every decoy above every genuine text" if d[0] > g[-1]
                   else "partly: the decoys' median is above the genuine texts' median"
                   if med(d) > med(g) else "the measure cannot separate the decoys from the "
                   "genuine texts")  # fmt: skip
        out_[key] = {
            "genuine": {n: rate(n, key) for n in gen}, "decoys": {n: rate(n, key) for n in dec},
            "genuine_range": [g[0], g[-1]] if g else None, "genuine_median": med(g),
            "decoy_median": med(d), "book": book,
            "book_above_genuine": None if book is None else sum(book > x for x in g),
            "book_above_decoys": None if book is None else sum(book > x for x in d),
            "genuine_with_zero": sum(x == 0 for x in g), "decoys_vs_genuine": verdict,
        }  # fmt: skip
    return out_


def bom113() -> dict:
    """BOM-113's item-list numbers, beside (read from its judged result if present)."""
    p = a113.JUDGED
    if not p.exists():
        return {"not_attempted": f"{p} not present"}
    j = json.loads(p.read_text())
    b = j.get("book_items_compared", {})
    return {"source": str(p), "countable_items": b.get("n"), "strict_share": b.get("strict_share"),
            "loose_share": b.get("loose_share"),
            "note": "share of Roper's countable things attested in Mesoamerica in period "
                    "(strict) or anywhere in the ancient world (loose); a different unit from "
                    "this test's rates per 10,000 words"}  # fmt: skip


# ------------------------------------------------------------------------------ commands


def texts_report(cfg: dict) -> dict:
    s = settings(cfg)
    res = {}
    for n, t in all_texts(cfg).items():
        spec = s["texts"][n]
        words = None if t is None else len(t.split())
        win = None if words is None else words // s["passage_words"]
        res[n] = {"group": spec["group"], "kind": spec["kind"], "setting": spec["setting"],
                  "source": spec.get("ids") or spec.get("file") or spec.get("spec")
                  or spec.get("books") or spec["kind"],
                  "words": words, "windows": win,
                  "sampled": None if win is None else min(s["passages_per_text"], win)}  # fmt: skip
    return res


def estimate(cfg: dict, n_texts: int) -> dict:
    """Calls before any answer exists: step 2 at most one per step-1 passage."""
    s = settings(cfg)
    k = len(s["planted"]["kinds"]) * s["planted"]["per_kind"]
    cases = sum(len(c["passages"]) for c in s["textbook"].values())
    main = n_texts * s["passages_per_text"]
    agree = ceil(s["agreement_items"] / 8)  # about 8 or more items a passage
    total = 12 + 2 * (k + cases) + agree + 2 * main
    return {
        "reader": 12,
        "check_list": k + cases,
        "check_code_at_most": k + cases,
        "agree_about": agree,
        "list": main,
        "code_at_most": main,
        "total_at_most": total,
    }


def _stamp(res: dict) -> dict:
    return {**res, **config.stamp()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["texts", "jobs", "jobs2", "check", "score"])
    ap.add_argument("--stage", choices=["check", "main"], default="main")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "texts":
        rep = texts_report(cfg)
        body = {"texts": rep, "calls": estimate(cfg, len(rep))}
        out(OUT / "texts.json").write_text(json.dumps(_stamp(body), indent=1) + "\n")
        print(json.dumps(body, indent=1))
        return 0
    if a.cmd == "jobs":
        print(json.dumps(make_jobs(cfg), indent=1))
        return 0
    if a.cmd == "jobs2":
        res = code_jobs(cfg, a.stage)
        print(json.dumps(res, indent=1))
        return 0
    if a.cmd == "check":
        res = run_check(cfg)
        if "refused" in res:
            print("refused:", res["refused"], json.dumps(res["answers"]))
            return 1
        out(OUT / "check.json").write_text(json.dumps(_stamp(res), indent=1) + "\n")
        print(json.dumps({k: v.get("passed") for k, v in res.items() if isinstance(v, dict)
                          and "passed" in v}), "passed" if res["passed"] else "MISSED")  # fmt: skip
        return 0 if res["passed"] else 1
    res = score(cfg)
    if "refused" in res:
        print("refused:", res["refused"])
        return 1
    out(OUT / "result.json").write_text(json.dumps(_stamp(res), indent=1) + "\n")
    print("wrote", OUT / "result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
