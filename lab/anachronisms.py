"""BOM-113: Roper's anachronism tally, with a control (rule-based counts; judging prepared only).

Roper (2025, *Interpreter* 65) counts 226 things critics called anachronisms in the Book of
Mormon and how many are now "confirmed". Two item lists run through the same counting: **Roper's
own**, keyed from his held chapters by ``lab.anachronisms_roper`` (``items.json``), and the
**stand-in** used before his chapters were held (``items_standin.json``): the Wikipedia article
"Anachronisms in the Book of Mormon" (fetched 2026-11-20), Coe 1973 as summarised in
``docs/research/2026-11-20-the-books-setting.md``, and a short supplement **written from memory
by the AI**. Each item names a "thing", the word forms counted for it; several items may share one.

Every countable item is counted per 10,000 words in the Book of Mormon (all text, and without the
long Bible-quotation chapters), in control books of known modern origin set in antiquity
(``lab.anachronisms.controls``), and in the BOM-111 worlds (``lab.inventory.named_texts`` and its
background sample), reading text with BOM-111's ``words_of``. A known-answer check runs first
(planted mentions; horse and chariot in the King James Old Testament; maize in the Mesoamerican
native texts; no New World probe in the King James Bible); if it misses, nothing else is reported.
The cross-table of Roper's status by Bible item is coded but not attempted until his statuses are
keyed. The judging half (recode by place and period; control items under the loose standard) is
written as jobs for ``lab.judge``, **simulated judging by an AI model**, and not run here.
Card: ``data/private/lab/owner/2026-11-21-anachronism-tally/card.md``. The result holds item
names, labels and counts, no passages.

Usage::

    python -m lab.anachronisms items   # -> .../items.json (Roper) and .../items_standin.json
    python -m lab.anachronisms check [--list standin]   # known-answer check -> known_answer*.json
    python -m lab.anachronisms run [--list standin]     # check, then counts -> result*.json
    python -m lab.anachronisms jobs [--list standin]    # judging questions (private; not run)
    python -m lab.anachronisms judged  # score the judge's answers -> .../judged.json

``judged`` reads ``answers_known``, ``answers_bom`` and ``answers_control`` (``lab.judge``
output beside the jobs) and refuses while any answer is open or unreadable (raw text logged to
``logs/lab/``) or the known-answer subset is below its bar. It reports Roper's items recoded by
place and period, the strict standard against the loose one (``lab.anachronisms.judged``), the
control books' things under the same codes, and each control against the book.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
from collections import Counter
from pathlib import Path
from statistics import median

from lab import anachronisms_roper as roper
from lab import inventory as inv
from lab.numbers import CAND, _file, _library, bom_text
from lab.paths import FAST, LOGS, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "setting" / "anachronisms"
CACHE = FAST / "anachronisms"
PRIVATE = NOTES / "owner" / "2026-11-21-anachronism-tally"
SRC = FAST / "sources"
CATEGORIES = ("animal", "plant", "metal", "technology", "textile", "writing", "warfare",
              "custom", "name", "other")  # fmt: skip
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-113). "

# ------------------------------------------------------------------------------ the items

WP = "wikipedia: Anachronisms in the Book of Mormon (fetched 2026-11-20)"
WPQ = "wikipedia: opening quotation's list of out-of-place things (fetched 2026-11-20)"
COE = "Coe 1973, as summarised in docs/research/2026-11-20-the-books-setting.md (Coe not held)"
MEM = "memory: written by the AI from memory, not from a held source"

# (id, label, category, forms or None if not countable, plural, guard, [(source, section)])
_RAW = [
    ("horse", "horses", "animal", ["horse"], True, False,
     [(WP, "Horses"), (WPQ, ""), (COE, "")]),
    ("elephant", "elephants", "animal", ["elephant"], True, False, [(WP, "Elephants"), (WPQ, "")]),
    ("cattle", "cattle and cows", "animal", ["cattle", "cow", "kine"], True, False,
     [(WP, "Cattle and cows"), (WPQ, ""), (COE, "")]),
    ("goat", "goats", "animal", ["goat"], True, False, [(WP, "Goats"), (WPQ, "")]),
    ("swine", "swine", "animal", ["swine"], False, False, [(WP, "Swine"), (WPQ, "")]),
    ("ass", "asses", "animal", ["ass", "asses"], False, False, [(WPQ, "")]),
    ("barley", "barley", "plant", ["barley"], False, False, [(WP, "Barley and wheat"), (COE, "")]),
    ("wheat", "wheat", "plant", ["wheat"], False, False,
     [(WP, "Barley and wheat"), (WPQ, ""), (COE, "")]),
    ("silk", "silk", "textile", ["silk", "silks"], False, False, [(WPQ, "")]),
    ("chariot", "chariots", "technology", ["chariot"], True, False,
     [(WP, "Chariots"), (WPQ, ""), (COE, "")]),
    ("compass", "compass", "technology", ["compass"], True, True, [(WP, "Compass")]),
    ("window", "windows", "technology", ["window"], True, False, [(WP, "Windows")]),
    ("dross", "dross", "metal", ["dross"], False, False, [(WP, "Uses of metal: Dross")]),
    ("steel", "steel", "metal", ["steel"], False, False,
     [(WP, "Uses of metal: Steel and iron"), (WPQ, "")]),
    ("iron", "iron", "metal", ["iron"], False, False,
     [(WP, "Uses of metal: Steel and iron"), (WPQ, "")]),
    ("brass", "brass", "metal", ["brass"], False, False, [(WPQ, "")]),
    ("sword", "metal swords", "warfare", ["sword"], True, False,
     [(WP, "Uses of metal: Metal swords")]),
    ("cimeter", "cimeters", "warfare", ["cimeter", "scimitar", "scimetar"], True, False,
     [(WP, "Uses of metal: Cimeters")]),
    ("metallurgy", "metallurgy", "metal", None, False, False, [(COE, "")]),
    ("precious_metal_exchange", "system of exchange using precious metals", "other", None, False,
     False, [(WP, "Uses of metal: System of exchange using precious metals")]),
    ("reformed_egyptian", "reformed Egyptian", "writing", ["reformed egyptian"], False, False,
     [(WP, "Knowledge of a modified Hebrew and reformed Egyptian languages")]),
    ("christ", "the title Christ", "name", ["christ"], False, False,
     [(WP, "Christ and Messiah")]),
    ("messiah", "the title Messiah", "name", ["messiah", "messias"], False, False,
     [(WP, "Christ and Messiah")]),
    ("greek_names", "Greek or Hellenised names", "name",
     ["timothy", "antipas", "archeantus", "esrom", "ezias", "jonas", "judea", "lachoneus",
      "zenos"], False, False, [(WP, "Greek names")]),
    ("church", "the word church", "other", ["church"], True, False,
     [(WP, "Church and synagogue")]),
    ("synagogue", "synagogues", "other", ["synagogue"], True, False,
     [(WP, "Church and synagogue")]),
    ("isabel", "the name Isabel", "name", ["isabel"], False, False, [(WP, "The name Isabel")]),
    ("ships_of_tarshish", "ships of Tarshish", "other", ["ships of tarshish"], False, False,
     [(WP, "All the ships of the sea, and upon all the ships of Tarshish")]),
    ("satyr", "satyrs", "other", ["satyr"], True, False, [(WP, "Satyr")]),
    ("baptism", "baptism", "custom",
     ["baptism", "baptisms", "baptize", "baptized", "baptizing", "baptizeth", "baptise",
      "baptised"], False, False, [(WP, "Baptism")]),
    ("five_books_of_moses", "the five books of Moses", "writing", ["five books of moses"], False,
     False, [(WP, "Books of Moses")]),
    ("deutero_isaiah", "quoting Isaiah 48-54", "other", None, False, False,
     [(WP, "Quoting Isaiah")]),
    ("dating_600_years", "600 years from Lehi to Christ", "other", None, False, False,
     [(WP, "Dating of known historical events")]),
    ("new_testament_phrases", "New Testament phrasing", "other", None, False, False,
     [(WP, "New Testament anachronisms")]),
    ("anti_universalism", "anti-Universalist rhetoric", "custom", None, False, False,
     [(WP, "Anti-Universalist rhetoric")]),
    ("satisfaction_atonement", "satisfaction theory of atonement", "custom", None, False, False,
     [(WP, "Satisfaction theory of atonement")]),
    ("cement", "cement", "other", ["cement"], True, False, [(MEM, "")]),
    ("linen", "linen", "textile", ["linen"], True, False, [(MEM, "")]),
    ("sheep", "sheep", "animal", ["sheep"], False, False, [(MEM, "")]),
    ("ox", "oxen", "animal", ["ox", "oxen"], False, False, [(MEM, "")]),
    ("bee", "honey bees", "animal", ["bee"], True, False, [(MEM, "")]),
    ("wheel", "wheels", "technology", ["wheel"], True, False, [(MEM, "")]),
]  # fmt: skip

HELD = {
    "roper_2025": {
        "citation": "Matthew Roper, 'Anachronisms: Accidental Evidence', Interpreter: A Journal "
        "of Latter-day Saint Faith and Scholarship 65 (2025)",
        "address": "https://cdn.interpreterfoundation.org/jnlpdf/roper-v65-2025-1-8-PDF.pdf",
        "held": False,
        "missing": "the whole paper: the 226-item table, each item's year raised, critic, status "
        "at 1844 / 1965 / 2024, the attestation cited, page numbers",
        "second_hand_only": {
            "source": "docs/research/2026-11-20-the-books-setting.md (an AI agent opened the "
            "introduction and chapter 9; not checked by a person)",
            "confirmed_partial_unconfirmed_of_total": {
                "1844": [7, 2, 93, 102], "1965": [36, 10, 122, 168], "2024": [174, 31, 21, 226]},
            "standard_as_read_by_the_agent": "confirmed = attested anywhere in the ancient record",
        },
    },
    "roper_2012_held": "roper2012_stylometry_short_history.pdf is held but has no anachronism list",
}  # fmt: skip


def keyed_items() -> list[dict]:
    """The stand-in list (items_standin.json): no Roper fields (keyed before his chapters were
    held)."""
    rows = []
    for iid, label, cat, forms, plural, guard, srcs in _RAW:
        assert cat in CATEGORIES, cat
        rows.append({
            "id": iid, "label": label, "category": cat, "countable": forms is not None,
            "thing": iid if forms is not None else None,
            "forms": forms or [], "plural": plural, "guard": guard,
            "sources": [{"source": s, "section": sec} for s, sec in srcs],
            "from_memory": all(s == MEM for s, _ in srcs),
            "year_first_raised": None, "raised_by": None, "roper_status": None,
            "roper_confirmation_kind": None, "roper_page": None,
        })  # fmt: skip
    return rows


def standin_things(items: list[dict]) -> list[dict]:
    return [{"id": it["id"], "forms": it["forms"], "plural": it["plural"], "guard": it["guard"]}
            for it in items if it["countable"]]  # fmt: skip


def roper_things() -> list[dict]:
    return [{"id": k, "forms": f, "plural": p, "guard": g}
            for k, (f, p, g) in roper.THINGS.items()]  # fmt: skip


def compile_forms(items: list[dict]) -> dict[str, dict]:
    """Per counted thing: the set of single-word forms and of phrases (tuples of words)."""
    res: dict[str, dict] = {}
    seen: dict[str, str] = {}
    for it in items:
        if not it.get("forms"):
            continue
        single, phrases = set(), set()
        for f in it["forms"]:
            words = f.lower().split()
            variants = inv._plurals(words[-1]) if it["plural"] else {words[-1]}
            for v in variants:
                full = tuple(words[:-1] + [v])
                key = " ".join(full)
                if key in seen and seen[key] != it["id"]:
                    raise ValueError(f"form {key!r} claimed by {seen[key]} and {it['id']}")
                seen[key] = it["id"]
                (phrases if len(full) > 1 else single).add(full if len(full) > 1 else full[0])
        res[it["id"]] = {"single": single, "phrases": phrases, "guard": it["guard"]}
    return res


def items_sha(forms: dict[str, dict]) -> str:
    body = {k: [sorted(v["single"]), sorted(" ".join(p) for p in v["phrases"]), v["guard"]]
            for k, v in forms.items()}  # fmt: skip
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


# ------------------------------------------------------------------------------ counting


def count_words(words: list[str], forms: dict[str, dict]) -> dict[str, int]:
    """Mentions per item in a word list (case ignored; a guarded item needs a determiner)."""
    low = [w.lower() for w in words]
    uni = Counter(low)
    res = {}
    first: dict[str, list[tuple[str, tuple]]] = {}
    for iid, f in forms.items():
        if f["guard"]:
            n = sum(
                1 for i, w in enumerate(low) if w in f["single"] and i and low[i - 1] in inv.DET
            )
        else:
            n = sum(uni[w] for w in f["single"])
        res[iid] = n
        for p in f["phrases"]:
            first.setdefault(p[0], []).append((iid, p))
    if first:
        for i, w in enumerate(low):
            for iid, p in first.get(w, ()):
                if tuple(low[i : i + len(p)]) == p:
                    res[iid] += 1
    return {k: v for k, v in res.items() if v}


def counted(name: str, text: str | None, forms: dict[str, dict]) -> dict | None:
    """Counts for one text (cached by item forms and text); None if the text is not held."""
    if text is None:
        return None
    key = hashlib.sha256(
        (items_sha(forms) + "long-s-v1" + str(len(inv.VOCAB))
         + hashlib.sha256(text.encode()).hexdigest()).encode()).hexdigest()[:20]  # fmt: skip
    path = (
        CACHE / f"{''.join(c if c.isalnum() or c in '-_.' else '_' for c in name)[:80]}-{key}.json"
    )
    if path.exists():
        return json.loads(path.read_text())
    words = inv.words_of(text)
    res = {"words": len(words), "counts": count_words(words, forms)}
    out(path).write_text(json.dumps(res))
    return res


def rate(c: dict, iid: str) -> float:
    return c["counts"].get(iid, 0) * 1e4 / c["words"] if c["words"] else 0.0


# ------------------------------------------------------------------------------ the texts


def control_text(spec: str) -> str | None:
    where, _, name = spec.partition(":")
    if where == "candidates":
        return _file(CAND / name)
    return _file(SRC / where / name / "text.txt")


def controls(cfg: dict) -> list[tuple[str, str, str | None]]:
    """(name, group, text or None) for every control book, in config order."""
    a = cfg["lab"]["anachronisms"]
    return [(name, group, control_text(spec)) for group, books in a["controls"].items()
            for name, spec in books.items()]  # fmt: skip


def probe_forms(cfg: dict) -> dict[str, dict]:
    a = cfg["lab"]["anachronisms"]
    items = []
    for p in a["new_world_probes"]:
        fs = a["maize_forms"] if p == "maize" else [p]
        items.append({"id": p, "countable": True, "forms": fs, "plural": True, "guard": False})
    return compile_forms(items)


# ------------------------------------------------------------------------------ known answers


def plant(words: list[str], forms: dict[str, dict], items: list[dict], n: int, seed: int):
    """Insert ``n`` copies of each countable item's first form at seeded safe positions."""
    every = set()
    for f in forms.values():
        every |= f["single"] | {w for p in f["phrases"] for w in p}
    low = [w.lower() for w in words]
    safe = [i for i in range(1, len(words)) if low[i - 1] not in every | inv.DET
            and low[i] not in every]  # fmt: skip
    rng = random.Random(seed)
    inserts: dict[int, list[str]] = {}
    planted = {}
    for it in items:
        if not it.get("forms"):
            continue
        unit = (["the"] if it["guard"] else []) + it["forms"][0].split()
        for pos in rng.sample(safe, n):
            inserts.setdefault(pos, []).append(unit)
        planted[it["id"]] = n
    res = []
    for i, w in enumerate(words):
        for unit in inserts.get(i, ()):
            res += unit + ["and"]
        res.append(w)
    return res, planted


def known_answer(cfg: dict, items: list[dict], forms: dict, named: dict[str, str | None],
                 meso_native: list[str]) -> dict:  # fmt: skip
    a = cfg["lab"]["anachronisms"]
    res: dict = {}
    nt = named.get("kjv_new_testament")
    if nt is None:
        return {"passed": False, "not_attempted": "kjv_new_testament not readable"}
    words = inv.words_of(nt)
    base = count_words(words, forms)
    planted_words, planted = plant(words, forms, items, a["planted_per_item"], a["seed"])
    after = count_words(planted_words, forms)
    misses = {k: [base.get(k, 0), after.get(k, 0), n] for k, n in planted.items()
              if after.get(k, 0) - base.get(k, 0) != n}  # fmt: skip
    share = 1 - len(misses) / len(planted)
    res["planted"] = {"things": len(planted), "per_item": a["planted_per_item"],
                      "recovered_share": share, "misses": misses,
                      "passed": share >= a["bar_planted"]}  # fmt: skip
    pres = {}
    for text, need in a["documented_present"].items():
        t = named.get(text)
        got = count_words(inv.words_of(t), forms) if t is not None else None
        for iid, k in need.items():
            pres[f"{text}/{iid}"] = {"need": k, "got": None if got is None else got.get(iid, 0)}
    for v in pres.values():
        v["passed"] = v["got"] is not None and v["got"] >= v["need"]
    res["documented_present"] = pres
    probes = probe_forms(cfg)
    maize = 0
    read = []
    for nm in meso_native:
        if named.get(nm) is not None:
            maize += count_words(inv.words_of(named[nm]), probes).get("maize", 0)
            read.append(nm)
    res["maize_in_mesoamerican_native_texts"] = {
        "texts": read,
        "got": maize,
        "need": a["maize_min"],
        "passed": bool(read) and maize >= a["maize_min"],
    }
    absent = {}
    for nm in ("kjv_old_testament", "kjv_new_testament", "kjv_apocrypha"):
        t = named.get(nm)
        absent[nm] = None if t is None else count_words(inv.words_of(t), probes)
    res["new_world_probes_in_kjv"] = {
        "counts": absent,
        "passed": all(v is not None and not v for v in absent.values()),
    }
    res["passed"] = (res["planted"]["passed"] and all(v["passed"] for v in pres.values())
                     and res["maize_in_mesoamerican_native_texts"]["passed"]
                     and res["new_world_probes_in_kjv"]["passed"])  # fmt: skip
    return res


# ------------------------------------------------------------------------------ the tally


def fisher(table: list[list[int]]) -> float | None:
    from scipy.stats import fisher_exact

    if any(sum(r) == 0 for r in table) or any(sum(c) == 0 for c in zip(*table, strict=True)):
        return None
    return float(fisher_exact(table)[1])


def _verdict(t: list[list[int]], p: float | None, alpha: float) -> str:
    share = [t[i][0] / sum(t[i]) if sum(t[i]) else None for i in (0, 1)]
    if p is None or None in share:
        return "cannot tell"
    return "yes" if p < alpha and share[0] > share[1] else "no"


def cross_table(items: list[dict], flag: str, alpha: float, loose: bool = False) -> dict:
    """Roper-confirmed (rows: yes, no) by ``flag`` (cols: yes, no), over items with a status.
    ``loose`` counts partly confirmed as confirmed."""
    rows = [it for it in items if it.get("roper_status") is not None and it.get(flag) is not None]
    if not rows:
        return {"not_attempted": "Roper's item statuses are not keyed"}
    ok = ("confirmed", "partial") if loose else ("confirmed",)
    t = [[0, 0], [0, 0]]
    for it in rows:
        t[0 if it["roper_status"] in ok else 1][0 if it[flag] else 1] += 1
    p = fisher(t)
    share = [t[i][0] / sum(t[i]) if sum(t[i]) else None for i in (0, 1)]
    return {"items": len(rows), "rows": "confirmed" + ("_or_partial" if loose else "") + ", not",
            "cols": f"{flag}, not", "table": t, "fisher_p": p,
            "share_flagged_among_confirmed": share[0], "share_flagged_among_other": share[1],
            "verdict": _verdict(t, p, alpha)}  # fmt: skip


def kind_tables(items: list[dict], alpha: float) -> dict:
    """For each kind of confirmation: that kind against every other kind, by confirmed or not
    (one exact test per kind; several tests, so read p values with that in mind)."""
    kinds = sorted({it["roper_confirmation_kind"] for it in items
                    if it.get("roper_confirmation_kind")})  # fmt: skip
    res = {}
    for k in kinds:
        flagged = [{**it, "is_kind": it["roper_confirmation_kind"] == k} for it in items]
        res[k] = cross_table(flagged, "is_kind", alpha)
        res[k]["items_of_kind"] = sum(f["is_kind"] for f in flagged)
    return res


def world_summary(texts: dict[str, dict], ids: list[str]) -> dict:
    res = {}
    for world in sorted({t["world"] for t in texts.values()}):
        names = [n for n, t in texts.items() if t["world"] == world]
        per = {}
        for iid in ids:
            rs = [rate(texts[n], iid) for n in names]
            per[iid] = {"share_of_texts": round(sum(r > 0 for r in rs) / len(rs), 3),
                        "median_per_10k": round(median(rs), 3),
                        "max_per_10k": round(max(rs), 3)}  # fmt: skip
        res[world] = {"texts": len(names), "items": per}
    return res


def gather(cfg: dict, forms: dict, with_background: bool = True) -> dict:
    """Load and count every text; the long-s vocabulary is fixed first, as in BOM-111."""
    rows = inv.prepare(cfg)
    named = {n: t for n, _, _, t in rows}
    texts, missing = {}, []
    for name, world, register, text in rows:
        c = counted(name, text, forms)
        if c is None:
            missing.append(name)
            continue
        texts[name] = {**c, "world": world or "scored_only", "register": register}
    if with_background:
        _, back = inv.library_samples(cfg)
        for r in back:
            c = counted(r["work_id"], _library(r), forms)
            if c is None:
                missing.append(r["work_id"])
            else:
                texts[r["work_id"]] = {**c, "world": "background", "register": "library"}
    ctl = {}
    for name, group, text in controls(cfg):
        c = counted("control-" + name, text, forms)
        if c is None:
            missing.append(name)
        else:
            ctl[name] = {**c, "group": group}
    native = [n for n, w, r, _ in rows if w == "mesoamerica" and r == "native"]
    return {"named": named, "texts": texts, "controls": ctl, "missing": missing,
            "native": native}  # fmt: skip


def n_of(c: dict, it: dict) -> int:
    return c["counts"].get(it["thing"], 0) if it.get("thing") else 0


def tally(cfg: dict, items: list[dict], forms: dict, data: dict) -> dict:
    a = cfg["lab"]["anachronisms"]
    cnt = [it for it in items if it.get("thing")]
    things = sorted({it["thing"] for it in cnt})
    memory = {it["id"] for it in items if it.get("from_memory")}
    texts = data["texts"]
    kjv = {k: texts[k]["counts"] for k in ("kjv_old_testament", "kjv_new_testament",
                                            "kjv_apocrypha") if k in texts}  # fmt: skip
    bible_thing = {t: (kjv.get("kjv_old_testament", {}).get(t, 0)
                       + kjv.get("kjv_new_testament", {}).get(t, 0)) >= a["bible_min"]
                   for t in things}  # fmt: skip
    book = {"all_text": counted("book_of_mormon", bom_text(False), forms),
            "without_quoted_chapters": counted("book_of_mormon_without_quoted", bom_text(True),
                                               forms)}  # fmt: skip
    res: dict = {"book_of_mormon": {}, "controls": {}}
    for k, c in book.items():
        present = [it["id"] for it in cnt if n_of(c, it) >= a["present_min"]]
        res["book_of_mormon"][k] = {
            "words": c["words"], "counts": c["counts"],
            "per_10k": {t: round(rate(c, t), 3) for t in things if c["counts"].get(t)},
            "items_present": len(present), "things_present":
            sum(1 for t in things if c["counts"].get(t, 0) >= a["present_min"]),
            "present": present}  # fmt: skip
    in_book = set(res["book_of_mormon"]["all_text"]["present"])
    subsets = [("all_items", lambda it: True)]
    if memory:
        subsets.append(("without_memory_items", lambda it: it["id"] not in memory))
    for subset, keep in subsets:
        its = [it for it in cnt if keep(it)]
        book_s = [it for it in its if it["id"] in in_book]
        per = {}
        for name, c in data["controls"].items():
            present = [it for it in its if n_of(c, it) >= a["present_min"]]
            shared = [it for it in present if it["id"] in in_book]
            per[name] = {"group": c["group"], "words": c["words"],
                         "items_present": len(present),
                         "share_of_countable": round(len(present) / len(its), 3),
                         "book_items_present": len(shared),
                         "share_of_book_items": round(len(shared) / len(book_s), 3)
                         if book_s else None,
                         "things_present": sorted({it["thing"] for it in present}),
                         "present": [it["id"] for it in present],
                         "confirmed_items_present": sum(it.get("roper_status") == "confirmed"
                                                        for it in present),
                         "per_10k": {t: round(rate(c, t), 3)
                                     for t in sorted({it["thing"] for it in present})}}  # fmt: skip
        nc = per.get(a["named_control"])
        s = None if nc is None else nc["share_of_book_items"]
        verdict = ("not attempted" if s is None else "yes" if s >= a["control_share_bar"]
                   else "no" if s < a["control_share_low"] else "partly")  # fmt: skip
        res["controls"][subset] = {"countable_items": len(its), "book_items": len(book_s),
                                   "books": per, "named_control": a["named_control"],
                                   "verdict_named_control": verdict}  # fmt: skip
    bible_item = {it["id"]: bible_thing[it["thing"]] for it in cnt}
    conf = [it for it in cnt if it.get("roper_status") == "confirmed"]
    res["bible"] = {
        "kjv_counts": kjv,
        "bible_things": sorted(t for t in things if bible_thing[t]),
        "not_bible_things": sorted(t for t in things if not bible_thing[t]),
        "countable_items": len(cnt),
        "bible_items": sum(bible_item.values()),
        "share_of_countable_items": round(sum(bible_item.values()) / len(cnt), 3) if cnt else None,
        "confirmed_countable_items": len(conf),
        "confirmed_that_are_bible_items": sum(bible_item[it["id"]] for it in conf),
        "share_of_confirmed_that_are_bible_items":
        round(sum(bible_item[it["id"]] for it in conf) / len(conf), 3) if conf else None,
    }  # fmt: skip
    flagged = [{**it, "bible_item": bible_item.get(it["id"])} for it in items]
    res["cross_tables"] = {
        "confirmed_by_bible_item": cross_table(flagged, "bible_item", a["alpha"]),
        "confirmed_or_partial_by_bible_item": cross_table(flagged, "bible_item", a["alpha"], True),
        "confirmed_by_kind_of_confirmation": kind_tables(items, a["alpha"])
        if any(it.get("roper_confirmation_kind") for it in items) else
        {"not_attempted": "no kinds keyed"},
    }  # fmt: skip
    res["worlds"] = world_summary(texts, things)
    res["texts"] = {n: {"world": t["world"], "register": t["register"], "words": t["words"],
                        "things_present": sum(1 for x in things if t["counts"].get(x, 0)
                                              >= a["present_min"]),
                        "counts": t["counts"]}
                    for n, t in texts.items() if t["world"] != "background"}  # fmt: skip
    return res


# ------------------------------------------------------------------------------ judging (prepared)

KNOWN_JUDGE = {  # written from memory by the AI: codes taken as uncontroversial for the
    # Book of Mormon's claimed setting; the judge must match these before its answers are read
    "maize": "mesoamerica_in_period", "cacao": "mesoamerica_in_period",
    "domestic turkey": "mesoamerica_in_period", "jaguar": "mesoamerica_in_period",
    "llama": "americas_other_time_or_place", "potato": "americas_other_time_or_place",
    "wheat": "old_world_only", "war chariot": "old_world_only",
    "silk from silkworms": "old_world_only", "gunpowder": "not_attested",
    "telescope": "not_attested", "printing press with movable type": "not_attested",
}  # fmt: skip

SCALE_TEXT = (
    "mesoamerica_in_period = attested in Mesoamerica within the claimed period; "
    "americas_other_time_or_place = attested in the Americas, but at another time or place; "
    "old_world_only = attested before the end of the claimed period somewhere in the Old World, "
    "not in the Americas; not_attested = not attested anywhere before the end of the claimed "
    "period; not_applicable = not a physical thing or practice that archaeology could attest."
)


def _prompt(setting: str, item: str, passages: list[str]) -> str:
    shown = "\n\n".join(f"Passage {i + 1}: ...{p}..." for i, p in enumerate(passages))
    return (
        SIMULATED + "You are coding claimed anachronisms. A book claims this setting: "
        f"{setting}.\nThe item: {item}.\n" + (shown + "\n" if shown else "")
        + "Question 1: code the item as the book uses it, for the claimed setting, on this "
        f"scale: {SCALE_TEXT}\n"
        "Question 2 (the loose standard): would it count as 'confirmed' if confirmed meant "
        "attested anywhere in the ancient world before the end of the claimed period? yes or no.\n"
        'Reply with one line of JSON only: {"code": "...", "loose_confirmed": "yes|no", '
        '"basis": "a few words naming the evidence"}'
    )  # fmt: skip


def windows(text: str, iid: str, forms: dict, cfg: dict) -> list[str]:
    a = cfg["lab"]["anachronisms"]
    words = inv.words_of(text)
    hits = [i for i in range(len(words))
            if count_words(words[i : i + 4], {iid: forms[iid]}).get(iid)
            and not count_words(words[i + 1 : i + 4], {iid: forms[iid]}).get(iid)]  # fmt: skip
    if forms[iid]["guard"]:
        hits = [i + 1 for i in hits]
    pick = hits[:1] + (random.Random(f"{a['seed']}-{iid}").sample(hits[1:], 1) if hits[1:] else [])
    w = a["window_words"]
    return [" ".join(words[max(0, i - w) : i + w]) for i in pick[: a["windows_per_item"]]]


JOBS_NAME = {"roper": "jobs", "standin": "jobs_standin"}


def jobs(cfg: dict, items: list[dict], forms: dict, res: dict, which: str) -> dict:
    """Write the judging questions (not run). Prompts quote passages: private folder only.
    Book of Mormon: every item (counted or not; a counted one shows passages). Controls: every
    counted thing present in a judged control book."""
    a = cfg["lab"]["anachronisms"]
    setting = a["settings_claimed"]["book_of_mormon"]
    known = [{"id": f"known|{k}", "prompt": _prompt(setting, k, [])} for k in KNOWN_JUDGE]
    book_text = bom_text(False)
    present = set(res["book_of_mormon"]["all_text"]["present"])
    bom = [{"id": f"bom|{it['id']}",
            "prompt": _prompt(setting, it["label"], windows(book_text, it["thing"], forms, cfg)
                              if it["id"] in present else [])} for it in items]  # fmt: skip
    ctl = []
    texts = {n: t for n, _, t in controls(cfg)}
    for name, c in res["controls"]["all_items"]["books"].items():
        if c["group"] not in a["judged_groups"]:
            continue
        for t in c["things_present"]:
            ctl.append({"id": f"control|{name}|{t}",
                        "prompt": _prompt(a["settings_claimed"][name], t.replace("_", " "),
                                          windows(texts[name], t, forms, cfg))})  # fmt: skip
    files = {}
    for stage, js in (("known", known), ("bom", bom), ("control", ctl)):
        path = out(PRIVATE / f"{JOBS_NAME[which]}_{stage}.jsonl")
        path.write_text("".join(json.dumps(j, ensure_ascii=False) + "\n" for j in js))
        files[stage] = {"path": str(path), "questions": len(js)}
    files["expected_known"] = KNOWN_JUDGE
    files["label"] = "simulated judging by an AI model; prepared, not run"
    files["model"] = a["judge_model"]
    files["kind_not_stated_by_roper"] = sum(it.get("roper_confirmation_kind") == "not_stated"
                                            for it in items)  # fmt: skip
    return files


# ------------------------------------------------------------------------------ judged answers
# Reads the judge's answers (simulated judging by an AI model) once every question is answered.
# Settings: ``lab.anachronisms.judged`` (set 2026-11-23, before any answer below was read).

CODES = (
    "mesoamerica_in_period",
    "americas_other_time_or_place",
    "old_world_only",
    "not_attested",
    "not_applicable",
)  # fmt: skip  (the prompt's scale, SCALE_TEXT)
JUDGED = OUT / "judged.json"


def parse_judged(reply: str) -> dict | None:
    """One line of JSON with code and loose_confirmed; None if it cannot be read as an answer."""
    s = (reply or "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b < a:
        return None
    try:
        r = json.loads(s[a : b + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(r, dict):
        return None
    code = str(r.get("code", "")).strip().lower()
    loose = str(r.get("loose_confirmed", "")).strip().lower()
    if code not in CODES or loose not in ("yes", "no"):
        return None
    return {"code": code, "loose": loose == "yes"}


def read_judged(stage: str, which: str = "roper") -> dict:
    """Answers of one stage (known, bom, control) by id; open and unreadable ids apart. An
    unreadable reply is logged with its raw text and never counted as an answer."""
    jobs = PRIVATE / f"{JOBS_NAME[which]}_{stage}.jsonl"
    answers = PRIVATE / f"answers{'' if which == 'roper' else '_standin'}_{stage}.jsonl"
    ids = [json.loads(ln)["id"] for ln in jobs.read_text().splitlines() if ln.strip()]
    got: dict[str, dict] = {}
    bad: list[dict] = []
    if answers.exists():
        for ln in answers.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                p = parse_judged(r.get("reply", ""))
                if p is None:
                    bad.append({"id": r["id"], "reply": r.get("reply")})
                else:
                    got[r["id"]] = p
    unread = sorted({b["id"] for b in bad} - set(got))
    if unread:
        out(LOGS / f"anachronisms_unparsed_{stage}.jsonl").write_text(
            "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in bad if b["id"] in unread)
        )
    return {"answers": got, "jobs": len(ids), "answered": sum(i in got for i in ids),
            "open": [i for i in ids if i not in got and i not in unread],
            "unreadable": unread}  # fmt: skip


def _share(k: int, n: int) -> float | None:
    return round(k / n, 3) if n else None


def code_summary(codes: list[dict], strict: str) -> dict:
    n = len(codes)
    st = sum(c["code"] == strict for c in codes)
    lo = sum(c["loose"] for c in codes)
    return {"n": n, "codes": {c: sum(x["code"] == c for x in codes) for c in CODES},
            "strict_confirmed": st, "strict_share": _share(st, n),
            "loose_confirmed": lo, "loose_share": _share(lo, n)}  # fmt: skip


def holds(items: list[dict], ans: dict[str, dict], cfg: dict) -> dict:
    """Of Roper's confirmed items, the share each standard keeps; the verdict by ``holds_bar``."""
    j = cfg["lab"]["anachronisms"]["judged"]
    conf = [ans[it["id"]] for it in items if it["roper_status"] == "confirmed"]
    s = code_summary(conf, j["strict_code"])
    bar = j["holds_bar"]
    verdict = ("holds under the strict rule" if (s["strict_share"] or 0) >= bar
               else "holds only under the loose rule" if (s["loose_share"] or 0) >= bar
               else "does not hold under either rule")  # fmt: skip
    return {"roper_confirmed": s, "bar": bar, "verdict": verdict}


def compare(ctl: list[dict], book: list[dict], key: str, alpha: float) -> dict:
    """Fisher's exact test: share confirmed (by ``key``) in a control against the book."""
    k1, k2 = sum(c[key] for c in ctl), sum(b[key] for b in book)
    t = [[k1, len(ctl) - k1], [k2, len(book) - k2]]
    p = fisher(t)
    s1, s2 = _share(k1, len(ctl)), _share(k2, len(book))
    verdict = ("cannot tell" if p is None else "same" if p >= alpha
               else "control lower" if s1 < s2 else "control higher")  # fmt: skip
    return {"control": [k1, len(ctl)], "book": [k2, len(book)], "control_share": s1,
            "book_share": s2, "fisher_p": p, "verdict": verdict}  # fmt: skip


def score_judged(cfg: dict, items: list[dict], result: dict) -> dict:
    """The judged half, from the answers; refused while any answer is open or unreadable, or if
    the judge's known-answer subset is below its bar. ``result`` is the counting run's result."""
    a = cfg["lab"]["anachronisms"]
    j = a["judged"]
    stages = {s: read_judged(s) for s in ("known", "bom", "control")}
    state = {s: {"jobs": r["jobs"], "answered": r["answered"], "open": len(r["open"]),
                 "unreadable": r["unreadable"]} for s, r in stages.items()}  # fmt: skip
    if any(r["open"] or r["unreadable"] for r in stages.values()):
        return {"refused": "answers still open or unreadable; nothing scored", "answers": state}
    kn = stages["known"]["answers"]
    hit = sum(kn[f"known|{k}"]["code"] == v for k, v in KNOWN_JUDGE.items())
    known = {"matched": hit, "of": len(KNOWN_JUDGE), "bar": a["judge_bar"],
             "passed": hit / len(KNOWN_JUDGE) >= a["judge_bar"]}  # fmt: skip
    if not known["passed"]:
        return {"refused": "the judge's known-answer subset is below its bar", "known": known,
                "answers": state}  # fmt: skip
    bom = {k.split("|", 1)[1]: v for k, v in stages["bom"]["answers"].items()}
    strict = j["strict_code"]
    only_quoted = set(result["book_of_mormon"]["all_text"]["present"]) - set(
        result["book_of_mormon"]["without_quoted_chapters"]["present"]
    )
    subsets = {"all_items": items,
               "without_items_only_in_quoted_chapters":
               [it for it in items if it["id"] not in only_quoted]}  # fmt: skip
    statuses = ("confirmed", "partial", "unconfirmed")
    book: dict = {}
    for name, its in subsets.items():
        by_status = {s: code_summary([bom[it["id"]] for it in its if it["roper_status"] == s],
                                     strict) for s in statuses}  # fmt: skip
        book[name] = {"all": code_summary([bom[it["id"]] for it in its], strict),
                      **holds(its, bom, cfg), "by_roper_status": by_status}  # fmt: skip
    book["by_era_first_raised"] = {
        e: {**code_summary([bom[it["id"]] for it in items if it["era_first_raised"] == e], strict),
            "roper_confirmed": sum(it["roper_status"] == "confirmed" for it in items
                                   if it["era_first_raised"] == e)}
        for e in sorted({str(it["era_first_raised"]) for it in items})
    }  # fmt: skip
    book["by_category"] = {c: code_summary([bom[it["id"]] for it in items
                                            if it["category"] == c], strict)
                           for c in sorted({it["category"] for it in items})}  # fmt: skip
    book["loose_against_roper"] = {s: {"loose_yes": sum(bom[it["id"]]["loose"] for it in items
                                                        if it["roper_status"] == s),
                                       "items": sum(it["roper_status"] == s for it in items)}
                                   for s in ("confirmed", "partial", "unconfirmed")}  # fmt: skip
    book["items"] = {it["id"]: bom[it["id"]] for it in items}
    # the controls: each judged book's things against the book's countable items, same codes
    base = (
        [it for it in items if it.get("thing")] if j["compare_book_items"] == "countable" else items
    )
    bvals = [{**bom[it["id"]], "strict": bom[it["id"]]["code"] == strict} for it in base]
    ctl_ans: dict[str, dict[str, dict]] = {}
    for k, v in stages["control"]["answers"].items():
        _, name, thing = k.split("|", 2)
        ctl_ans.setdefault(name, {})[thing] = v
    groups = result["controls"]["all_items"]["books"]
    controls = {}
    for name, things in sorted(ctl_ans.items()):
        vals = [{**v, "strict": v["code"] == strict} for v in things.values()]
        row = {
            "group": groups.get(name, {}).get("group"),
            **code_summary(vals, strict),
            "loose_vs_book": compare(vals, bvals, "loose", a["alpha"]),
            "things": things,
        }
        if name in j["strict_defined_for"]:
            row["strict_vs_book"] = compare(vals, bvals, "strict", a["alpha"])
        else:
            row["strict_vs_book"] = "not defined: the book is not set in the Americas"
        controls[name] = row
    named = controls.get(a["named_control"])
    named_v = ("not attempted" if named is None else
               "the control shows the same under the loose rule"
               if named["loose_vs_book"]["verdict"] in ("same", "control higher")
               else "the control is confirmed less often under the loose rule")  # fmt: skip
    return {
        "label": "simulated judging by an AI model (" + a["judge_model"] + ")",
        "answers": state, "known": known, "settings": j,
        "book_of_mormon": book,
        "book_items_compared": {"which": j["compare_book_items"], "n": len(bvals),
                                **code_summary(bvals, strict)},
        "controls": controls,
        "named_control": a["named_control"], "named_control_verdict": named_v,
        "verdict_book": book["all_items"]["verdict"],
        "trend_in_control": "not attempted: the control books' things have no dates first "
                            "raised, so no change over time can be built",
    }  # fmt: skip


# ------------------------------------------------------------------------------ commands


def load_list(cfg: dict, which: str) -> tuple[list[dict], list[dict]]:
    """(items, things) for Roper's list or the stand-in, from the written files if present."""
    a = cfg["lab"]["anachronisms"]
    p = Path(a["items"] if which == "roper" else a["items_standin"])
    if p.exists():
        body = json.loads(p.read_text())
        return body["items"], body["things"]
    if which == "roper":
        return roper.key_items()["items"], roper_things()
    items = keyed_items()
    return items, standin_things(items)


def write_items(cfg: dict) -> list[Path]:
    a = cfg["lab"]["anachronisms"]
    keyed = roper.key_items()
    if not keyed["items"]:
        raise SystemExit(keyed.get("not_attempted", "Roper's chapters not readable"))
    rthings = roper_things()
    body = {"what": "BOM-113: Roper 2025's own items, keyed from his held chapters (headings "
            "machine-read; eras and 1844/1965 statuses keyed by hand by the AI from the figure "
            "images; categories, things and the kind rule are the AI's choices)",
            "source": roper.HELD_SOURCE, "items_sha256": items_sha(compile_forms(rthings)),
            "keying_check": keyed["keying_check"],
            "counts": {"items": len(keyed["items"]),
                       "countable": sum(i["countable"] for i in keyed["items"]),
                       "things": len(rthings)},
            "things": rthings, "items": keyed["items"]}  # fmt: skip
    paths = [out(Path(a["items"]))]
    paths[0].write_text(json.dumps(body, indent=1) + "\n")
    items = keyed_items()
    sthings = standin_things(items)
    body = {"what": "BOM-113 stand-in list, used before Roper's chapters were held: the held "
            "Wikipedia article, Coe 1973 via the research note, and a labelled memory supplement",
            "held_then": HELD, "items_sha256": items_sha(compile_forms(sthings)),
            "counts": {"items": len(items), "countable": sum(i["countable"] for i in items),
                       "from_memory": sum(i["from_memory"] for i in items)},
            "things": sthings, "items": items}  # fmt: skip
    paths.append(out(Path(a["items_standin"])))
    paths[1].write_text(json.dumps(body, indent=1) + "\n")
    return paths


def _stamp(res: dict) -> dict:
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["items", "check", "run", "jobs", "judged"])
    ap.add_argument("--list", dest="which", choices=["roper", "standin"], default="roper")
    ap.add_argument("--no-background", action="store_true", help="skip the library sample")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "items":
        print("wrote", *write_items(cfg))
        return 0
    items, things = load_list(cfg, a.which)
    if a.cmd == "judged":
        if a.which != "roper":
            raise SystemExit("judged: Roper's list only (the stand-in was never judged)")
        res_path = OUT / "result.json"
        if not res_path.exists():
            raise SystemExit("judged: run `python -m lab.anachronisms run` first")
        got = score_judged(cfg, items, json.loads(res_path.read_text()))
        if "refused" in got:
            print("refused:", got["refused"])
            print(json.dumps(got.get("answers"), indent=1))
            return 1
        out(JUDGED).write_text(json.dumps(_stamp(got), indent=1) + "\n")
        print(got["verdict_book"], "|", got["named_control_verdict"], "->", JUDGED)
        return 0
    forms = compile_forms(things)
    suffix = "" if a.which == "roper" else "_standin"
    data = gather(cfg, forms, with_background=not a.no_background and a.cmd == "run")
    ka = known_answer(cfg, things, forms, data["named"], data["native"])
    if a.cmd == "check":
        out(OUT / f"known_answer{suffix}.json").write_text(
            json.dumps(_stamp({"list": a.which, "known_answer": ka}), indent=1) + "\n"
        )
        print(json.dumps(ka, indent=1))
        return 0 if ka["passed"] else 1
    if not ka["passed"]:
        print("known-answer check missed: nothing else is reported")
        print(json.dumps(ka, indent=1))
        return 1
    res = tally(cfg, items, forms, data)
    if a.cmd == "jobs":
        print(json.dumps(jobs(cfg, items, forms, res, a.which), indent=1))
        return 0
    full = {"list": a.which, "settings": cfg["lab"]["anachronisms"],
            "items_sha256": items_sha(forms), "known_answer": ka,
            "not_attempted": data["missing"], **res}  # fmt: skip
    if a.which == "roper":
        full["roper_totals"] = roper_totals(items)
    out(OUT / f"result{suffix}.json").write_text(json.dumps(_stamp(full), indent=1) + "\n")
    print("wrote", OUT / f"result{suffix}.json")
    return 0


def roper_totals(items: list[dict]) -> dict:
    """Roper's own tallies reproduced from the keyed list, by chapter, era raised and kind."""
    keys = ("confirmed", "partial", "unconfirmed")

    def count(rows):
        c = Counter(it["roper_status"] for it in rows)
        return {**{k: c.get(k, 0) for k in keys}, "total": len(rows)}

    return {
        "all": count(items), "stated": roper.STATED["1966-2024"],
        "by_chapter": {roper.CHAPTERS[ch]: count([i for i in items if i["chapter"] == ch])
                       for ch in roper.CHAPTERS},
        "by_era_first_raised": {e: count([i for i in items if i["era_first_raised"] == e])
                                for e in sorted({i["era_first_raised"] for i in items})},
        "by_kind": {k: count([i for i in items if i["roper_confirmation_kind"] == k])
                    for k in sorted({i["roper_confirmation_kind"] for i in items})},
        "status_1844_from_figures": dict(Counter(i["status_1844"] for i in items
                                                 if i["status_1844"])),
        "status_1965_from_figures": dict(Counter(i["status_1965"] for i in items
                                                 if i["status_1965"])),
    }  # fmt: skip


if __name__ == "__main__":
    raise SystemExit(main())
