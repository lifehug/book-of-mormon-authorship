"""BOM-109 second design: the Manchester library sensitivity (card amendment 1, 2026-11-22).

The card's 1820s picture is a rule-drawn set of library works; its sensitivity restricts that set
to "what was at hand": the titles of the Manchester (New York) library, a few miles from the
Smith farm, as Robert Paul published them ("Joseph Smith and the Manchester (New York) Library",
*BYU Studies* 22/3, 1982; private copy, ``lab.sources``). Paul numbers the books in the order the
library bought them; accessions 1 to ``manchester_accession_max`` (275) were bought by 1830 (his
note 7). We keyed each of those entries as author surname, a title pattern and the year he gives
(``ENTRIES``; our short forms, bibliographic facts only); an entry he could give only a word or two
for is "unkeyable" and not matched. Each keyed entry is matched to the library by
``lab.threeworlds2_vogel.match_works`` (any edition printed by ``manchester_year_max``): matched,
ambiguous (a title-only entry that fits works by several authors; not used) or unmatched.

Two readings of the sensitivity, both fixed before any three-worlds answer existed:

(a) *The card's words*: the 1820s rows keep only the texts that are Manchester titles. Said in
    advance: almost none of the 1820s set is in the Manchester list (only Seaver's *Mary Jemison*,
    in the contemporary-Indians row, which is reported and not pooled), so (a) is expected to leave
    the 1820s world unsettled on every feature; that is reported as it falls, not repaired.
(b) *The Manchester holdings as the 1820s row*: every matched Manchester title not already a
    three-worlds text gets the rule-drawn set's subject question (``SUBJECT_PROMPT``, simulated
    judging by an AI model); those answered A, B or C (ancient America, Indian origins, a story of
    ancient America) form one row, ``manchester``, whose mentions are judged as every other
    text's; D (Indians of the author's own day) is reported, not pooled. The 1820s world value is
    then that row alone.

Each variant replaces the 1820s column, re-selects the kept features and re-scores the Book of
Mormon by ``lab.threeworlds2.score_book``; nothing runs unless the main run's checks have passed
(``lab.threeworlds2.evaluate``). The main result is not changed.

Usage::

    python -m lab.threeworlds2_manchester match        # Paul's accessions matched (1 min)
    python -m lab.threeworlds2_manchester jobs         # subject questions, then mentions (5 min)
    python -m lab.threeworlds2_manchester sensitivity  # (a) and (b) from the answers (5 min)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

from lab import door
from lab import threeworlds2 as tw
from lab import threeworlds2_vogel as vg
from lab.paths import out
from metadata import config

OUT = tw.OUT
CARD = tw.CARD
AM = tw.AM
LABEL = "Manchester (New York) library titles to 1830 as keyed by us from Paul 1982"
SIMULATED = "SIMULATED JUDGING BY AN AI MODEL (lab.judge; BOM-109 Manchester sensitivity)"

# (accession(s), author surname pattern or None, title pattern or None, year Paul gives or None)
# None title: Paul gives too little to identify the book ("unkeyable"). Accession 265 is not in
# his list. Repeated titles (114/130, 110/146, 50/174, 170/190, 115/197-198, 180/267) are kept as
# he lists them.
ENTRIES: list[tuple[str, str | None, str | None, int | None]] = [
    ("1", "voltaire", r"charles (xii|the twelfth)", 1811),
    ("2", "nares", r"thinks.i.to.myself|i says,? says i", 1812),
    ("3", "gass", r"journal of the voyages", 1811),
    ("4-5", "cowper", r"poems", 1812),
    ("6-7", "silliman", r"journal of travels in england", 1812),
    ("8", None, r"letters of junius|junius'?s? letters", 1807),
    ("9", "jefferson", r"notes on the state of virginia", 1803),
    ("10", "weld", r"life of benjamin franklin", 1786),
    ("11-12", "irving|knickerbocker", r"history of new.york", 1812),
    ("13-14", "ramsay", r"history of the american revolution", 1811),
    ("15", "goldsmith", r"history of greece|grecian history", 1787),
    ("16", "goldsmith", r"history of england", 1808),
    ("17", "goldsmith", r"history of rome|roman history", 1772),
    ("18", "morse", r"history of new.england", 1809),
    ("19", "ramsay", r"life of george washington", 1807),
    ("20", "mackenzie", r"voyages from montreal", 1802),
    ("21", None, None, None),
    ("22", "more", r"practical piety", 1812),
    ("23-24", "roche", r"children of the abbey", None),
    ("25", None, r"laughable budget", 1820),
    ("26-33", "addison|steele", r"^(the )?spectator", 1810),
    ("34", "foxe?,", r"martyrs", 1811),
    ("35-36", "jay", r"short discourses", 1812),
    ("37", "smellie", r"philosophy of natural history", 1808),
    ("38", "fessenden", r"original poems", 1806),
    ("39-40", "johnson", r"\bidler\b", 1803),
    ("41", "goldsmith", r"vicar of wakefield", 1823),
    ("42-43", "morse", r"american universal geography", 1812),
    ("44", "arrowsmith", r"general atlas", 1812),
    ("45", "baldwin|godwin", r"fables,? ancient and modern", 1812),
    ("46", "baker", r"manual", 1800),
    ("47", "fuller", r"gospel its own witness", 1803),
    ("48", "arndt|arnd", r"true christianity", 1809),
    ("49", "bunyan", r"pilgrim'?s progress", 1804),
    ("50", "butler", r"sketches of universal history", 1822),
    ("51", None, r"guide to domestic happiness", 1807),
    ("52-59", "rollin", r"ancient history", 1812),
    ("60", None, None, None),
    ("61", "murray", r"sequel to the english reader", 1810),
    ("62", "murray", r"power of religion on the mind", 1802),
    ("63", "backus", r"doctrine of regeneration", 1800),
    ("64", "baxter", r"saints'? everlasting rest", 1802),
    ("65", "mason", r"self.knowledge", 1793),
    ("66-69", None, None, None),
    ("70", "l.estrange|seneca", r"seneca'?s morals", 1800),
    ("71", "park", r"travels in the interior", 1813),
    ("72", "spafford", r"gazetteer of the state of new.york", 1813),
    ("73", None, r"life of (the late )?(gen(eral|\.)? )?william eaton", 1813),
    ("74-79", "pope", r"^(the )?(poetical )?works", 1804),
    ("80-81", "curran", r"^(the )?speeches", 1811),
    ("82", "temple", r"irish rebellion", 1812),
    ("83-84", "cook", r"voyage towards the south pole", 1784),
    ("85", "goldsmith", r"natural history", 1810),
    ("86", "laverne", r"souvarof|suworow|suvorov", 1814),
    ("87", "svin", r"moreau", 1814),
    ("88-89", "clarke?,", r"travels in various countries", 1813),
    ("90", "porter", r"campaign in russia", 1814),
    ("91-92", "locke", r"concerning human understanding", 1813),
    ("93", "clark", r"naval history of the united states", 1813),
    ("94", "ramsay", r"travels of cyrus", 1814),
    ("95", "clarke", r"history of the war", 1817),
    ("96-97", "clarkson", r"william penn", 1814),
    ("98-100", "clarkson", r"portraiture of quakerism", 1806),
    ("101", "foster", r"essays,? in a series of letters", 1807),
    ("102", "low", r"poems", 1800),
    ("103", "honeywood", r"poems", 1801),
    ("104", "duncan", r"elements of logic", 1804),
    ("105", "taylor", r"stenography", 1810),
    ("106", "hofland", r"son of a genius", 1814),
    ("107", "scott", r"lay of the last minstrel", 1811),
    ("108-109", "porter", r"thaddeus of warsaw", 1810),
    ("110", "montolieu", r"caroline (of|de) lichtfield", 1815),
    ("111", "waterhouse|westerhouse", r"journal,? of a young man of massachusetts", 1816),
    ("112-113", None, r"montalbert", None),
    ("114", "riley", r"loss of the american brig commerce", 1817),
    ("115", "hall", r"extracts from a journal", 1824),
    ("116", "labaume", r"campaign in russia", 1817),
    ("117-118", "porter", r"scottish chiefs", 1816),
    ("119", "humboldt", r"personal narrative|travels and researches", None),
    ("120", "adams", r"flowers of ancient history", 1796),
    ("121", "kimball", r"naval temple", 1816),
    ("122", "burroughs", r"memoirs of (the notorious )?stephen burroughs", 1811),
    ("123", "brown", r"western gazetteer", 1817),
    ("124", "morse", r"history of america", 1819),
    ("125", None, None, None),
    ("126", "salzmann", r"elements of morality", 1811),
    ("127-128", None, r"sketches of modern life", 1799),
    ("129", "fletcher", r"religious controversy", 1808),
    ("130", "riley", r"loss of the american brig commerce", 1817),
    ("131", "adams", r"dictionary of all religions|view of religions", 1817),
    ("132", None, r"haddock", None),
    ("133", "tooke", r"pantheon", 1803),
    ("134", None, r"robert boyle|boyle'?s voyages", None),
    ("135", None, r"samuel patterson", 1817),
    ("136", "radcliffe", r"romance of the forest", 1806),
    ("137-138", "woodworth", r"champions of freedom", 1816),
    ("139", None, r"beaut(y|ies) of poetry", 1814),
    ("140", "sampson", r"brief remarks on the ways of man", 1823),
    ("141", "nelson", r"practice of true devotion", 1812),
    ("142", "tuke", r"george fox", 1815),
    ("143", "savage", r"poetical works", 1805),
    ("144", "montgomery", r"wanderer of switzerland", 1806),
    ("145", "bennett", r"letters to a young lady", 1829),
    ("146", "montolieu", r"caroline (of|de) lichtfield", 1815),
    ("147", "johnson", r"rasselas|prince of abyssinia", 1798),
    ("148", "sampson", r"youth'?s companion", 1816),
    ("149", "woods", r"harriet newell", 1818),
    ("150", None, None, None),
    ("151", None, r"christian companion in his field", 1814),
    ("152", "meikle", r"solitude sweetened", 1803),
    ("153", "wright", r"life of our blessed lord", 1814),
    ("154", "campbell", r"travels in south (africa|america)", 1816),
    ("155", None, r"anecdotes of peter the great", None),
    ("156", "zimmerman", r"solitude", 1804),
    ("157", "woodbury", r"fanny woodbury", None),
    ("158", "baxter", r"call to the unconverted", 1818),
    ("159-165", None, r"literary and philosophical repertory", 1815),
    ("166-167", "goldsmith|phillips", r"manners,? customs,? and curiosities of nations", 1822),
    ("168", None, None, None),
    ("169", "marcet", r"conversations (on|in) natural philosophy", 1821),
    ("170", "goodrich", r"history of the united states", 1824),
    ("171", "mead", r"almost christian", 1815),
    ("172", "sedgwick", r"new.england tale", 1822),
    ("173", "young", r"night thoughts|the complaint", 1818),
    ("174", "butler", r"sketches of universal history", 1822),
    ("175-176", "cooper", r"\bthe spy\b", 1822),
    ("177", "morse", r"american gazetteer", 1797),
    ("178", "hervey|harvey", r"meditations and contemplations", 1814),
    ("179", "lothrop", r"juvenile philosopher", 1823),
    ("180", "horry|weems", r"francis marion", 1823),
    ("181-186", "josephus", r"works", 1806),
    ("187", "lyon, g", r"private journal|narrative|journey", None),
    ("188-189", "cooper", r"\bpioneers\b", 1823),
    ("190", "goodrich", r"history of the united states", 1824),
    ("191", None, r"charlotte and leopold", 1818),
    ("192", "seaver", r"mary jemison|mrs\.? mary", 1826),
    ("193", "scott", r"lady of the lake", 1816),
    ("194-196", "montgomery", r"poetical works", 1821),
    ("197-198", "hall", r"extracts from a journal", 1824),
    ("199", "heckewelder", r"mission of the united brethren", 1820),
    ("200", None, None, None),
    ("201", "defoe", r"robinson crusoe", 1719),
    ("202-203", "newton", r"letters and sermons", 1797),
    ("204", "wilberforce", r"practical view of the prevailing religious system", 1799),
    ("205", None, r"memoirs of (general )?la ?fayette", 1825),
    ("206", "hudson", r"jemima wilkinson", 1821),
    ("207", "kenrick", r"whole duty of woman", 1821),
    ("208", "priest", r"wonders of nature", 1825),
    ("209", None, None, None),
    ("210", None, r"blue laws", None),
    ("211-212", None, None, None),
    ("213-216", "cervantes", r"don quixote", 1825),
    ("217-221", "goldsmith", r"miscellaneous works", 1816),
    ("222-223", None, None, None),
    ("224", None, r"sir william wallace", 1791),
    ("225-229", "goldsmith", r"history of the earth,? and animated nature", 1823),
    ("230-234", "montagu", r"works", 1803),
    ("235-236", None, r"board of agriculture of the state of new.york", 1821),
    ("237", None, r"pierre and his family", None),
    ("238", "denham", r"narrative of travels and discoveries", 1826),
    ("239-241", "shoberl", r"turkey", 1829),
    ("242", None, r"fire.side stories", 1827),
    ("243", "emerson", r"letters from the (a|ae|æ)gean", 1829),
    ("244", "dick", r"philosophy of a future state", 1829),
    ("245", "dick", r"christian philosopher", 1826),
    ("246-247", "shipp", r"military career of john shipp", 1829),
    ("248", "irving", r"christopher columbus", 1829),
    ("249-250", "scott", r"anne of geierstein", 1829),
    ("251-252", "scott", r"\bthe pirate\b", None),
    ("253", "murray", r"tour in italy", 1824),
    ("254", "howard", r"beauties of literature", None),
    ("255", None, None, None),
    ("256", "combe", r"devil upon two sticks", 1811),
    ("257-258", None, r"arabian nights", 1826),
    ("259", "venn", r"mistakes in religion", 1810),
    ("260-261", None, r"george barnwell", 1810),
    ("262", "howe", r"greek revolution", 1828),
    ("263-264", "cooper", r"lionel lincoln", 1824),
    ("266", "hume", r"history of england", 1827),
    ("267", "horry|weems", r"francis marion", 1823),
    ("268", None, r"life of napoleon", 1815),
    ("269", "paley", r"moral and political philosophy", 1822),
    ("270", "tytler", r"elements of general history", 1827),
    ("271", "waldo", r"stephen decatur", 1822),
    ("272", "church", r"philip'?s war", 1827),
    ("273", "nicholson", r"farmer'?s assistant", 1815),
    ("274", "opie", r"illustrations of lying", None),
    ("275", "grimshawe", r"leigh richmond", 1830),
]

# Three-worlds texts that are Manchester titles (by hand at keying, 2026-11-22: only Seaver's
# Jemison, accession 192; Heckewelder's 1819 *Account* is not his 1820 *Narrative*, accession 199).
NAMED = {"seaver_jemison_1826": "192"}


def settings(cfg: dict) -> dict:
    return tw.settings(cfg)


def first_accession(acc: str) -> int:
    return int(acc.split("-")[0])


def cmd_match(cfg: dict) -> dict:
    s = settings(cfg)
    reg, cat = vg.library_rows()
    rows, n_acc = {}, Counter()
    for acc, sur, title, year in ENTRIES:
        if first_accession(acc) > s["manchester_accession_max"]:
            continue
        a, _, b = acc.partition("-")
        vols = int(b or a) - int(a) + 1
        if title is None:
            rows[acc] = {"state": "unkeyable", "volumes": vols}
        else:
            m = vg.match_works(sur, title, s["manchester_year_max"], reg, cat)
            rows[acc] = {"state": m["state"], "volumes": vols, "paul_year": year,
                         "clusters": m["clusters"], "earliest": m["earliest"]}  # fmt: skip
        n_acc[rows[acc]["state"]] += vols
    states = Counter(v["state"] for v in rows.values())
    return {"label": LABEL, "entries": len(rows), "by_state_entries": dict(states),
            "by_state_accessions": dict(n_acc), "accessions": sum(n_acc.values()),
            "named_texts_in_list": NAMED, "matches": rows}  # fmt: skip


def manchester_works(match: dict) -> dict[str, str]:
    """work id -> accession, for matched entries (every copy and volume of the matched work)."""
    got = {}
    for acc, v in match["matches"].items():
        if v["state"] == "matched":
            for wids in v["clusters"].values():
                for w in wids:
                    got.setdefault(w, acc)
    return got


def picks(match: dict, reg: list[dict]) -> dict[str, str]:
    """accession -> the one work read for it (reading b): the longest held copy or volume of
    the matched work (the rule-drawn set's rule); repeated titles share a work."""
    words = {r["work_id"]: r["words"] or 0 for r in reg}
    got = {}
    for acc, v in match["matches"].items():
        if v["state"] == "matched":
            ws = [w for c in v["clusters"].values() for w in c]
            got[acc] = max(ws, key=lambda w: (words.get(w, 0), w))
    return got


def subject_answers() -> dict[str, str]:
    raw = tw.load_answers([CARD / "answers_manchester_subject.jsonl"])
    got = {}
    for k, v in raw.items():
        p = tw.parse_letter(v, "ABCDE")
        if p is None:
            tw.log_unparsed(k, v)
        else:
            got[k] = p
    return got


def text_work_ids(texts: list[dict]) -> dict[str, str]:
    """work id -> three-worlds text name, for texts read from the library."""
    return {t["source"][4:]: t["name"] for t in texts if t["source"].startswith("lib:")}


def manchester_texts(cfg: dict, texts: list[dict], match: dict) -> list[dict]:
    """The Manchester row of reading (b): one work per matched entry (``picks``), entries whose
    work is already a three-worlds text left out, with their subject answers (A-C pooled as
    ``manchester``, D reported, E and open left out)."""
    s = settings(cfg)
    already = text_work_ids(texts)
    in_set = {acc for w, acc in manchester_works(match).items() if w in already}
    ans = subject_answers()
    rows, seen = [], set()
    reg, _cat = vg.library_rows()
    for acc, wid in sorted(picks(match, reg).items(), key=lambda kv: first_accession(kv[0])):
        if acc in in_set or wid in seen:
            continue
        seen.add(wid)
        a = ans.get(f"msubject|{wid}")
        row = {"A": "manchester", "B": "manchester", "C": "manchester",
               "D": "manchester_contemporary_indians"}.get(a or "")  # fmt: skip
        rows.append({"name": f"manchester|{wid}", "role": "reference", "world": AM, "row": row,
                     "source": "lib:" + wid, "accession": acc, "subject_answer": a,
                     "subject": s["subjects"]["indians_now" if a == "D" else
                                              "ancient_america"]})  # fmt: skip
    return rows


def cmd_jobs(cfg: dict) -> dict:
    """jobs_manchester_subject.jsonl: one subject question per matched Manchester work not
    already a three-worlds text. jobs_manchester.jsonl: the sampled mentions of those answered
    A-D (empty until the subject answers exist)."""
    s = settings(cfg)
    match = cmd_match(cfg)
    texts = tw.all_texts(cfg, tw.subject_answers())
    tw._named(cfg)
    subj, ment = [], []
    labels = {f: v[0] for f, v in tw.feat.FEATURES.items()}
    for t in manchester_texts(cfg, texts, match):
        segs = tw.segments_of(t, cfg)
        if segs is None:
            continue
        wid = t["source"][4:]
        if t["subject_answer"] is None:
            words = " ".join(segs[0][1].split()[: s["subject_words"]])
            title = " ".join((door.catalog({wid}).get(wid, {}).get("title") or "").split())
            q = tw.SUBJECT_PROMPT.format(title=title, opening=words)
            subj.append({"id": f"msubject|{wid}", "prompt": q})
        if t["row"] is None:
            continue
        m = tw.mentions_of(t["name"], segs, cfg)
        for x in m["sample"]:
            q = tw.prompt_first(labels[x["feature"]], t["subject"], x["passage"])
            ment.append({"id": x["id"], "prompt": q})
    out(CARD / "jobs_manchester_subject.jsonl").write_text(
        "".join(json.dumps(j) + "\n" for j in subj)
    )
    out(CARD / "jobs_manchester.jsonl").write_text("".join(json.dumps(j) + "\n" for j in ment))
    per_hour = cfg["lab"]["judge"]["per_hour"]
    in_set = [w for w in manchester_works(match) if w in text_work_ids(texts)]
    return {"label": LABEL, "simulated": SIMULATED + "; prepared, not run",
            "subject_questions": len(subj), "mention_questions": len(ment),
            "hours_at_per_hour": round((len(subj) + len(ment)) / per_hour, 1),
            "per_hour": per_hour, "model": s["judge_model"],
            "manchester_works_already_three_worlds_texts": in_set,
            "order": "subject questions first; then `jobs` writes the mentions"}  # fmt: skip


def variant(texts: list[dict], states: dict[str, dict], am_rows: dict[str, tuple[str, str]],
            pooled: list[str], ments: dict, answers: dict, cfg: dict) -> dict:  # fmt: skip
    """World values with the 1820s column built from ``am_rows`` (pooling ``pooled``), the kept
    features, and the book scored against them."""
    c2 = json.loads(json.dumps(cfg))
    c2["lab"]["three_worlds2"]["rows_pooled"][AM] = pooled
    rows = {n: wr for n, wr in tw.world_rows(texts).items() if wr[0] != AM}
    rows.update(am_rows)
    values = tw.world_values(states, rows, c2)
    keep, dropped = tw.kept_features(values)
    am_settled = sorted(f for f, v in values.items() if v[AM]["value"] != "unsettled")
    book = tw.score_book(ments, answers, values, keep, c2)
    return {"am_texts": sorted(am_rows), "am_settled_features": am_settled,
            "features_kept": keep, "dropped": dropped,
            "book_verdict": book.get("verdict") if isinstance(book, dict) else book,
            "book": book}  # fmt: skip


def cmd_sensitivity(cfg: dict) -> dict:
    texts, ments = tw.collect(cfg)
    meta = json.loads((CARD / "jobs_meta.json").read_text())
    answers = tw.all_answers()
    answers.update(tw.load_answers([CARD / "answers_manchester.jsonl"]))
    ev = tw.evaluate(texts, ments, answers, meta, cfg)
    res = {"test": "BOM-109 second design, Manchester sensitivity (lab; exploratory)",
           "label": LABEL, "simulated": SIMULATED}  # fmt: skip
    if not ev["passed"]:
        res["state"] = "not scored: the main run's checks have not passed"
        return res
    match = cmd_match(cfg)
    mworks = manchester_works(match)
    by_work = text_work_ids(texts)
    in_list = {by_work[w] for w in mworks if w in by_work} | set(NAMED)
    ref = [t for t in texts if t["role"] in ("reference", "rule") and t["row"]]
    states, _status, _sig = tw.score_texts(ref, ments, answers, cfg)
    s = settings(cfg)
    am_a = {t["name"]: (AM, t["row"]) for t in ref if t["world"] == AM and t["name"] in in_list}
    res["a_card_words"] = variant(texts, states, am_a, s["rows_pooled"][AM], ments, answers, cfg)
    mt = [t for t in manchester_texts(cfg, texts, match) if t["row"]]
    for t in mt:
        segs = tw.segments_of(t, cfg)
        if segs is not None:
            ments[t["name"]] = tw.mentions_of(t["name"], segs, cfg)
    st_b, status_b, _ = tw.score_texts(mt, ments, answers, cfg)
    open_b = [t["name"] for t in mt if t["name"] in ments and t["name"] not in st_b]
    res["b_holdings_row"] = {"texts": {t["name"]: {"accession": t["accession"],
                                                   "subject": t["subject_answer"]} for t in mt},
                             "open": open_b}  # fmt: skip
    if open_b or any(t["subject_answer"] is None for t in manchester_texts(cfg, texts, match)):
        res["b_holdings_row"]["state"] = "open (subject or mention answers missing)"
    else:
        am_b = {t["name"]: (AM, t["row"]) for t in mt}
        res["b_holdings_row"].update(
            variant(texts, {**states, **st_b}, am_b, ["manchester"], ments, answers, cfg)
        )
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["match", "jobs", "sensitivity"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "match":
        res = cmd_match(cfg)
        tw.write(OUT / "manchester_match.json", res)
        print(json.dumps({k: v for k, v in res.items() if k != "matches"}, indent=1))
    elif a.cmd == "jobs":
        res = cmd_jobs(cfg)
        tw.write(OUT / "manchester_jobs.json", res)
        print(json.dumps(res, indent=1))
    else:
        res = cmd_sensitivity(cfg)
        tw.write(OUT / "manchester_sensitivity.json", res)
        print(res.get("state") or json.dumps({k: res[k].get("book_verdict") for k in
                                              ("a_card_words", "b_holdings_row")}))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
