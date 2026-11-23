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
``jobs3`` (third design, 2026-11-23, post hoc) drops retrieval: each text is cut into consecutive
sections and every item, with planted decoy features, is asked of every section in batches.
The test card is ``data/private/lab/owner/2026-11-21-dale-checklist/card.md``. Public files hold
labels, numbers and page numbers, never text from the paper or any book.

Usage::

    python -m lab.dalechecklist keys     # paper -> data/lab/setting/dale_checklist/items.json
    python -m lab.dalechecklist arith    # known-answer check + alternatives -> result.json
    python -m lab.dalechecklist jobs     # candidate passages + judging questions (private)
    python -m lab.dalechecklist jobs2    # second design: keyword + meaning passages (private)
    python -m lab.dalechecklist jobs3    # third design: whole texts in sections (private jobs)
    python -m lab.dalechecklist checkc [--design first|second|third]   # score check C
    python -m lab.dalechecklist controls [--design second|third]  # refused unless check C passed
    python -m lab.dalechecklist retry3 [--which check|controls]  # re-ask unreadable replies

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


# ------------------------------------------------------------------------------ third design
# 2026-11-23, post hoc (decided after check C missed and the second design's retrieval check
# missed; owner: "read the whole book"). No retrieval: every text is cut into consecutive
# sections and every item is asked of every section, in batches with planted decoys. The bars
# are unchanged; two guards against a reader who says yes too easily are added.

JOBS3_CHECK = PRIVATE / "jobs3_check.jsonl"
JOBS3_CHECK_SECOND = PRIVATE / "jobs3_check_second.jsonl"
JOBS3_CONTROLS = PRIVATE / "jobs3_controls.jsonl"
JOBS3_CONTROLS_SECOND = PRIVATE / "jobs3_controls_second.jsonl"
SECTIONS3 = PRIVATE / "sections3.jsonl"


def answers_for(jobs: Path) -> Path:
    """jobs3_x.jsonl -> answers3_x.jsonl (retry rounds: answers3_x.retryN.jsonl)."""
    return jobs.with_name(jobs.name.replace("jobs3_", "answers3_"))


def third(cfg: dict) -> dict:
    return settings(cfg)["third_design"]


def sections(text: str, size: int, overlap: int) -> list[tuple[int, int]]:
    """(start, end) word offsets: the fewest equal consecutive cores of at most ``size`` words,
    each section also carrying the last ``overlap`` words of the core before it."""
    n = len(text.split())
    k = max(1, math.ceil(n / size))
    cuts = [round(i * n / k) for i in range(k + 1)]
    return [(max(0, cuts[i] - overlap) if i else 0, cuts[i + 1]) for i in range(k)]


def batches(item_ids: list[str], decoy_ids: list[str], max_items: int, seed: int) -> list[list]:
    """The fixed batches: real items and decoys each shuffled with the seed, dealt round-robin so
    decoys spread evenly, then each batch shuffled; the same batches for every section and text."""
    import random

    rng = random.Random(seed)
    real, dec = list(item_ids), list(decoy_ids)
    rng.shuffle(real)
    rng.shuffle(dec)
    n = math.ceil((len(real) + len(dec)) / max_items)
    out_: list[list[str]] = [[] for _ in range(n)]
    for k, i in enumerate(dec):
        out_[k % n].append(i)
    for k, i in enumerate(real):
        out_[(k + len(dec)) % n].append(i)
    for b in out_:
        rng.shuffle(b)
    return out_


PROMPT3 = """Below is one section of a book (part {part} of {parts}, about {words:,} words). \
After it comes a list of features to check against it. This is part of a study; your answers \
are recorded as simulated judging by an AI model.

<section>
{text}
</section>

Read the whole section. For each feature in the list below decide:

- SUPPORTS: the section states or plainly describes the feature as a fact about the people or \
land the book describes. A feature can be plainly described by the narrative (named persons, \
places, groups or events) as well as by a general statement: a story in which travellers cross \
a river by ferry plainly describes ferries.
- CONTRADICTS: the section plainly states the opposite about those people or land.
- NOT_ADDRESSED: otherwise. Silence, a vague hint, a figure of speech, or a statement about \
some other people does not count. Most features will not be in any given section.

Judge each feature on its own.

Features:
{features}

Answer with exactly one line per feature, in the order given, and nothing else:
CODE | VERDICT | LOCATION
where VERDICT is SUPPORTS, CONTRADICTS or NOT_ADDRESSED, and LOCATION is, for SUPPORTS or \
CONTRADICTS, up to {loc} consecutive words copied exactly from the section where it is stated \
(leave it empty for NOT_ADDRESSED)."""


def _feature(i: str) -> str:
    return coding.DECOY_FEATURE[i] if i.startswith("D:") else coding.FEATURE[i]


def decoy_hits(texts: dict[str, str | None]) -> dict[str, dict[str, int]]:
    """Keyword hits of each decoy's rule in each text (all should be 0)."""
    return {name: {d_: len(re.findall(p, t, re.I)) for d_, p in coding.DECOY_KEYWORDS.items()}
            for name, t in texts.items() if t is not None}  # fmt: skip


def _sample(n_sections: int, k: int, seed: int, name: str) -> list[int]:
    import random

    rng = random.Random(f"{seed}|{name}")
    return sorted(rng.sample(range(n_sections), min(k, n_sections)))


def build_jobs3(cfg: dict) -> dict | None:
    """Write the third design's questions: the Book of Mormon check (its own file), its second-
    reader sample, then the controls and theirs. Nothing is asked here."""
    k = keyed(cfg)
    if k is None:
        return None
    s3 = third(cfg)
    items = [i["id"] for i in k["items"] if i["appendix"] in ("A", "B")]
    decoys = list(coding.DECOY_FEATURE)
    groups = batches(items, decoys, s3["max_items_per_question"], s3["seed"])
    texts = control_texts(cfg)
    files: dict[Path, list[dict]] = {JOBS3_CHECK: [], JOBS3_CHECK_SECOND: [], JOBS3_CONTROLS: [],
                                     JOBS3_CONTROLS_SECOND: []}  # fmt: skip
    secs, per_text = [], {}
    for name, text in texts.items():
        if text is None:
            per_text[name] = {"state": "not attempted (text not held)"}
            continue
        w = text.split()
        cut = sections(text, s3["section_words"], s3["section_overlap_words"])
        n_second = s3["second_reader_sections"][BOM if name == BOM else "control"]
        sample = _sample(len(cut), n_second, s3["seed"], name)
        main_f, second_f = ((JOBS3_CHECK, JOBS3_CHECK_SECOND) if name == BOM
                            else (JOBS3_CONTROLS, JOBS3_CONTROLS_SECOND))  # fmt: skip
        chars = 0
        for s, (a, b) in enumerate(cut, 1):
            secs.append({"text": name, "section": s, "start_word": a, "end_word": b})
            body = " ".join(w[a:b])
            for g, group in enumerate(groups, 1):
                feats = "\n".join(f"F{n:02d}. {_feature(i)}" for n, i in enumerate(group, 1))
                prompt = PROMPT3.format(part=s, parts=len(cut), words=b - a, text=body,
                                        features=feats, loc=s3["location_words"])  # fmt: skip
                job = {"id": f"{name}|s{s:02d}|b{g}", "prompt": prompt, "items": group}
                files[main_f].append(job)
                chars += len(prompt)
                if s - 1 in sample:
                    files[second_f].append(job)
        per_text[name] = {"words": len(w), "sections": len(cut),
                          "questions": len(cut) * len(groups),
                          "second_reader_sections": [x + 1 for x in sample],
                          "approx_input_tokens": round(chars * s3["tokens_per_char"]),
                          "known_answer": name == BOM}  # fmt: skip
    for path, rows in files.items():
        with out(path).open("w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with out(SECTIONS3).open("w", encoding="utf-8") as fh:
        for r in secs:
            fh.write(json.dumps(r) + "\n")
    tok = s3["tokens_per_char"]
    size = {p.name: {"questions": len(r), "approx_input_tokens":
                     round(sum(len(j["prompt"]) for j in r) * tok),
                     "hours_at_per_hour": round(len(r) / cfg["lab"]["judge"]["per_hour"], 2)}
            for p, r in files.items()}  # fmt: skip
    hits = decoy_hits(texts)
    return {"design": "third: whole-book reading (2026-11-23, post hoc: after check C missed "
                      "and the second design's retrieval check missed)",
            "batches": [len(g) for g in groups],
            "decoys_per_batch": [sum(i.startswith("D:") for i in g) for g in groups],
            "files": size, "per_text": per_text,
            "decoy_keyword_hits": {t: {d_: n for d_, n in h.items() if n}
                                   for t, h in hits.items()},
            "reader": s3["reader_model"], "second_reader": s3["second_reader_model"],
            "labelled": "simulated judging by an AI model (not run)"}  # fmt: skip


_LINE3 = re.compile(
    r"^\W*F(\d{1,3})\W*\|\s*\**(SUPPORTS|CONTRADICTS|NOT[_ ]ADDRESSED)\**\s*(?:\|\s*(.*))?$",
    re.I,
)


def parse_reply3(reply: str, n: int) -> list[dict] | None:
    """One verdict (and location words) per feature F01..Fn; None unless every code is answered
    once, or twice the same way."""
    got: dict[int, dict] = {}
    for ln in (reply or "").splitlines():
        m = _LINE3.match(ln.strip())
        if not m:
            continue
        k = int(m.group(1))
        v = {"verdict": m.group(2).upper().replace(" ", "_"),
             "location": (m.group(3) or "").strip().strip('"“”').strip()}  # fmt: skip
        if k in got and got[k]["verdict"] != v["verdict"]:
            return None
        got.setdefault(k, v)
    if sorted(got) != list(range(1, n + 1)):
        return None
    return [got[k] for k in range(1, n + 1)]


def read_answers3(jobs: Path, stage: str) -> dict:
    """Answers per question from ``answers3_*.jsonl`` and its retry rounds (a readable reply
    supersedes an unreadable one); open and unreadable questions apart, raw text logged."""
    js = {j["id"]: j for j in (json.loads(x) for x in jobs.read_text().splitlines() if x.strip())}
    ans = answers_for(jobs)
    got: dict[str, list[dict]] = {}
    bad: dict[str, str] = {}
    model: dict[str, str] = {}
    for f in (ans, *_retry_answers(jobs)):
        if not f.exists():
            continue
        for ln in f.read_text().splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r["id"] not in js:
                continue
            p = parse_reply3(r.get("reply", ""), len(js[r["id"]]["items"]))
            if p is None:
                bad.setdefault(r["id"], r.get("reply"))
            else:
                got[r["id"]] = p
                model[r["id"]] = r.get("model", "")
    unread = sorted(set(bad) - set(got))
    if unread:
        log = out(LOGS / f"dalechecklist_unparsed_{stage}.jsonl")
        log.write_text("".join(json.dumps({"id": i, "reply": bad[i]}, ensure_ascii=False) + "\n"
                               for i in unread))  # fmt: skip
    return {"jobs": js, "answers": got, "open": [i for i in js if i not in got and i not in bad],
            "unreadable": unread, "models": sorted(set(model.values()))}  # fmt: skip


def _norm3(s: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def per_item(r: dict) -> dict[str, dict]:
    """text|item -> sections that SUPPORT (with location words) and that CONTRADICT."""
    res: dict[str, dict] = {}
    for qid, verdicts in r["answers"].items():
        text, sec, _ = qid.split("|")
        for item, v in zip(r["jobs"][qid]["items"], verdicts, strict=True):
            e = res.setdefault(f"{text}|{item}", {"supports": [], "contradicts": []})
            if v["verdict"] == "SUPPORTS":
                e["supports"].append((sec, v["location"]))
            elif v["verdict"] == "CONTRADICTS":
                e["contradicts"].append(sec)
    return res


def kappa(a: list[bool], b: list[bool]) -> float | None:
    """Cohen's kappa for two yes/no readings of the same units."""
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1:  # both readers gave one answer throughout: agreement is total but uninformative
        return 1.0 if po == 1 else 0.0
    return round((po - pe) / (1 - pe), 3)


def agreement(main: dict, second_: dict, text_prefix: str | None = None) -> dict:
    """Reader against second reader on the same questions: kappa over (real item x section)
    units, SUPPORTS against anything else; decoys counted apart."""
    a, b, dec = [], [], {"reader": 0, "second_reader": 0, "units": 0}
    for qid, v2 in second_["answers"].items():
        if text_prefix and not qid.startswith(text_prefix + "|"):
            continue
        v1 = main["answers"].get(qid)
        if v1 is None:
            continue
        for item, x, y in zip(main["jobs"][qid]["items"], v1, v2, strict=True):
            if item.startswith("D:"):
                dec["units"] += 1
                dec["reader"] += x["verdict"] == "SUPPORTS"
                dec["second_reader"] += y["verdict"] == "SUPPORTS"
            else:
                a.append(x["verdict"] == "SUPPORTS")
                b.append(y["verdict"] == "SUPPORTS")
    return {"units": len(a), "reader_supports": sum(a), "second_reader_supports": sum(b),
            "agree": sum(x == y for x, y in zip(a, b, strict=True)), "kappa": kappa(a, b),
            "decoy_supports": dec}  # fmt: skip


def text_summary(name: str, items: dict[str, dict], ratio: dict, cfg: dict) -> dict:
    """One text's tally: supported positives, negatives, decoys (any-section rule)."""
    s3 = third(cfg)
    mine = {k.split("|", 1)[1]: v for k, v in items.items() if k.startswith(name + "|")}
    sup = sorted(i for i, v in mine.items() if v["supports"])
    pos = [i for i in sup if i.startswith("A:")]
    neg = [i for i in sup if i.startswith("B:")]
    dec = [i for i in sup if i.startswith("D:")]
    n_dec = sum(i.startswith("D:") for i in mine)
    rejected = (n_dec - len(dec)) / n_dec if n_dec else None
    both = sorted(i for i, v in mine.items() if v["supports"] and v["contradicts"])
    return {"positive_supported": len(pos), "negative_supported": len(neg),
            "decoys_supported": dec, "decoy_rejection": None if rejected is None
            else round(rejected, 3), "decoy_bar": s3["decoy_bar"],
            "decoy_guard_met": rejected is not None and rejected >= s3["decoy_bar"],
            "supported_and_contradicted": both,
            "log10_positive_product": round(log10_product([ratio[i] for i in pos]), 2),
            "log10_negative_product": round(log10_product([ratio[i] for i in neg]), 2),
            "positive_by_ratio": {str(x): sum(ratio[i] == x for i in pos)
                                  for x in (0.5, 0.1, 0.02)},
            "items": pos + neg}  # fmt: skip


def _refuse_open(stage: str, r: dict) -> dict | None:
    if r["open"] or r["unreadable"]:
        return {"refused": f"{stage}: answers still open or unreadable; nothing scored",
                "questions": len(r["jobs"]), "answered": len(r["answers"]),
                "open": len(r["open"]), "unreadable": r["unreadable"]}  # fmt: skip
    return None


def score_check3(cfg: dict) -> dict:
    """Check C, third design: SUPPORTS (in any section) for the bar share of the 131 positives
    and of the 18 negatives, the decoys rejected at their bar, and the second reader agreeing
    at its bar on the sampled sections. Refuses while any of these answers is open."""
    st, s3 = settings(cfg), third(cfg)
    for f in (JOBS3_CHECK, JOBS3_CHECK_SECOND):
        if not f.exists():
            return {"design": "third", "refused": f"no jobs file {f}"}
    r = read_answers3(JOBS3_CHECK, "check_third")
    r2 = read_answers3(JOBS3_CHECK_SECOND, "check_third_second")
    for stage, x in (("check", r), ("second reader", r2)):
        no = _refuse_open(stage, x)
        if no:
            return {"design": "third", **no, "label": "simulated judging by an AI model"}
    items = per_item(r)
    ratio = {i["id"]: i["ratio"] for i in keyed(cfg)["items"]}
    summ = text_summary(BOM, items, ratio, cfg)
    n_pos = sum(k.startswith(f"{BOM}|A:") for k in items)
    n_neg = sum(k.startswith(f"{BOM}|B:") for k in items)
    parts = {}
    for side, n, k_, bar in (("positive", n_pos, summ["positive_supported"],
                              st["judge_bar_positive"]),
                             ("negative", n_neg, summ["negative_supported"],
                              st["judge_bar_negative"])):  # fmt: skip
        parts[side] = {"items": n, "supports": k_, "share": round(k_ / n, 3) if n else None,
                       "bar": bar, "met": bool(n) and k_ / n >= bar}  # fmt: skip
    agr = agreement(r, r2)
    parts["decoys"] = {"items": len(coding.DECOY_FEATURE),
                       "supported": summ["decoys_supported"],
                       "rejection": summ["decoy_rejection"], "bar": s3["decoy_bar"],
                       "met": summ["decoy_guard_met"]}  # fmt: skip
    parts["second_reader"] = {**agr, "bar": s3["second_reader_kappa_bar"],
                              "met": agr["kappa"] is not None
                              and agr["kappa"] >= s3["second_reader_kappa_bar"],
                              "models": {"reader": r["models"],
                                         "second_reader": r2["models"]}}  # fmt: skip
    real = [k.split("|", 1)[1] for k in items if k.startswith(BOM + "|") and "|D:" not in k]
    return {"design": "third (whole-book reading; post hoc)", "questions": len(r["jobs"]),
            **parts, "passed": all(p["met"] for p in parts.values()),
            "not_supported": sorted(i for i in real if not items[f"{BOM}|{i}"]["supports"]),
            "supported_and_contradicted": summ["supported_and_contradicted"],
            "rule": s3["rule"], "label": "simulated judging by an AI model"}  # fmt: skip


def outside_quotes(items: dict[str, dict], unquoted: str) -> dict[str, str]:
    """For each supported Book of Mormon item: 'outside' if any supporting location's words are
    found in the text without the Bible-quotation chapters, else 'inside' or 'unlocated' (the
    words found in no section: not counted outside)."""
    res = {}
    full = _norm3(bom_text(drop_quotes=False))
    for k, v in items.items():
        if not k.startswith(BOM + "|") or not v["supports"]:
            continue
        locs = [_norm3(loc) for _, loc in v["supports"] if _norm3(loc)]
        if any(loc in unquoted for loc in locs):
            res[k.split("|", 1)[1]] = "outside"
        elif any(loc in full for loc in locs):
            res[k.split("|", 1)[1]] = "inside"
        else:
            res[k.split("|", 1)[1]] = "unlocated"
    return res


def score_controls3(cfg: dict) -> dict:
    """Each control scored as the Book of Mormon was; refused unless check C (third design)
    passed and every control answer (both readers) is in. A control whose own decoys are not
    rejected at the bar is not compared."""
    s2, s3 = second(cfg), third(cfg)
    c = score_check3(cfg)
    if not c.get("passed"):
        return {"refused": "check C (third design) has not passed: control scores are not "
                "reported", "check_c": c}  # fmt: skip
    for f in (JOBS3_CONTROLS, JOBS3_CONTROLS_SECOND):
        if not f.exists():
            return {"refused": f"no jobs file {f}"}
    r = read_answers3(JOBS3_CONTROLS, "controls_third")
    r2 = read_answers3(JOBS3_CONTROLS_SECOND, "controls_third_second")
    for stage, x in (("controls", r), ("controls second reader", r2)):
        no = _refuse_open(stage, x)
        if no:
            return no
    rb = read_answers3(JOBS3_CHECK, "check_third")
    ratio = {i["id"]: i["ratio"] for i in keyed(cfg)["items"]}
    items = {**per_item(rb), **per_item(r)}
    texts = sorted({k.split("|", 1)[0] for k in items})
    per = {t: text_summary(t, items, ratio, cfg) for t in texts}
    where = outside_quotes(items, _norm3(bom_text(drop_quotes=True)))
    b = per[BOM]
    keep = [i for i in b["items"] if where.get(i) == "outside"]
    per[BOM + "_without_quoted_chapters"] = {
        "positive_supported": sum(i.startswith("A:") for i in keep),
        "negative_supported": sum(i.startswith("B:") for i in keep),
        "log10_positive_product": round(log10_product([ratio[i] for i in keep
                                                       if i.startswith("A:")]), 2),
        "located": {s: sum(v == s for v in where.values())
                    for s in ("outside", "inside", "unlocated")}, "items": keep}  # fmt: skip
    lo = max(b["log10_positive_product"],
             per[BOM + "_without_quoted_chapters"]["log10_positive_product"])  # fmt: skip
    reach = {}
    for t, v in per.items():
        if t.startswith(BOM):
            continue
        reach[t] = {"log10_positive_product": v["log10_positive_product"],
                    "decoy_guard_met": v["decoy_guard_met"],
                    "second_reader": agreement(r, r2, t),
                    "reaches_book_of_mormon": (
                        v["log10_positive_product"] <= lo if v["decoy_guard_met"]
                        else "not compared: decoys not rejected at the bar")}  # fmt: skip
    st = settings(cfg)
    return {"check_c": {k_: c[k_] for k_ in ("passed", "positive", "negative", "decoys",
                                             "second_reader")},
            "texts": per, "book_of_mormon_weaker_end": lo, "reach": reach,
            "reach_rule": s2["reach_rule"], "rule": s3["rule"],
            "theirs": {"spalding": st["published"]["spalding"],
                       "view_of_the_hebrews": st["published"]["view_of_the_hebrews"]},
            "label": "simulated judging by an AI model"}  # fmt: skip


def _retry_answers(jobs: Path) -> list[Path]:
    ans = answers_for(jobs)
    return sorted(ans.parent.glob(ans.stem + ".retry*.jsonl"))


def write_retry3(which: str) -> dict:
    """Questions whose every reply so far was unreadable, to a new retry round: jobs file
    ``jobs3_x.retryN.jsonl``, answers to ``answers3_x.retryN.jsonl`` (the judge skips ids already
    in an answers file, so each round has its own). Nothing earlier is overwritten."""
    res = {}
    for jobs in ((JOBS3_CHECK, JOBS3_CHECK_SECOND) if which == "check"
                 else (JOBS3_CONTROLS, JOBS3_CONTROLS_SECOND)):  # fmt: skip
        if not jobs.exists():
            continue
        r = read_answers3(jobs, f"retry_{jobs.stem}")
        if not r["unreadable"]:
            continue
        n = len(_retry_answers(jobs)) + 1
        retry_jobs = jobs.with_suffix(f".retry{n}.jsonl")
        with out(retry_jobs).open("w", encoding="utf-8") as fh:
            for i in r["unreadable"]:
                fh.write(json.dumps(r["jobs"][i], ensure_ascii=False) + "\n")
        retry_ans = answers_for(jobs).with_suffix(f".retry{n}.jsonl")
        out(retry_ans).touch()
        res[retry_jobs.name] = {"questions": len(r["unreadable"]), "answers_to": retry_ans.name}
    return res


def _save(key: str, value: dict) -> Path:
    prev = PUBLIC / "result.json"
    old = json.loads(prev.read_text()) if prev.exists() else {}
    old[key] = {**value, "config_sha256": config.sha256_of_config()}
    out(prev).write_text(json.dumps(old, indent=1) + "\n")
    return prev


# ------------------------------------------------------------------------------ command line


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["keys", "arith", "jobs", "jobs2", "jobs3", "checkc", "controls",
                                    "retry3"])  # fmt: skip
    ap.add_argument("--design", choices=["first", "second", "third"], default="second")
    ap.add_argument("--which", choices=["check", "controls"], default="check")
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
    elif a.cmd == "jobs3":
        res = build_jobs3(cfg)
        if res is None:
            print("not attempted: the paper is not held at", PDF)
            return
        print(json.dumps({k: v for k, v in res.items() if k != "per_text"}, indent=1),
              "->", _save("control_jobs_third_design", res))  # fmt: skip
    elif a.cmd == "retry3":
        print(json.dumps(write_retry3(a.which), indent=1))
    elif a.cmd == "checkc" and a.design == "third":
        res = score_check3(cfg)
        print(json.dumps({k: v for k, v in res.items() if k != "not_supported"}, indent=1))
        if "refused" in res:
            raise SystemExit(1)
        print("->", _save("check_c_third_design", res))
    elif a.cmd == "controls" and a.design == "third":
        res = score_controls3(cfg)
        if "refused" in res:
            print("refused:", res["refused"])
            raise SystemExit(1)
        print(json.dumps(res["reach"], indent=1), "->", _save("controls_third_design", res))
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
