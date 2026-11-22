"""BOM-104: Joseph Smith's other dictated texts, and who wrote the Lectures on Faith.

Two questions, measured with the three measures already built for the two-voices runs and reused,
not rebuilt: function words (``lab.twovoices``: Burrows's and Cosine Delta on the 150 most
frequent words of a library background), the study's two style encoders (``lab.twovoices_enc``)
and 125M author models (``lab.dictations_alm``, the recipe of ``lab.twovoices_alm``).

A. Are the Book of Moses (Old Testament Revision 1, Moses 1-8), the Book of Abraham (1842) and the
revelations of Revelation Book 1 by period closer to the Book of Mormon, to Joseph Smith's ordinary
writing or to another candidate, and does the distance from the Book of Mormon grow with the years?
B. Which of five candidates (Smith, Rigdon, Cowdery, Phelps, Pratt) is closest to each of the seven
Lectures on Faith (1835), against the published attributions (Phipps 1977; Reynolds 2005)?

Every text is lower-cased, long-s repaired, King James word 5-grams dropped and cut into 1,000-word
chunks (``lab.twovoices``). Each candidate's first ``train_chunks`` chunks train (centroids; the
author models' slices); ``test_chunks`` held-out chunks per candidate form the known-answer check,
which every measure must pass before it is used. The Book of Mormon is embedded and scored, never
trained or tuned on. Card, written first: ``data/private/lab/owner/2026-11-21-other-dictations/
card.md``; settings ``lab.dictations``. The result holds ids and numbers, no text; vectors and
model losses stay in ``data/corpus/lab/dictations/``.

Usage::

    python -m lab.dictations plan                      # words and chunks per text (seconds)
    python -m lab.dictations embed [--encoder bom30|v2]  # Mac GPU: chunk vectors per encoder
    python -m lab.dictations check                     # known-answer check, every measure held
    python -m lab.dictations run                       # -> data/lab/dictations/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from pathlib import Path

import numpy as np

from lab import twovoices as tv
from lab.paths import FAST, REGISTRY, out
from metadata import config

OUT = REGISTRY / "dictations"
WORK = FAST / "dictations"
CLEAN = Path("data/candidates/clean")
SIGNED = Path("data/candidates/signed_items.json")
DC1835 = Path("data/private/replication/jsp_dc1835.jsonl")
DICTATED = Path("data/private/lab/sources/dictated")
JS_LATER = Path("data/private/candidates/later")
JS_PRE = Path("data/private/candidates/samples/joseph-smith__dictated__pre1830.txt")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
SIGNERS = {"sidney_rigdon": "Sidney Rigdon", "oliver_cowdery": "Oliver Cowdery",
           "ww_phelps": "W. W. Phelps"}  # fmt: skip
LECTURES = ("FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH")
# The published attributions, as summarised in the issue (BOM-104 comment of 2026-11-18): Phipps
# 1977 from the record page, Reynolds 2005 from the abstract. Not checked against the originals.
PUBLISHED = {
    "phipps_1977": {1: "sidney_rigdon", 2: "sidney_rigdon", 3: "sidney_rigdon",
                    4: "sidney_rigdon", 5: "joseph_smith", 6: "sidney_rigdon",
                    7: "sidney_rigdon"},
    "reynolds_2005": dict.fromkeys(range(1, 8), "sidney_rigdon"),
}  # fmt: skip
PUBLISHED_NOTE = ("from the issue's summaries (record page; abstract), unverified against the "
                  "originals; the summaries disagree on whether Phipps gave lecture 2 or 5 to "
                  "Smith")  # fmt: skip
LEFT_OUT = {
    "visions_of_moses_1830": "a second copy of Moses 1, which Old Testament Revision 1 holds",
    "ot_revision_2": "a copy of Revision 1, then a Bible revision that is mostly King James text",
    "ot_revision_1_after_p20": "Genesis revision after Moses 8: under 25% non-King James a page",
    "abraham_ms_a_b_c": "1835 copies of part of the text printed in 1842",
    "rigdon_appeal_1840": "unsigned",
    "rigdon_sidneyrigdon_com": "series attributed by a modern editor, not signed",
}
BRACKET = re.compile(r"\[([^\]]*)\]")
QA = re.compile(r"^\s*(question|q\.)", re.I | re.M)


# ------------------------------------------------------------------------------ texts


def strip_editorial(text: str) -> str:
    """Joseph Smith Papers transcripts: page markers and editors' notes in square brackets are
    removed ("[p. 12]", "[page blank]", "-[§ iii. ¶ 26.]-"); a bracketed supplied letter or word
    inside the text ("[to] pass") keeps its content."""

    def sub(m: re.Match) -> str:
        c = m.group(1)
        if re.match(r"\s*p\.", c) or re.search(r"page|blank|§|¶|cover|flyleaf|pastedown", c):
            return " "
        return c

    return BRACKET.sub(sub, text).replace("-[", " ").replace("]-", " ")


def masked(text: str, vocab: set[str], grams: set[str]) -> list[str]:
    return tv.drop_kjv(tv.tokens(text, vocab)[0], grams, 5)


def _pages(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines()]


def _page_no(r: dict) -> int | None:
    p = str(r["editorialPageNumber"])
    return int(p) if p.isdigit() else None


def candidate_tokens(cfg: dict, vocab: set[str], grams: set[str]) -> tuple[dict, dict]:
    """({candidate: masked tokens in text order}, {candidate: record}). Joseph Smith's stream is
    built exactly as ``lab.twovoices_alm`` built his ordinary voice (so its cached models fit)."""
    n = cfg["lab"]["two_voices"]["kjv_ngram"]
    toks: dict[str, list[str]] = {}
    rec: dict[str, dict] = {}
    words: list[str] = []
    for src in tv.SPEC["joseph_smith"]["ordinary"]:
        text, _ = tv.read_source(src, cfg)
        words += tv.tokens(text, vocab)[0]
    toks["joseph_smith"] = tv.drop_kjv(words, grams, n)
    rec["joseph_smith"] = {"sources": "lab.twovoices.SPEC joseph_smith ordinary (4 samples)",
                           "words": len(words)}  # fmt: skip
    items = [s for s in json.loads(SIGNED.read_text()) if s["admit"]]
    order = {"wwp-evening-morning-star": 0, "oc-messenger-advocate": 1}
    for cand, signer in SIGNERS.items():
        mine = sorted((s for s in items if s["signer"] == signer),
                      key=lambda s: (order.get(s["source"], 9), s["start"]))  # fmt: skip
        files = [CLEAN / f"{s['source']}__{s['start']}-{s['end']}.txt" for s in mine]
        if cand == "sidney_rigdon":
            files.append(CLEAN / "sr-1838-oration.txt")
        words = []
        for f in files:
            text, _ = tv.read_source(("file", str(f)), cfg)
            words += tv.tokens(text, vocab)[0]
        toks[cand] = tv.drop_kjv(words, grams, n)
        rec[cand] = {"sources": [f.name for f in files], "words": len(words)}
    text, _ = tv.read_source(("file", str(CLEAN / "ppp-1837-voice-of-warning.txt")), cfg)
    words = tv.tokens(text, vocab)[0]
    toks["parley_pratt"] = tv.drop_kjv(words, grams, n)
    rec["parley_pratt"] = {"sources": ["ppp-1837-voice-of-warning.txt"], "words": len(words)}
    for c in toks:
        rec[c]["words_masked"] = len(toks[c])
    return {c: toks[c] for c in cfg["lab"]["dictations"]["candidates"]}, rec


def lectures(cfg: dict, vocab: set[str], grams: set[str]) -> dict:
    """{lecture number: {"body": tokens, "qa": tokens}} from the 1835 Doctrine and Covenants."""
    a, b = cfg["lab"]["dictations"]["lectures_pages"]
    rows = [r for r in _pages(DC1835) if _page_no(r) is not None and a <= _page_no(r) <= b]
    text = strip_editorial("\n".join(r["text"] for r in rows))
    cuts = [re.search(rf"LECTURE {w}\b", text) for w in LECTURES]
    if any(c is None for c in cuts):
        raise OSError("a lecture heading was not found")
    res = {}
    for i, c in enumerate(cuts):
        end = cuts[i + 1].start() if i + 1 < len(cuts) else len(text)
        part = text[c.start() : end]
        q = QA.search(part)
        body, qa = (part[: q.start()], part[q.start() :]) if q else (part, "")
        res[i + 1] = {"body": masked(body, vocab, grams), "qa": masked(qa, vocab, grams)}
    return res


def dictated(cfg: dict, vocab: set[str], grams: set[str]) -> tuple[dict, dict]:
    """({group: tokens}, {group: record}): Moses, Abraham 1842, revelations by period."""
    from eval.js_later import year_of

    t = cfg["lab"]["dictations"]
    groups: dict[str, list[str]] = {}
    rec: dict[str, dict] = {}
    a, b = t["moses_pages"]
    rows = [r for r in _pages(DICTATED / "ot_revision_1" / "pages.jsonl")
            if _page_no(r) is not None and a <= _page_no(r) <= b]  # fmt: skip
    groups["moses"] = masked(strip_editorial("\n".join(r["text"] for r in rows)), vocab, grams)
    rec["moses"] = {
        "source": "ot_revision_1",
        "pages": [a, b],
        "dates": "1830-06 to 1831-03",
        "scribes": "Cowdery, Whitmer, Emma Smith, Rigdon (issue research)",
    }
    rows = _pages(DICTATED / "abraham_1842" / "pages.jsonl")
    groups["abraham"] = masked(strip_editorial("\n".join(r["text"] for r in rows)), vocab, grams)
    rec["abraham"] = {"source": "abraham_1842", "pages": len(rows), "dates": "1835-1842"}
    per: dict[str, list[str]] = {p: [] for p in t["periods"]}
    files: dict[str, int] = dict.fromkeys(t["periods"], 0)

    def period(y: int) -> str | None:
        return next((p for p, (lo, hi) in t["periods"].items() if lo <= y <= hi), None)

    per[period(1829)] += masked(JS_PRE.read_text(errors="replace"), vocab, grams)
    files[period(1829)] += 1
    undated = 0
    for f in sorted(JS_LATER.glob("*.txt")):
        text = f.read_text(errors="replace")
        y = year_of(text[:60])
        p = period(y) if y else None
        if p is None:
            undated += 1
            continue
        per[p] += masked(text, vocab, grams)
        files[p] += 1
    for p, toks in per.items():
        groups[f"rev_{p}"] = toks
        rec[f"rev_{p}"] = {"source": "Revelation Book 1 (1828-29 sample + later sections)",
                           "sections": files[p]}  # fmt: skip
    rec["_undated_sections"] = undated
    return groups, rec


def bom_tokens(vocab: set[str], grams: set[str]) -> list[str]:
    rows = [json.loads(x) for x in EDITION.read_text().splitlines()]
    return masked(" ".join(r["text"] for r in rows if r["kind"] == "body"), vocab, grams)


def pieces(toks: list[str], size: int, min_last: int) -> list[list[str]]:
    """Consecutive ``size``-word pieces and a last shorter one of at least ``min_last`` words."""
    res = [toks[i : i + size] for i in range(0, len(toks), size)]
    if res and len(res[-1]) < min(size, min_last):
        res.pop()
    return res


def build(cfg: dict) -> dict:
    """Every unit of the run: {"items": {id: tokens}, "whole": {id: tokens}, "meta": records}.
    Item ids: ``cand|<c>|train|i``, ``cand|<c>|test|i``, ``lec|<n>|i``, ``qa|<n>|i``,
    ``grp|<g>|i``, ``bom|i``; "whole" holds each lecture body (``lecw|<n>``)."""
    t, size = cfg["lab"]["dictations"], cfg["lab"]["two_voices"]["chunk_words"]
    vocab, grams = tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
    items: dict[str, list[str]] = {}
    whole: dict[str, list[str]] = {}
    meta: dict = {"candidates": {}, "lectures": {}, "groups": {}, "not_attempted": {}}
    cands, crec = candidate_tokens(cfg, vocab, grams)
    held = {c: tv.chunks(x, size)[t["train_chunks"] :] for c, x in cands.items()}
    k = min([t["test_chunks"]] + [len(h) for h in held.values()])
    rng = random.Random(t["seed"])
    for c, x in cands.items():
        ch = tv.chunks(x, size)
        for i in range(t["train_chunks"]):
            items[f"cand|{c}|train|{i}"] = ch[i]
        pick = sorted(rng.sample(range(len(held[c])), k))
        for j, i in enumerate(pick):
            items[f"cand|{c}|test|{j}"] = held[c][i]
        meta["candidates"][c] = {
            **crec[c],
            "chunks": len(ch),
            "heldout_chunks": len(held[c]),
            "test_chunk_index": [t["train_chunks"] + i for i in pick],
        }
    meta["test_chunks"] = k
    try:
        lec = lectures(cfg, vocab, grams)
        for n, d in lec.items():
            ps = pieces(d["body"], size, t["min_piece_words"])
            for i, p in enumerate(ps):
                items[f"lec|{n}|{i}"] = p
            whole[f"lecw|{n}"] = d["body"]
            for i, p in enumerate(pieces(d["qa"], size, t["min_piece_words"])):
                items[f"qa|{n}|{i}"] = p
            meta["lectures"][n] = {"body_words_masked": len(d["body"]), "pieces": len(ps),
                                   "qa_words_masked": len(d["qa"])}  # fmt: skip
    except OSError as e:
        meta["not_attempted"]["lectures"] = str(e)
    try:
        groups, grec = dictated(cfg, vocab, grams)
        for g, x in groups.items():
            ch = tv.chunks(x, size)
            for i, c in enumerate(ch):
                items[f"grp|{g}|{i}"] = c
            meta["groups"][g] = {**grec[g], "words_masked": len(x), "chunks": len(ch)}
        meta["undated_sections"] = grec["_undated_sections"]
    except OSError as e:
        meta["not_attempted"]["dictated"] = str(e)
    try:
        b = tv.chunks(bom_tokens(vocab, grams), size)
        for i, c in enumerate(b):
            items[f"bom|{i}"] = c
        meta["book_of_mormon"] = {"chunks": len(b), "use": "scored only; never trained or tuned"}
    except OSError as e:
        meta["not_attempted"]["book_of_mormon"] = str(e)
    return {
        "items": items,
        "whole": whole,
        "meta": meta,
        "cands": list(cands),
        "train_tokens_stream": cands,
    }


# ------------------------------------------------------------------------------ vectors


def fw_vectors(cfg: dict, b: dict) -> tuple[dict, dict]:
    """Function-word z-vectors of every item and every whole lecture."""
    t = cfg["lab"]["two_voices"]
    vocab, grams = tv.kjv_vocab_and_grams(t["kjv_ngram"])
    windows = tv.background(cfg, vocab, grams)
    feats = tv.features(windows, t["mfw"], set())
    mu, sd = tv.scaler(windows, feats, t["chunk_words"])

    def z(x):
        return (tv.relfreq(x, feats) - mu) / sd

    vecs = {i: z(x) for i, x in {**b["items"], **b["whole"]}.items()}
    return vecs, {"background_works": len(windows), "features": len(feats), "_z": z}


def embed(cfg: dict, name: str) -> int:
    """Encoder vectors of every item, as ``lab.twovoices_enc.embed`` embeds a chunk."""
    import torch
    from tokenizers import Tokenizer

    from lab.twovoices_enc import chunk_ids
    from style_embed.train import load_encoder
    from sweep.index import episode_vectors
    from timelocked_lm.release import TOKENIZER

    s = cfg["style_embed"]
    path = Path(cfg["lab"]["two_voices_enc"]["encoders"][name])
    if not path.exists():
        raise OSError(f"encoder weights missing: {path}")
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    b = build(cfg)
    enc = load_encoder(path, cfg).to(dev)
    tok = Tokenizer.from_file(str(TOKENIZER))
    n, per = s["passage_tokens"], s["episode_passages"]
    keys = sorted(b["items"])
    arr = []
    for k in keys:
        ids = chunk_ids(tok.encode(" ".join(b["items"][k])).ids, n, per)
        arr.append(episode_vectors(enc, ids, n, per, dev)[0][0])
    p = out(WORK / f"vectors_{name}.tmp.npz")
    np.savez(p, keys=np.array(keys), vecs=np.stack(arr).astype(np.float32))
    p.replace(WORK / f"vectors_{name}.npz")
    print(f"{name}: {len(keys)} items on {dev} -> {WORK / f'vectors_{name}.npz'}")
    return 0


def enc_vectors(name: str, b: dict) -> dict:
    """{item: vector} plus each whole lecture as the mean of its pieces; ``OSError`` if missing
    or built from another set of items."""
    p = WORK / f"vectors_{name}.npz"
    if not p.exists():
        raise OSError(f"{p} missing: run embed --encoder {name}")
    z = np.load(p)
    vecs = {str(k): v.astype(np.float64) for k, v in zip(z["keys"], z["vecs"], strict=True)}
    if set(vecs) != set(b["items"]):
        raise OSError(f"{p} was built from other items: rerun embed --encoder {name}")
    for w in b["whole"]:
        n = w.split("|")[1]
        ps = [v for k, v in vecs.items() if k.startswith(f"lec|{n}|")]
        if ps:
            vecs[w] = np.mean(ps, axis=0)
    return vecs


# ------------------------------------------------------------------------------ analysis


def ids_of(keys, prefix: str) -> list[str]:
    return sorted((k for k in keys if k.startswith(prefix)), key=lambda k: int(k.split("|")[-1]))


def known_answer(scores: dict, cands: list[str], t: dict) -> dict:
    """``scores``: {test item: {candidate: distance}}; lower wins (ties by name)."""
    per, went = {}, {c: {} for c in cands}
    for c in cands:
        rows = [k for k in scores if k.startswith(f"cand|{c}|test|")]
        for k in rows:
            w = min(cands, key=lambda x: (scores[k][x], x))
            went[c][w] = went[c].get(w, 0) + 1
        per[c] = round(went[c].get(c, 0) / len(rows), 3) if rows else None
    rates = [r for r in per.values() if r is not None]
    macro = round(sum(rates) / len(rates), 3) if rates else None
    pull = {}
    for c in cands:
        others = sum(sum(went[o].values()) for o in cands if o != c)
        pull[c] = round(sum(went[o].get(c, 0) for o in cands if o != c) / others, 3) if others \
            else None  # fmt: skip
    passed = (
        macro is not None
        and macro >= t["known_bar"]
        and all(r is not None and r >= t["min_each"] for r in per.values())
    )
    return {"own_rate": per, "macro": macro, "went_to": went, "pull": pull,
            "chance": round(1 / len(cands), 3), "passed": bool(passed)}  # fmt: skip


def votes(scores: dict, keys: list[str], refs: list[str]) -> dict:
    got: dict[str, int] = {}
    for k in keys:
        w = min(refs, key=lambda x: (scores[k][x], x))
        got[w] = got.get(w, 0) + 1
    return got


def centroid_scores(vecs: dict, cands: list[str], dist, extra: dict | None = None) -> dict:
    """Distance of every item (and whole lecture) to each candidate's training centroid, and to
    the extra references given as {name: centroid}."""
    cents = {c: np.mean([vecs[k] for k in ids_of(vecs, f"cand|{c}|train|")], axis=0)
             for c in cands}  # fmt: skip
    cents.update(extra or {})
    return {k: {c: float(dist(v, cents[c])) for c in cents} for k, v in vecs.items()}


def lecture_table(scores: dict, cands: list[str], keys) -> dict:
    res = {}
    for w in sorted(k for k in keys if k.startswith("lecw|")):
        n = w.split("|")[1]
        order = sorted(cands, key=lambda c: (scores[w][c], c))
        res[n] = {"winner": order[0], "runner_up": order[1],
                  "margin": round(scores[w][order[1]] - scores[w][order[0]], 4),
                  "distance": {c: round(scores[w][c], 4) for c in cands},
                  "piece_votes": votes(scores, ids_of(scores, f"lec|{n}|"), cands)}  # fmt: skip
    qa = [k for k in scores if k.startswith("qa|")]
    if qa:
        res["qa_pooled_piece_votes"] = votes(scores, qa, cands)
    return res


def spearman(x: list[float], y: list[float]) -> float:
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    if rx.std() == 0 or ry.std() == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def profiles(vecs: dict, groups: list[str], cands: list[str], dist, t: dict) -> dict:
    """Question A: equal profiles of ``profile_chunks`` chunks, ``resamples`` draws."""
    rng = np.random.default_rng(t["seed"])
    k = t["profile_chunks"]
    pools = {g: [vecs[x] for x in ids_of(vecs, f"grp|{g}|")] for g in groups}
    pools["book_of_mormon"] = [vecs[x] for x in ids_of(vecs, "bom|")]
    for c in cands:
        pools[c] = [vecs[x] for x in ids_of(vecs, f"cand|{c}|train|")]
    refs = ["book_of_mormon", *cands]
    ok = [g for g in groups if len(pools[g]) >= k]
    if len(pools["book_of_mormon"]) < k:
        return {"not_attempted": "Book of Mormon chunks missing"}
    d = {g: {r: [] for r in refs} for g in ok}
    periods = [g for g in ok if g.startswith("rev_")]
    dated = [g for g in ("rev_1828-30", "moses", "rev_1831", "rev_1832", "rev_1833-34",
                         "abraham") if g in ok]  # fmt: skip
    trend, trend_all, trend_ord = [], [], []
    for _ in range(t["resamples"]):
        prof = {}
        for name, pool in pools.items():
            if len(pool) >= k:
                pick = rng.choice(len(pool), size=k, replace=False)
                prof[name] = np.mean([pool[i] for i in pick], axis=0)
        for g in ok:
            for r in refs:
                d[g][r].append(float(dist(prof[g], prof[r])))
        if len(periods) >= 3:
            trend.append(
                spearman(list(range(len(periods))), [d[g]["book_of_mormon"][-1] for g in periods])
            )
            trend_ord.append(spearman(list(range(len(periods))),
                                      [d[g]["joseph_smith"][-1] for g in periods]))  # fmt: skip
        if len(dated) >= 3:
            trend_all.append(spearman(list(range(len(dated))),
                                      [d[g]["book_of_mormon"][-1] for g in dated]))  # fmt: skip

    def q(xs):
        return [round(float(np.percentile(xs, p)), 4) for p in (2.5, 50, 97.5)]

    res: dict = {"groups": {}, "too_few_chunks": [g for g in groups if g not in ok]}
    for g in ok:
        med = {r: float(np.median(d[g][r])) for r in refs}
        closer = float(np.mean(np.array(d[g]["book_of_mormon"]) < np.array(d[g]["joseph_smith"])))
        if closer >= t["clear_share"]:
            v = "closer to the Book of Mormon"
        elif 1 - closer >= t["clear_share"]:
            v = "closer to his ordinary writing"
        else:
            v = "cannot tell"
        res["groups"][g] = {"distance": {r: q(d[g][r]) for r in refs},
                            "nearest_reference": min(refs, key=lambda r: med[r]),
                            "share_bom_closer_than_ordinary": round(closer, 3),
                            "verdict_bom_vs_ordinary": v}  # fmt: skip

    def verdict(xs):
        if not xs:
            return {"verdict": "not attempted"}
        up = float(np.mean(np.array(xs) > 0))
        down = float(np.mean(np.array(xs) < 0))
        v = ("grows" if up >= t["clear_share"] else "shrinks" if down >= t["clear_share"]
             else "no clear trend")  # fmt: skip
        return {"spearman": q(xs), "share_above_0": round(up, 3),
                "share_below_0": round(down, 3), "verdict": v}  # fmt: skip

    res["years_revelations_to_bom"] = {"order": periods, **verdict(trend)}
    res["years_revelations_to_ordinary"] = {"order": periods, **verdict(trend_ord),
                                            "note": "descriptive"}  # fmt: skip
    res["years_all_dictated_to_bom"] = {"order": dated, **verdict(trend_all),
                                        "note": "secondary, descriptive"}  # fmt: skip
    return res


def group_votes(scores: dict, groups: list[str], refs: list[str]) -> dict:
    res = {g: votes(scores, ids_of(scores, f"grp|{g}|"), refs) for g in groups}
    res["book_of_mormon"] = votes(
        scores, ids_of(scores, "bom|"), [r for r in refs if r != "book_of_mormon"]
    )
    res["lectures_pooled"] = votes(scores, [k for k in scores if k.startswith("lec|")], refs)
    return res


def moses_scribes(scores: dict, b: dict, cands: list[str]) -> dict:
    """Moses chunks split by position: the first nine pages (Cowdery, per the issue's research;
    unverified at page level) against the rest, by the number of words before page 10."""
    return {"note": "chunks of the Book of Moses in text order; the scribe of each page is not "
            "in the data: see the card", "votes_by_chunk": {
                k: min(cands, key=lambda c: (scores[k][c], c))
                for k in ids_of(scores, "grp|moses|")}}  # fmt: skip


def measure(vecs: dict, b: dict, dist, t: dict, check_only: bool) -> dict:
    cands = b["cands"]
    groups = list(b["meta"]["groups"])
    sc = centroid_scores(vecs, cands, dist)
    ka = known_answer({k: v for k, v in sc.items() if "|test|" in k}, cands, t)
    res: dict = {"known_answer": ka}
    if check_only:
        return res
    if not ka["passed"]:
        res["stopped"] = "missed the known-answer bar: not used for either question"
        return res
    res["lectures"] = lecture_table(sc, cands, sc.keys())
    bom = [vecs[k] for k in ids_of(vecs, "bom|")]
    rng = random.Random(t["seed"])
    if len(bom) >= t["train_chunks"]:
        pick = sorted(rng.sample(range(len(bom)), t["train_chunks"]))
        ref = {"book_of_mormon": np.mean([bom[i] for i in pick], axis=0)}
        sc2 = centroid_scores({k: v for k, v in vecs.items() if not k.startswith("bom|")},
                              cands, dist, ref)  # fmt: skip
        res["chunk_nearest_with_bom"] = {
            g: votes(sc2, ids_of(sc2, f"grp|{g}|"), ["book_of_mormon", *cands]) for g in groups
        }
        res["chunk_nearest_with_bom"]["lectures_pooled"] = votes(
            sc2, [k for k in sc2 if k.startswith("lec|")], ["book_of_mormon", *cands]
        )
        res["bom_reference_chunks"] = pick
    res["chunk_nearest_candidate"] = group_votes(sc, groups, cands)
    res["profiles"] = profiles(vecs, groups, cands, dist, t)
    res["moses_positions"] = moses_scribes(sc, b, cands)
    return res


def halves_check(cfg: dict, b: dict, vecs: dict, dist) -> dict:
    """POST HOC diagnostic, added after every measure missed the check, and never used to answer
    either question: the two-voices design (``lab.twovoices.within_voice``'s halves, both ways),
    every chunk of each candidate split into first and second half, each side capped at the
    smallest candidate's half, to see whether the miss comes from the small training part."""
    t = cfg["lab"]["dictations"]
    cands = b["cands"]
    vocab, grams = tv.kjv_vocab_and_grams(cfg["lab"]["two_voices"]["kjv_ngram"])
    streams = b["train_tokens_stream"]
    size = cfg["lab"]["two_voices"]["chunk_words"]
    feats_z = vecs["_z"]
    z = {c: np.array([feats_z(x) for x in tv.chunks(streams[c], size)]) for c in cands}
    k = min(len(a) for a in z.values()) // 2
    rng = random.Random(t["seed"])
    per = {c: [0, 0] for c in cands}
    for flip in (False, True):
        tr, te = {}, {}
        for c, a in z.items():
            h = len(a) // 2
            x, y = (a[h:], a[:h]) if flip else (a[:h], a[h:])
            tr[c] = x[sorted(rng.sample(range(len(x)), k))]
            te[c] = y[sorted(rng.sample(range(len(y)), k))]
        for c, (n, ok, _) in tv.attribute(tr, te, dist).items():
            per[c][0] += n
            per[c][1] += ok
    rates = {c: round(ok / n, 3) for c, (n, ok) in per.items()}
    return {"chunks_a_side": k, "own_rate": rates,
            "macro": round(sum(rates.values()) / len(rates), 3)}  # fmt: skip


def combined(res: dict, alm: dict | None) -> dict:
    """Question B read across the measures that passed: a lecture is attributed when every one of
    them names the same candidate (author models only where both doses agree)."""
    used = {
        m: r
        for m, r in res.items()
        if m in ("function_words_burrows", "encoder_bom30", "encoder_v2") and "lectures" in r
    }
    table = {}
    for n in map(str, range(1, 8)):
        names = {m: r["lectures"][n]["winner"] for m, r in used.items() if n in r["lectures"]}
        if alm and alm.get("lectures", {}).get(n, {}).get("both_doses") not in (None, "no answer"):
            names["author_models"] = alm["lectures"][n]["both_doses"]
        vals = set(names.values())
        table[n] = {"by_measure": names,
                    "attributed": vals.pop() if len(vals) == 1 and names else
                    "measures disagree" if names else "no measure passed"}  # fmt: skip
    agree = {}
    for study, att in PUBLISHED.items():
        agree[study] = {
            "combined": sum(table[str(n)]["attributed"] == c for n, c in att.items()),
            **{
                m: sum(r["lectures"][str(n)]["winner"] == c for n, c in att.items())
                for m, r in used.items()
            },
        }
        if alm and "lectures" in alm:
            agree[study]["author_models_both_doses"] = sum(
                alm["lectures"][str(n)].get("both_doses") == c for n, c in att.items()
            )
    return {"measures_used": list(used) + (["author_models"] if alm and "lectures" in alm
                                           else []),
            "per_lecture": table, "agreement_with_published": agree,
            "published": PUBLISHED, "published_note": PUBLISHED_NOTE}  # fmt: skip


def run(cfg: dict, check_only: bool = False) -> dict:
    t = cfg["lab"]["dictations"]
    b = build(cfg)
    res: dict = {
        "exploratory": True,
        "settings": t,
        "texts": b["meta"],
        "left_out": LEFT_OUT,
        "book_of_mormon": "embedded and scored only; never trained or tuned on (lesson 11)",
        "measures": {},
        "not_attempted": dict(b["meta"]["not_attempted"]),
    }
    fw, info = fw_vectors(cfg, b)
    zf = info.pop("_z")
    res["function_words_background"] = info
    res["measures"]["function_words_burrows"] = measure(fw, b, tv.delta, t, check_only)
    res["measures"]["function_words_cosine"] = measure(fw, b, tv.cosine_delta, t, check_only)
    for name in cfg["lab"]["two_voices_enc"]["encoders"]:
        try:
            v = enc_vectors(name, b)
        except OSError as e:
            res["not_attempted"][f"encoder_{name}"] = str(e)
            continue
        res["measures"][f"encoder_{name}"] = measure(v, b, tv.cosine_delta, t, check_only)
    from lab import dictations_alm

    try:
        res["measures"]["author_models"] = dictations_alm.analyse(cfg, b, check_only)
    except OSError as e:
        res["not_attempted"]["author_models"] = str(e)
    res["passed_check"] = [m for m, r in res["measures"].items()
                           if r.get("known_answer", {}).get("passed")]  # fmt: skip
    if check_only:
        return res
    if not res["passed_check"]:
        res["post_hoc_diagnostic_halves"] = {
            "function_words_burrows": halves_check(cfg, b, {"_z": zf}, tv.delta),
            "function_words_cosine": halves_check(cfg, b, {"_z": zf}, tv.cosine_delta),
            "note": "post hoc, after the check missed; not used to answer",
        }
        res["stopped"] = ("every measure missed the known-answer bar: neither question is "
                          "answered and no target is reported")  # fmt: skip
    else:
        res["question_b"] = combined(res["measures"], res["measures"].get("author_models"))
    return res


def _commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plan", "embed", "check", "run"])
    ap.add_argument("--encoder", help="embed: one encoder (default: every one in the config)")
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plan":
        print(json.dumps(build(cfg)["meta"], indent=1))
        return 0
    if a.cmd == "embed":
        for name in [a.encoder] if a.encoder else list(cfg["lab"]["two_voices_enc"]["encoders"]):
            embed(cfg, name)
        return 0
    res = run(cfg, check_only=a.cmd == "check")
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = _commit()
    if a.cmd == "check":
        print(json.dumps({m: {k: r["known_answer"][k] for k in ("own_rate", "macro", "passed")}
                          if "known_answer" in r else r for m, r in res["measures"].items()},
                         indent=1))  # fmt: skip
        print("not attempted:", res["not_attempted"] or "none")
        return 0
    out(OUT / "result.json").write_text(json.dumps(res, indent=1) + "\n")
    for m, r in res["measures"].items():
        ka = r.get("known_answer", {})
        print(m, ka.get("macro"), ka.get("passed"), r.get("stopped", ""))
    print(res.get("stopped") or json.dumps(res["question_b"]["per_lecture"], indent=1))
    print("->", OUT / "result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
