"""BOM-112 (first part): Dale and Dale's checklist keyed, its arithmetic redone, controls prepared.

Dale and Dale (2019, *Interpreter*, pp. 77-186) list 131 correspondences between the Book of
Mormon and Coe's *The Maya* (Appendix A), each with a ratio of 0.5, 0.1 or 0.02, and 18 negative
ones (Appendix B) at 2, 10 or 50; they multiply them as independent and with a prior of 10^9
against report 1.03 x 10^-111 that the book is fiction. Appendices C and D score Spalding's
manuscript and *View of the Hebrews* the same way.

``keys`` reads the paper (private PDF, fetched once from the Interpreter site) and keys every item:
number, a short label (the paper's heading, shortened), category, ratio, journal page, and two
fields coded by the AI agent **from memory** by written rules (``lab.dalechecklist_coding``).
``arith`` reproduces their numbers from the keyed ratios (the known-answer check) and recomputes
the total under stated alternatives. ``jobs`` applies the same checklist to control texts: keyword
rules pull candidate passages (private) and one question per item and text is written for
``lab.judge``; every answer will be **simulated judging by an AI model**. Nothing is judged here.
The test card is ``data/private/lab/owner/2026-11-21-dale-checklist/card.md``. Public files hold
labels, numbers and page numbers, never text from the paper or any book.

Usage::

    python -m lab.dalechecklist keys     # paper -> data/lab/setting/dale_checklist/items.json
    python -m lab.dalechecklist arith    # known-answer check + alternatives -> result.json
    python -m lab.dalechecklist jobs     # candidate passages + judging questions (private)
    python -m lab.dalechecklist jobs2    # second design: keyword + meaning passages (private)
    python -m lab.dalechecklist checkc [--design first|second]   # score check C from answers
    python -m lab.dalechecklist controls # score the controls (refused unless check C passed)

The second design (2026-11-23, post hoc, after check C missed) keeps the bars and adds windows
found by meaning (the passage index's own model) to the keyword windows, for every text alike.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from pathlib import Path

from lab import dalechecklist_coding as coding
from lab.numbers import CAND, KJV, SRC, _file, bom_text, gutenberg
from lab.paths import LOGS, REGISTRY, out
from metadata import config

PRIVATE = Path("data/private/lab/owner/2026-11-21-dale-checklist")
PDF = PRIVATE / "source" / "dale2019.pdf"
TEXT = PRIVATE / "source" / "dale2019.txt"
PUBLIC = REGISTRY / "setting" / "dale_checklist"
FROM_MEMORY = (
    "coded by the AI agent (Claude) from memory by the rules in lab/dalechecklist_coding.py; "
    "no handbook or source text was consulted"
)


def settings(cfg: dict) -> dict:
    return cfg["lab"]["dale_checklist"]


# ------------------------------------------------------------------------------ keying the paper


def paper_text() -> str | None:
    """The paper's text (layout kept), extracted once to the private folder; None if not held."""
    if not TEXT.exists():
        if not PDF.exists():
            return None
        got = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True,
                             text=True)  # fmt: skip
        if got.returncode != 0 or not got.stdout.strip():
            return None
        out(TEXT).write_text(got.stdout, encoding="utf-8")
    return TEXT.read_text(encoding="utf-8")


_RATIO = re.compile(
    r"(?:[Ll]ikelihood|weight|be)(?:\s+(?:is|would be|therefore))*\s*"
    r"(?:(?:[0-9.]+/[0-9.]+\s*)?=|of|weighted\s+more\s+than)\s*([0-9]+(?:\.[0-9]+)?)"
)


_SUMMARY = re.compile(r"^\s*(Calculation of|Summary of)")


def _lines_with_pages(text: str, first_page: int) -> list[tuple[int, str]]:
    """Each line with its journal page (the PDF's n-th page is journal page first_page + n)."""
    rows = []
    for n, page in enumerate(text.split("\f")):
        for line in page.split("\n"):
            rows.append((first_page + n, line))
    return rows


def _region(rows: list[tuple[int, str]], start: str, stop: str | None) -> list[tuple[int, str]]:
    a = next(i for i, (_, s) in enumerate(rows) if s.strip() == start)
    b = len(rows)
    if stop is not None:
        b = next(i for i, (_, s) in enumerate(rows) if i > a and s.strip() == stop)
    return rows[a:b]


def _is_header(s: str) -> bool:
    return bool(re.search(r"• Interpreter|Greatest Guesser • \d+\s*$", s))


def _items(rows: list[tuple[int, str]], head: re.Pattern, sequential: bool = False) -> list[dict]:
    """Split a region into items at lines matching ``head``; label runs to 'Coe's standard'.

    ``sequential``: numbered 1, 2, 3 ...; a line whose number breaks the run (a footnote) is not an
    item start.
    """
    starts = [i for i, (_, s) in enumerate(rows) if head.match(s)]
    if sequential:
        keep, want = [], 1
        for i in starts:
            n = int(head.match(rows[i][1]).group("num"))
            if n == want or (n == 1 and keep):
                keep.append(i)
                want = n + 1
        starts = keep
    res = []
    for k, i in enumerate(starts):
        j = starts[k + 1] if k + 1 < len(starts) else len(rows)
        block = [s for _, s in rows[i:j] if not _is_header(s)]
        stop = next((n for n, s in enumerate(block) if n and _SUMMARY.match(s)), len(block))
        block = block[:stop]  # a section's own summary of ratios is not part of its last item
        m = head.match(rows[i][1])
        label = m.group("label").strip()
        for s in block[1:]:
            if (
                re.match(r"\s*(Coe.s standard|Coe.s|“?Manuscript Found|View of)", s)
                or not s.strip()
            ):
                break
            label += " " + s.strip()
        body = " ".join(block)
        ratios = _RATIO.findall(body)
        res.append({
            "num": m.group("num"),
            "label_full": re.sub(r"\s+", " ", label).strip(),
            "ratio": float(ratios[-1]) if ratios else None,
            "page": rows[i][0],
        })  # fmt: skip
    return res


def short(label: str, n: int) -> str:
    """The paper's heading cut to at most n characters at a word boundary, quotes removed."""
    s = re.sub(r"[“”\"]", "", label)
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + " ..."


def parse(text: str, cfg: dict) -> dict[str, list[dict]]:
    """Every item of Appendices A-D: appendix, number, label, category, ratio, journal page."""
    st = settings(cfg)
    rows = _lines_with_pages(text, st["first_pdf_page_journal"])
    A = _region(rows, "Appendix A", "Appendix B")
    B = _region(rows, "Appendix B", "Appendix C")
    C = _region(rows, "Appendix C", "Appendix D")
    D = _region(rows, "Appendix D", None)
    sec = re.compile(r"^(\d)\. (.+) Correspondences\s*$")
    a_head = re.compile(r"^\s{0,4}(?P<num>\d\.\d{1,2})\.?\s+(?P<label>[A-Z“].*)$")
    n_head = re.compile(r"^\s{0,4}(?P<num>\d{1,2})\.\s+(?P<label>[A-Z“].*)$")
    out_: dict[str, list[dict]] = {}
    # Appendix A, by section
    cats = [(i, sec.match(s)) for i, (_, s) in enumerate(A) if sec.match(s)]
    pos = []
    for k, (i, m) in enumerate(cats):
        j = cats[k + 1][0] if k + 1 < len(cats) else len(A)
        for it in _items(A[i + 1 : j], a_head):
            it["category"] = st["categories"][int(m.group(1)) - 1]
            pos.append(it)
    out_["A"] = pos
    # Appendix B: the six from The Maya, then the twelve from Coe's article and podcasts
    b_items = _items(B, n_head, sequential=True)
    for k, it in enumerate(b_items):
        it["part"] = "the_maya" if k < st["b_first_part"] else "article_and_podcasts"
        if k >= st["b_first_part"]:  # the second part numbers from 1 again
            it["num"] = "p" + it["num"]
    out_["B"] = b_items

    def split(region, pos_head: str, neg_head: str) -> tuple[list[dict], list[dict]]:
        p = next(i for i, (_, s) in enumerate(region) if s.strip().startswith(pos_head))
        q = next(i for i, (_, s) in enumerate(region) if s.strip().startswith(neg_head))
        e = next((i for i, (_, s) in enumerate(region) if i > q
                  and s.strip().startswith("Summary of the Negative")), len(region))  # fmt: skip
        ps = next(i for i, (_, s) in enumerate(region) if i > p
                  and s.strip().startswith("Summary of the Positive"))  # fmt: skip
        return (
            _items(region[p + 1 : ps], n_head, sequential=True),
            _items(region[q + 1 : e], n_head, sequential=True),
        )

    out_["C_pos"], out_["C_neg"] = split(C, "Positive Correspondences between", "Negative Corresp")
    out_["D_pos"], out_["D_neg"] = split(D, "Positive Correspondences between", "Negative Corresp")
    return out_


def keyed(cfg: dict) -> dict | None:
    """The items with the added fields; None if the paper is not held."""
    text = paper_text()
    if text is None:
        return None
    st = settings(cfg)
    parts = parse(text, cfg)
    items = []
    for appendix, rows in parts.items():
        for it in rows:
            iid = f"{appendix}:{it['num']}"
            add = coding.ADDED.get(iid, {})
            items.append({
                "id": iid,
                "appendix": appendix,
                "num": it["num"],
                "label": short(it["label_full"], st["label_chars"]),
                "category": it.get("category") or coding.CATEGORY.get(iid),
                "part": it.get("part"),
                "ratio": it["ratio"],
                "direction": "positive" if appendix in ("A", "C_pos", "D_pos") else "negative",
                "page": it["page"],
                "near_east": add.get("near_east"),
                "generic": add.get("generic"),
                "group": coding.NEG_GROUP.get(iid),
            })  # fmt: skip
    return {"items": items}


# ------------------------------------------------------------------------------ the arithmetic


def log10_product(ratios: list[float]) -> float:
    return sum(math.log10(r) for r in ratios)


def sci(lg: float) -> str:
    """A log10 value written as a x 10^b with three significant figures."""
    e = math.floor(lg)
    m = 10 ** (lg - e)
    if round(m, 2) >= 10:
        m, e = m / 10, e + 1
    return f"{m:.2f}e{e}"


def matches(lg: float, printed: float, tol: float) -> bool:
    """Whether 10**lg equals the printed figure within the relative tolerance."""
    return abs(10 ** (lg - math.log10(printed)) - 1) <= tol


def posterior(pos: list[float], neg: list[float], prior: float) -> float:
    """log10 of their 'probability of fiction': prior odds x positive ratios x negative ratios."""
    return math.log10(prior) + log10_product(pos) + log10_product(neg)


def _tally_log(tally: list[int]) -> float:
    return log10_product([0.5] * tally[0] + [0.1] * tally[1] + [0.02] * tally[2])


def known_answer(items: list[dict], cfg: dict) -> dict:
    """Parser counts; their arithmetic from their own tallies; item ratios against those tallies.

    Passes when the item counts match and every printed figure is reproduced from the printed
    tallies. A category whose items, as keyed, disagree with its printed tally is listed as a
    discrepancy in the paper (each was read by hand; see the card), not a parser failure.
    """
    st = settings(cfg)
    pub = st["published"]
    tol = st["tolerance"]
    cats = st["categories"]
    A = [i for i in items if i["appendix"] == "A"]
    counts = {
        "A": len(A),
        "A_by_category": {c: sum(i["category"] == c for i in A) for c in cats},
        "A_missing_ratio": sum(i["ratio"] is None for i in items),
        **{k: sum(i["appendix"] == k for i in items)
           for k in ("B", "C_pos", "C_neg", "D_pos", "D_neg")},
    }  # fmt: skip
    want = {
        "A": pub["n_positive"],
        "A_by_category": dict(zip(cats, pub["by_category"], strict=True)),
        "A_missing_ratio": 0,
        "B": pub["n_negative"], "C_pos": pub["spalding"][0], "C_neg": pub["spalding"][1],
        "D_pos": pub["view_of_the_hebrews"][0], "D_neg": pub["view_of_the_hebrews"][1],
    }  # fmt: skip
    count_ok = {k: counts[k] == want[k] for k in want}
    # (i) their arithmetic, from their printed tallies
    cat, disc = {}, {}
    for c, printed, tally in zip(
        cats, pub["category_products"], pub["category_tallies"], strict=True
    ):
        lg = _tally_log(tally)
        rs = [i["ratio"] for i in A if i["category"] == c]
        keyed_t = [rs.count(0.5), rs.count(0.1), rs.count(0.02)]
        cat[c] = {"printed": printed, "from_their_tally": sci(lg), "ok": matches(lg, printed, tol),
                  "their_tally": tally, "items_as_keyed": keyed_t,
                  "from_items_as_keyed": sci(log10_product(rs))}  # fmt: skip
        if keyed_t != tally:
            disc[c] = {"their_tally": tally, "items_as_keyed": keyed_t}
    tot = [sum(t[k] for t in pub["category_tallies"]) for k in range(3)]
    lp_t = _tally_log(tot)
    lp_i = log10_product([i["ratio"] for i in A])
    neg = [st["headline_negative"]] * pub["n_negative"]
    prior = math.log10(st["prior_against"])
    head_t = prior + lp_t + log10_product(neg)
    head_i = prior + lp_i + log10_product(neg)
    head_c = prior + math.log10(pub["positive_product"]) + log10_product(neg)
    arith = {
        "their_ratio_totals": {"printed": pub["by_ratio"], "sum_of_their_tallies": tot,
                               "ok": tot == pub["by_ratio"]},
        "positive_product": {"printed": pub["positive_product"], "from_their_tallies": sci(lp_t),
                             "ok": matches(lp_t, pub["positive_product"], tol),
                             "from_items_as_keyed": sci(lp_i)},
        "headline": {"printed": pub["headline"], "from_their_tallies": sci(head_t),
                     "exact_within_tolerance": matches(head_t, pub["headline"], tol),
                     # their chain: the printed positive product (rounded) x prior x 50^18
                     "from_their_printed_positive_product": sci(head_c),
                     "ok": matches(head_c, pub["headline"], tol),
                     "from_items_as_keyed": sci(head_i)},
        "by_category": cat,
    }  # fmt: skip
    toy = {
        "their_example": {"ratios": st["toy"], "product": round(10 ** log10_product(st["toy"]), 12),
                          "expected": st["toy_product"],
                          "ok": matches(log10_product(st["toy"]), st["toy_product"], tol)},
        "all_half": {"reproduced": sci(pub["n_positive"] * math.log10(0.5)),
                     "printed": pub["all_half"],
                     "ok": matches(pub["n_positive"] * math.log10(0.5), pub["all_half"], 0.02)},
    }  # fmt: skip
    # their own sums for the other appendices, from the items as keyed (reported, not gating)
    theirs = {}
    for key, printed, label in (
        ("B6", pub["b_maya_cumulative"], "B, the six from The Maya"),
        ("B12", pub["b_podcast_cumulative"], "B, the twelve from article and podcasts"),
        ("C_pos", pub["spalding_positive_product"], "Spalding positives"),
        ("C_neg", pub["spalding_negative_product"], "Spalding negatives"),
        ("D_pos", pub["vothe_positive_product"], "View of the Hebrews positives"),
        ("D_neg", pub["vothe_negative_product"], "View of the Hebrews negatives"),
    ):
        if key == "B6":
            rs = [i["ratio"] for i in items if i["appendix"] == "B" and i["part"] == "the_maya"]
        elif key == "B12":
            rs = [i["ratio"] for i in items if i["appendix"] == "B" and i["part"] != "the_maya"]
        else:
            rs = [i["ratio"] for i in items if i["appendix"] == key]
        lg = log10_product(rs) if all(r is not None for r in rs) else None
        theirs[key] = {"what": label, "printed": printed,
                       "from_items_as_keyed": sci(lg) if lg is not None else None,
                       "ok": bool(lg is not None and matches(lg, printed, tol))}  # fmt: skip
    passed = (all(count_ok.values()) and all(c["ok"] for c in cat.values())
              and all(v["ok"] for v in (arith["their_ratio_totals"], arith["positive_product"],
                                        arith["headline"], *toy.values())))  # fmt: skip
    return {"counts": counts, "counts_ok": count_ok, "arithmetic": arith, "toy": toy,
            "discrepancies_in_the_paper": disc, "their_other_sums": theirs,
            "passed": passed}  # fmt: skip


def _verdict(lg_post: float, cfg: dict) -> str:
    st = settings(cfg)
    if lg_post > -st["fragile_within"]:
        return "fragile"
    if lg_post <= -st["robust_beyond"]:
        return "robust"
    return "between"


def alternatives(items: list[dict], cfg: dict) -> dict:
    """The headline recomputed under each alternative fixed on the card."""
    st = settings(cfg)
    prior = st["prior_against"]
    A = [i for i in items if i["appendix"] == "A"]
    B = [i for i in items if i["appendix"] == "B"]
    hneg = st["headline_negative"]
    cap = st["cap_ratio"]

    def row(pos: list[float], neg: list[float], what: str, **extra) -> dict:
        lg = posterior(pos, neg, prior)
        return {"what": what, "n_positive": len(pos), "n_negative": len(neg),
                "log10_positive": round(-log10_product(pos), 2),
                "log10_negative": round(log10_product(neg), 2),
                "log10_probability_fiction": round(lg, 2), "probability_fiction": sci(lg),
                "verdict": _verdict(lg, cfg), **extra}  # fmt: skip

    res = {}
    pos = [i["ratio"] for i in A]
    tot = [sum(t[k] for t in st["published"]["category_tallies"]) for k in range(3)]
    res["headline_as_printed"] = row(
        [0.5] * tot[0] + [0.1] * tot[1] + [0.02] * tot[2],
        [hneg] * len(B),
        "their headline from their printed tallies",
    )
    res["headline"] = row(
        pos, [hneg] * len(B), "their headline from the 131 item ratios as keyed (the base below)"
    )
    res["negatives_as_itemised"] = row(
        pos, [i["ratio"] for i in B], "their item ratios for the 18 negatives instead of 50 each"
    )
    res["cap_positive"] = row(
        [max(r, 1 / cap) for r in pos],
        [hneg] * len(B),
        f"every positive ratio capped at {cap:g} (0.5); negatives at 50",
    )
    res["cap_both"] = row(
        [max(r, 1 / cap) for r in pos],
        [min(hneg, cap)] * len(B),
        f"every ratio, positive and negative, capped at {cap:g}",
    )
    for key, test, what in (
        (
            "drop_near_east",
            lambda i: i["near_east"] == "yes",
            "drop positive items coded also true of the Bible's world (near_east yes)",
        ),
        (
            "drop_generic",
            lambda i: i["generic"] == "yes",
            "drop positive items coded generic to agrarian states (generic yes)",
        ),
        (
            "drop_either",
            lambda i: i["near_east"] == "yes" or i["generic"] == "yes",
            "drop positive items coded near_east yes or generic yes",
        ),
        (
            "drop_either_or_unclear",
            lambda i: i["near_east"] in ("yes", "unclear") or i["generic"] in ("yes", "unclear"),
            "as drop_either, unclear also dropped",
        ),
    ):
        keep = [i["ratio"] for i in A if not test(i)]
        res[key] = row(keep, [hneg] * len(B), what, coded=FROM_MEMORY)
    # dependence: each category once, at its strongest item; negatives once per group
    by_cat: dict[str, list[float]] = {}
    for i in A:
        by_cat.setdefault(i["category"], []).append(i["ratio"])
    by_grp: dict[str, list[float]] = {}
    for i in B:
        by_grp.setdefault(i["group"] or "ungrouped", []).append(hneg)
    res["one_per_category"] = row(
        [min(v) for v in by_cat.values()],
        [max(v) for v in by_grp.values()],
        "each of the six categories counted once at its strongest item; negatives once per group",
        negative_groups={k: len(v) for k, v in by_grp.items()},
        grouped=FROM_MEMORY,
    )
    # sensitivity curve: summed log ratios scaled by n_eff / n
    lp, ln = -log10_product(pos), log10_product([hneg] * len(B))
    curve = []
    for n_eff in st["n_eff_grid"]:
        f = n_eff / len(pos)
        lg = math.log10(prior) - lp * f + ln * max(f, 1 / len(B))
        curve.append({"n_eff": n_eff, "log10_probability_fiction": round(lg, 2),
                      "verdict": _verdict(lg, cfg)})  # fmt: skip
    # where the curve crosses even odds (log10 = 0), solved exactly
    f0 = math.log10(prior) / (lp - ln)
    res["dependence_curve"] = {
        "what": "summed log ratios scaled by n_eff / 131; negatives scaled in the same proportion",
        "points": curve,
        "n_eff_for_even_odds": round(f0 * len(pos), 1),
    }
    return res


def run_arith(cfg: dict) -> dict | None:
    k = keyed(cfg)
    if k is None:
        return None
    items = k["items"]
    ka = known_answer(items, cfg)
    res = {
        "test": "BOM-112 Dale and Dale checklist: arithmetic (lab; exploratory)",
        "config_sha256": config.sha256_of_config(),
        "source": settings(cfg)["source"],
        "known_answer": ka,
        "coding_note": FROM_MEMORY,
        "coded_counts": {
            f: {
                v: sum(i[f] == v for i in items if i["appendix"] == "A")
                for v in ("yes", "no", "unclear", None)
            }
            for f in ("near_east", "generic")
        },  # fmt: skip
    }
    if ka["passed"]:
        res["alternatives"] = alternatives(items, cfg)
    else:
        res["alternatives"] = "not computed: the known-answer check missed (see known_answer)"
    return res


# ------------------------------------------------------------------------------ the control half


def _kjv_books(books: list[str]) -> str | None:
    raw = _file(KJV)
    if raw is None:
        return None
    rows = (json.loads(line) for line in raw.splitlines())
    return "\n".join(r["text"] for r in rows if r["book"] in set(books))


def control_texts(cfg: dict) -> dict[str, str | None]:
    """name -> text (None = not held: not attempted)."""
    st = settings(cfg)
    res: dict[str, str | None] = {"book_of_mormon": bom_text(drop_quotes=False)}
    for name, (kind, where) in st["controls"].items():
        if kind == "candidate":
            res[name] = _file(CAND / f"{where}.txt")
        elif kind == "corpus":
            res[name] = _file(SRC / where / "text.txt")
        elif kind == "gutenberg":
            raw = _file(SRC / where)
            res[name] = None if raw is None else gutenberg(raw)
        elif kind == "kjv":
            res[name] = _kjv_books(where)
    return res


def windows(text: str, size: int, step: int) -> list[str]:
    w = text.split()
    starts = list(range(0, max(len(w) - size, 0) + 1, step))
    if starts[-1] + size < len(w):  # the tail is never dropped
        starts.append(len(w) - size)
    return [" ".join(w[a : a + size]) for a in starts]


def _overlaps(k: int, used, size: int, step: int) -> bool:
    return any(abs(k - u) * step < size for u in used)


def keyword_picks(wins: list[str], pattern: re.Pattern, size: int, step: int,
                  keep: int) -> list[int]:  # fmt: skip
    """Indices of the ``keep`` windows with most keyword hits (distinct terms first), no overlap."""
    scored = []
    for k, win in enumerate(wins):
        hits = [m.group(0).lower() for m in pattern.finditer(win)]
        if hits:
            scored.append((-len(set(hits)), -len(hits), k))
    scored.sort()
    used: list[int] = []
    for _, _, k in scored:
        if _overlaps(k, used, size, step):  # no overlapping windows
            continue
        used.append(k)
        if len(used) == keep:
            break
    return sorted(used)


def candidates(text: str, pattern: re.Pattern, size: int, step: int, keep: int) -> list[str]:
    """The ``keep`` windows with most keyword hits (distinct terms first), in text order."""
    wins = windows(text, size, step)
    return [wins[k] for k in keyword_picks(wins, pattern, size, step, keep)]


PROMPT = """You are checking one feature against passages from one book. This is part of a \
study; your answer is recorded as simulated judging by an AI model.

The feature (from a published checklist of statements about the ancient Maya): {feature}
{direction}

Standard: count a correspondence only if a passage below states or plainly describes the \
feature as a fact about the people or land the book describes. Silence, a vague hint, or a \
statement about some other people does not count.

Passages (found by keyword search; they may be irrelevant):
{passages}

Answer on the first line with exactly one of: SUPPORTS, CONTRADICTS, NOT_ADDRESSED.
On the second line, if SUPPORTS, the strength: SPECIFIC (stated plainly), DETAILED (stated with \
particulars), or NONE otherwise. On the third line, the number of the passage you relied on \
(or 0)."""


def build_jobs(cfg: dict) -> dict | None:
    k = keyed(cfg)
    if k is None:
        return None
    st = settings(cfg)
    items = [i for i in k["items"] if i["appendix"] in ("A", "B")]
    texts = control_texts(cfg)
    jobs, passages, per_text = [], [], {}
    for name, text in texts.items():
        if text is None:
            per_text[name] = {"state": "not attempted (text not held)"}
            continue
        n_q = n_none = 0
        for it in items:
            pat = coding.KEYWORDS.get(it["id"])
            if pat is None:
                n_none += 1
                continue
            got = candidates(text, re.compile(pat, re.I), st["window_words"], st["window_step"],
                             st["passages_per_question"])  # fmt: skip
            qid = f"{name}|{it['id']}"
            passages.append({"id": qid, "passages": got})
            if not got:
                n_none += 1
                continue
            direction = (
                "The checklist scores this as something the book should say (a positive item)."
                if it["direction"] == "positive"
                else "Here the question is whether the book asserts this thing existed."
            )
            body = "\n\n".join(f"[{n}] {p}" for n, p in enumerate(got, 1))
            jobs.append({"id": qid, "prompt": PROMPT.format(
                feature=coding.FEATURE.get(it["id"], it["label"]), direction=direction,
                passages=body)})  # fmt: skip
            n_q += 1
        per_text[name] = {"words": len(text.split()), "questions": n_q,
                          "no_keyword_hit_or_no_rule": n_none,
                          "known_answer": name == "book_of_mormon"}  # fmt: skip
    # the known-answer subset first, so the judge is checked before any control is read
    jobs.sort(key=lambda j: not j["id"].startswith("book_of_mormon|"))
    with out(PRIVATE / "jobs.jsonl").open("w", encoding="utf-8") as fh:
        for j in jobs:
            fh.write(json.dumps(j, ensure_ascii=False) + "\n")
    with out(PRIVATE / "passages.jsonl").open("w", encoding="utf-8") as fh:
        for p in passages:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    return {"questions": len(jobs), "per_text": per_text,
            "known_answer_questions": sum(j["id"].startswith("book_of_mormon|") for j in jobs),
            "labelled": "simulated judging by an AI model (not run)"}  # fmt: skip


# ------------------------------------------------------------------------------ second design
# 2026-11-23, post hoc (decided after check C missed; see the card). Candidate passages are the
# keyword windows as before plus windows found by meaning with the passage index's own model;
# the same retrieval for every text. The bars are unchanged.

JOBS2_CHECK = PRIVATE / "jobs2_check.jsonl"
JOBS2_CONTROLS = PRIVATE / "jobs2_controls.jsonl"
PASSAGES2 = PRIVATE / "passages2.jsonl"
ANSWERS = {  # design -> (jobs, answers) for the known-answer check C
    "first": (PRIVATE / "jobs_first.jsonl", PRIVATE / "answers_first.jsonl"),
    "second": (JOBS2_CHECK, PRIVATE / "answers2_check.jsonl"),
}
ANSWERS2_CONTROLS = PRIVATE / "answers2_controls.jsonl"
VERDICTS = ("SUPPORTS", "CONTRADICTS", "NOT_ADDRESSED")
BOM = "book_of_mormon"

PROMPT2 = PROMPT.replace(
    "Passages (found by keyword search; they may be irrelevant):",
    "Passages (found by keyword search and by search by meaning; they may be irrelevant):",
)


def second(cfg: dict) -> dict:
    return settings(cfg)["second_design"]


def meaning_picks(scores, size: int, step: int, keep: int, taken: list[int]) -> list[int]:
    """Indices of the ``keep`` best-scoring windows overlapping neither each other nor ``taken``."""
    chosen: list[int] = []
    for k in sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i)):
        if _overlaps(k, taken + chosen, size, step):
            continue
        chosen.append(k)
        if len(chosen) == keep:
            break
    return chosen


def retrieve(wins: list[str], vecs, query_vec, pattern: re.Pattern | None, cfg: dict) -> list[dict]:
    """The second design's passages for one item in one text, in text order: the keyword picks
    (first design) and then the picks by meaning, none overlapping."""
    st, s2 = settings(cfg), second(cfg)
    size, step = st["window_words"], st["window_step"]
    kw = [] if pattern is None else keyword_picks(wins, pattern, size, step,
                                                   s2["keyword_passages"])  # fmt: skip
    mn = meaning_picks(vecs @ query_vec, size, step, s2["meaning_passages"], kw)
    how = {**{k: "keyword" for k in kw}, **{k: "meaning" for k in mn}}
    return [{"window": k, "how": how[k], "text": wins[k]} for k in sorted(how)]


def _embedder(cfg: dict):
    """Vectors from the passage index's own model (``semantic.index_model``), normalised."""
    import numpy as np

    from semantic.index import _model

    model = _model(cfg)

    def embed(texts: list[str], question: bool = False):
        prefix = cfg["lab"]["query_prefix"] if question else ""
        v = model.encode([prefix + " ".join(t.split()) for t in texts],
                         batch_size=cfg["semantic"]["batch_size"], normalize_embeddings=True,
                         convert_to_numpy=True, show_progress_bar=False)  # fmt: skip
        return np.asarray(v, dtype=np.float32)

    return embed


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def retrieval_check(shown: dict[str, list[dict]], cfg: dict) -> dict:
    """Of the items where the diagnosis found the stating passage, how many have it shown now
    (and how many by the keyword picks alone, the first design)."""
    s2 = second(cfg)
    per = {}
    for iid, marker in s2["retrieval_markers"].items():
        ps = shown.get(iid, [])
        hit = [p["how"] for p in ps if _norm(marker) in _norm(p["text"])]
        per[iid] = {"shown": bool(hit), "by": sorted(set(hit))}
    n = len(per)
    k = sum(v["shown"] for v in per.values())
    by_kw = sum("keyword" in v["by"] for v in per.values())
    return {"items": n, "shown": k, "shown_by_keyword": by_kw,
            "share": round(k / n, 3) if n else None, "bar": s2["retrieval_bar"],
            "passed": bool(n) and k / n >= s2["retrieval_bar"], "per_item": per}  # fmt: skip


def build_jobs2(cfg: dict, embed=None) -> dict | None:
    """Write the second design's questions: the 149 check questions in their own file, then the
    controls; every item gets a question in every text (meaning always finds passages)."""
    k = keyed(cfg)
    if k is None:
        return None
    st = settings(cfg)
    items = [i for i in k["items"] if i["appendix"] in ("A", "B")]
    texts = control_texts(cfg)
    embed = embed or _embedder(cfg)
    qvecs = embed([coding.FEATURE.get(i["id"], i["label"]) for i in items], question=True)
    unquoted = _norm(bom_text(drop_quotes=True))
    check, controls, passages, per_text, shown_bom = [], [], [], {}, {}
    for name, text in texts.items():
        if text is None:
            per_text[name] = {"state": "not attempted (text not held)"}
            continue
        wins = windows(text, st["window_words"], st["window_step"])
        vecs = embed(wins)
        quoted = [_norm(w) not in unquoted for w in wins] if name == BOM else None
        how = {"keyword": 0, "meaning": 0}
        for it, q in zip(items, qvecs, strict=True):
            pat = coding.KEYWORDS.get(it["id"])
            got = retrieve(wins, vecs, q, None if pat is None else re.compile(pat, re.I), cfg)
            qid = f"{name}|{it['id']}"
            rec = {"id": qid, "windows": [p["window"] for p in got], "how": [p["how"] for p in got],
                   "passages": [p["text"] for p in got]}  # fmt: skip
            if quoted is not None:
                rec["in_quoted_chapters"] = [quoted[p["window"]] for p in got]
                shown_bom[it["id"]] = got
            passages.append(rec)
            for p in got:
                how[p["how"]] += 1
            direction = (
                "The checklist scores this as something the book should say (a positive item)."
                if it["direction"] == "positive"
                else "Here the question is whether the book asserts this thing existed."
            )
            body = "\n\n".join(f"[{n}] {p['text']}" for n, p in enumerate(got, 1))
            job = {"id": qid, "prompt": PROMPT2.format(
                feature=coding.FEATURE.get(it["id"], it["label"]), direction=direction,
                passages=body)}  # fmt: skip
            (check if name == BOM else controls).append(job)
        per_text[name] = {"words": len(text.split()), "windows": len(wins),
                          "questions": len(items), "passages_by": how,
                          "known_answer": name == BOM}  # fmt: skip
    for path, rows in ((JOBS2_CHECK, check), (JOBS2_CONTROLS, controls), (PASSAGES2, passages)):
        with out(path).open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    s2 = second(cfg)
    return {"design": "second (2026-11-23, post hoc: after check C missed)",
            "retrieval": {"keyword_passages": s2["keyword_passages"],
                          "meaning_passages": s2["meaning_passages"],
                          "model": cfg["semantic"]["index_model"]},
            "check_questions": len(check), "control_questions": len(controls),
            "per_text": per_text, "retrieval_check": retrieval_check(shown_bom, cfg),
            "labelled": "simulated judging by an AI model (not run)"}  # fmt: skip


def parse_reply(reply: str) -> dict | None:
    """First line: the verdict; third line: the passage relied on. None if unreadable."""
    lines = [ln.strip().strip("*`#. ").upper() for ln in (reply or "").strip().splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines or lines[0] not in VERDICTS:
        return None
    m = re.match(r"\[?(\d+)", lines[2]) if len(lines) > 2 else None
    return {"verdict": lines[0], "passage": int(m.group(1)) if m else 0}


def read_answers(jobs: Path, answers: Path, stage: str) -> dict:
    """Answers by id; open ids (no answer yet) and unreadable ones (raw text logged) apart.
    An unreadable reply is never counted as an answer."""
    ids = [json.loads(ln)["id"] for ln in jobs.read_text().splitlines() if ln.strip()]
    got: dict[str, dict] = {}
    bad: list[dict] = []
    if answers.exists():
        for ln in answers.read_text().splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            p = parse_reply(r.get("reply", ""))
            if p is None:
                bad.append({"id": r["id"], "reply": r.get("reply")})
            else:
                got[r["id"]] = p
    unread = sorted({b["id"] for b in bad} - set(got))
    if unread:
        log = out(LOGS / f"dalechecklist_unparsed_{stage}.jsonl")
        log.write_text("".join(json.dumps(b, ensure_ascii=False) + "\n" for b in bad
                               if b["id"] in unread))  # fmt: skip
    return {"answers": {i: got[i] for i in ids if i in got},
            "open": [i for i in ids if i not in got and i not in unread], "unreadable": unread,
            "jobs": len(ids)}  # fmt: skip


def score_check(cfg: dict, design: str) -> dict:
    """Known-answer check C from the judge's answers: SUPPORTS on the Book of Mormon for at
    least the bar share of their positives (``book_of_mormon|A:*``) and negatives (``|B:*``)."""
    st = settings(cfg)
    jobs, answers = ANSWERS[design]
    if not jobs.exists():
        return {"design": design, "refused": f"no jobs file {jobs}"}
    r = read_answers(jobs, answers, f"check_{design}")
    res = {"design": design, "jobs": r["jobs"], "answered": len(r["answers"]),
           "open": len(r["open"]), "unreadable": r["unreadable"],
           "label": "simulated judging by an AI model"}  # fmt: skip
    if r["open"] or r["unreadable"]:
        res["refused"] = "answers still open or unreadable; nothing scored"
        return res
    parts = {}
    for side, tag, bar in (("positive", "A:", st["judge_bar_positive"]),
                           ("negative", "B:", st["judge_bar_negative"])):  # fmt: skip
        mine = {i: a for i, a in r["answers"].items() if i.startswith(f"{BOM}|{tag}")}
        sup = sorted(i.split("|", 1)[1] for i, a in mine.items() if a["verdict"] == "SUPPORTS")
        n = len(mine)
        parts[side] = {"items": n, "supports": len(sup),
                       "share": round(len(sup) / n, 3) if n else None, "bar": bar,
                       "met": bool(n) and len(sup) / n >= bar,
                       "verdicts": {v: sum(a["verdict"] == v for a in mine.values())
                                    for v in VERDICTS},
                       "not_supported": sorted(i.split("|", 1)[1] for i, a in mine.items()
                                               if a["verdict"] != "SUPPORTS")}  # fmt: skip
    res.update(parts)
    res["passed"] = all(p["met"] for p in parts.values())
    return res


def score_controls(cfg: dict) -> dict:
    """Each text's supported items scored with the Dales' own ratios; refused unless check C
    (second design) passed and every control answer is in."""
    st, s2 = settings(cfg), second(cfg)
    c = score_check(cfg, "second")
    if not c.get("passed"):
        return {"refused": "check C (second design) has not passed: control scores are not "
                "reported", "check_c": c}  # fmt: skip
    if not JOBS2_CONTROLS.exists():
        return {"refused": f"no jobs file {JOBS2_CONTROLS}"}
    r = read_answers(JOBS2_CONTROLS, ANSWERS2_CONTROLS, "controls")
    if r["open"] or r["unreadable"]:
        return {"refused": "control answers still open or unreadable; nothing scored",
                "jobs": r["jobs"], "answered": len(r["answers"]), "open": len(r["open"]),
                "unreadable": r["unreadable"]}  # fmt: skip
    k = keyed(cfg)
    ratio = {i["id"]: i["ratio"] for i in k["items"]}
    quoted = {}
    for ln in PASSAGES2.read_text().splitlines():
        p = json.loads(ln)
        if "in_quoted_chapters" in p:
            quoted[p["id"]] = p["in_quoted_chapters"]
    every = {
        **read_answers(JOBS2_CHECK, ANSWERS["second"][1], "check_second")["answers"],
        **r["answers"],
    }
    texts = sorted({i.split("|", 1)[0] for i in every})

    def summary(ids: list[str]) -> dict:
        pos = [i for i in ids if i.startswith("A:")]
        neg = [i for i in ids if i.startswith("B:")]
        return {"positive_supported": len(pos), "negative_supported": len(neg),
                "log10_positive_product": round(log10_product([ratio[i] for i in pos]), 2),
                "log10_negative_product": round(log10_product([ratio[i] for i in neg]), 2),
                "positive_by_ratio": {str(x): sum(ratio[i] == x for i in pos)
                                      for x in (0.5, 0.1, 0.02)},
                "items": sorted(ids)}  # fmt: skip

    per = {}
    for t in texts:
        sup = [i.split("|", 1)[1] for i, a in every.items()
               if i.startswith(t + "|") and a["verdict"] == "SUPPORTS"]  # fmt: skip
        per[t] = summary(sup)
        if t == BOM:  # without the quotation chapters: the passage relied on lies outside them
            keep = [i for i in sup
                    if 0 < every[f"{t}|{i}"]["passage"] <= len(quoted.get(f"{t}|{i}", []))
                    and not quoted[f"{t}|{i}"][every[f"{t}|{i}"]["passage"] - 1]]  # fmt: skip
            per[t + "_without_quoted_chapters"] = summary(keep)
    lo = max(
        per[BOM]["log10_positive_product"],
        per[BOM + "_without_quoted_chapters"]["log10_positive_product"],
    )
    reach = {t: {"log10_positive_product": v["log10_positive_product"],
                 "reaches_book_of_mormon": v["log10_positive_product"] <= lo}
             for t, v in per.items() if not t.startswith(BOM)}  # fmt: skip
    return {"check_c": {k_: c[k_] for k_ in ("passed", "positive", "negative")},
            "texts": per, "book_of_mormon_weaker_end": lo, "reach": reach,
            "reach_rule": s2["reach_rule"],
            "theirs": {"spalding": st["published"]["spalding"],
                       "view_of_the_hebrews": st["published"]["view_of_the_hebrews"]},
            "label": "simulated judging by an AI model"}  # fmt: skip


def _save(key: str, value: dict) -> Path:
    prev = PUBLIC / "result.json"
    old = json.loads(prev.read_text()) if prev.exists() else {}
    old[key] = {**value, "config_sha256": config.sha256_of_config()}
    out(prev).write_text(json.dumps(old, indent=1) + "\n")
    return prev


# ------------------------------------------------------------------------------ command line


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["keys", "arith", "jobs", "jobs2", "checkc", "controls"])
    ap.add_argument("--design", choices=["first", "second"], default="second")
    a = ap.parse_args()
    cfg = config.load()
    if a.cmd == "keys":
        k = keyed(cfg)
        if k is None:
            print("not attempted: the paper is not held at", PDF)
            return
        k["note"] = ("labels are the paper's headings shortened; near_east and generic are "
                     + FROM_MEMORY)  # fmt: skip
        k["source"] = settings(cfg)["source"]
        k["config_sha256"] = config.sha256_of_config()
        out(PUBLIC / "items.json").write_text(json.dumps(k, indent=1, ensure_ascii=False) + "\n")
        print(f"{len(k['items'])} items -> {PUBLIC / 'items.json'}")
    elif a.cmd == "arith":
        res = run_arith(cfg)
        if res is None:
            print("not attempted: the paper is not held at", PDF)
            return
        prev = PUBLIC / "result.json"
        old = json.loads(prev.read_text()) if prev.exists() else {}
        old.update(res)
        out(prev).write_text(json.dumps(old, indent=1) + "\n")
        print(json.dumps(res["known_answer"]["passed"]), "->", prev)
    elif a.cmd == "jobs2":
        res = build_jobs2(cfg)
        if res is None:
            print("not attempted: the paper is not held at", PDF)
            return
        print(json.dumps({k: v for k, v in res.items() if k != "per_text"}, indent=1),
              "->", _save("control_jobs_second_design", res))  # fmt: skip
    elif a.cmd == "checkc":
        res = score_check(cfg, a.design)
        print(json.dumps({k: v for k, v in res.items() if k not in ("positive", "negative")}),
              json.dumps({s: {k: v for k, v in res[s].items() if k != "not_supported"}
                          for s in ("positive", "negative") if s in res}, indent=1))  # fmt: skip
        if "refused" in res:
            raise SystemExit(1)
        print("->", _save(f"check_c_{a.design}_design", res))
    elif a.cmd == "controls":
        res = score_controls(cfg)
        if "refused" in res:
            print("refused:", res["refused"])
            raise SystemExit(1)
        print(json.dumps(res["reach"], indent=1), "->", _save("controls_second_design", res))
    else:
        res = build_jobs(cfg)
        if res is None:
            print("not attempted: the paper is not held at", PDF)
            return
        prev = PUBLIC / "result.json"
        old = json.loads(prev.read_text()) if prev.exists() else {}
        old["control_jobs"] = res
        out(prev).write_text(json.dumps(old, indent=1) + "\n")
        print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
