"""BOM-130: 2 Nephi 28 against the texts a reader named, by BOM-126's two searches.

A reader named four texts behind 2 Nephi 28: *Scripture Inquiry into the State and Condition of
Mankind* (1828), *The Life and Morals of Epicurus* (1822; both held), a farewell sermon *The
Immoral Tendency of Error in Sentiment* (1809) and George Richard Casse's *Authentic Narrative*
(neither held: Google Books only, see the card's amendment 1). This asks whether the chapter sits
closer to any of them than to the rest of the library, by the study's two borrowing searches cut
down to the chapter's passages:

- **Rare shared phrases.** The chapter's King James-masked 4-grams; a volume's score is how many
  of them it shares that are rare (document frequency by text at most ``borrowing.max_df`` over
  the stored 1780-1830 population) per 10,000 of its words. Hits come from the study's stored scan.
- **Meaning.** The study's stored query vectors for the chapter, one exact pass over the passage
  index: a work's place is the number of queries on which its best passage is among the query's
  100 nearest and above its bar (the stored measure), then the mean best-passage score.

Ranks are among kept copies (registry ``dup_keeper``, not sealed); anything else is placed against
them, with ties counted against the text. Topic controls (sermons and tracts on universal
salvation or endless punishment, 1780-1829 and 1640-1779), an Alma decoy chapter and the whole
1830 chapter XII go through the same code. The known-answer check plants ten passages from known
works into the chapter and asks a chapter-size window of *The Late War* to find Hunt's printings.

The card (written first, with its amendment) is
``data/private/lab/owner/2026-11-27-2nephi28-sources/card.md``; settings ``lab.nephi28_sources``.
Outputs hold ids, ranks and counts; the plant passages (text) stay in the private card folder.

Usage::

    python -m lab.nephi28_sources plants    # draw the plants; scan for their 4-grams (resumes)
    python -m lab.nephi28_sources meaning   # one exact pass over the passage index (resumes)
    python -m lab.nephi28_sources check     # the known-answer checks only
    python -m lab.nephi28_sources run       # -> data/lab/reruns/nephi28_sources/result.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from lab import door, registry
from lab.paths import FAST, NOTES, REGISTRY, out
from metadata import config

OUT = REGISTRY / "reruns" / "nephi28_sources"
WORK = FAST / "nephi28"  # derived, local: plant-gram scan parts, the index pass
CARD = NOTES / "owner" / "2026-11-27-2nephi28-sources"
PLANTS = CARD / "plants.jsonl"  # private: the plant passages' text
DONE = WORK / "plant_scan" / "done.json"
BOM_HITS = Path("data/reuse/bom/hits.parquet")
BOM_GRAMS = Path("data/reuse/bom/target_grams.txt")
LATE_WAR_HITS = Path("data/reuse/null_sizing/hits.parquet")
EDITION = Path("data/bom/1830/edition_1830.jsonl")
KJV_SPANS = Path("data/kjv_mask/bom/spans.jsonl")
SEARCH = Path("data/corpus/semantic/search")
CATALOG = Path("data/catalog/catalog.parquet")
INF = np.float32(-np.inf)


# ---- small pieces (tested) ----------------------------------------------------------------


def seqs(span: list[int]) -> set[int]:
    lo, hi = span
    return set(range(lo, hi + 1))


def rank_against(score: float, population: np.ndarray, member: bool) -> int:
    """Rank of ``score`` among ``population`` (one score per kept copy), ties counted against the
    text: every other score at or above it comes first. ``member``: the score is itself one of
    the population's (it does not beat itself)."""
    at_or_above = int((population >= score).sum())
    return at_or_above if member else at_or_above + 1


def meaning_key(places: np.ndarray, mean_best: np.ndarray) -> np.ndarray:
    """One number that orders by places first, then by mean best score (a score lies in [-1, 1],
    so four per place keeps the order lexicographic)."""
    return places.astype(np.float64) * 4.0 + mean_best.astype(np.float64)


def rare_grams(grams: set[int], df: dict[int, int], max_df: int, outside: bool) -> set[int]:
    """The target grams that count as rare. A text outside the population adds itself to each
    gram's document frequency."""
    extra = 1 if outside else 0
    return {g for g in grams if 0 < df.get(g, 0) + extra <= max_df}


def chapter_window(n_words: int, total: int) -> tuple[int, int]:
    """A window of ``n_words`` from the middle of a ``total``-word text."""
    a = max(0, (total - n_words) // 2)
    return a, min(total, a + n_words)


def verdict(best: dict[str, float | None], above_controls: dict[str, bool], c: dict) -> str:
    """The card's rule. ``best``: search -> the named text's best top share (None: not placed).
    ``above_controls``: search -> above every topic control of its era on that search."""
    shares = [s for s in best.values() if s is not None]
    if not shares:
        return "not placed"
    if any(
        s is not None and s <= c["yes_share"] and above_controls.get(k) for k, s in best.items()
    ):
        return "yes"
    if all(s > c["no_share"] for s in shares):
        return "no"
    return "cannot tell"


# ---- texts and grams ----------------------------------------------------------------------


def edition() -> dict[int, dict]:
    return {r["seq"]: r for r in map(json.loads, EDITION.read_text().splitlines())}


def masked_text(wanted: set[int]) -> str:
    """The paragraphs' King James-masked words, as ``reuse.rare.bom_text`` makes the whole book."""
    from segment.build import original_words

    spans = {r["id"]: r["spans"] for r in map(json.loads, KJV_SPANS.read_text().splitlines())}
    ed = edition()
    words: list[str] = []
    for s in sorted(wanted):
        words += original_words(ed[s]["text"], spans.get(f"bom:{s}", []))
    return " ".join(words)


def grams_of(text: str, n: int) -> set[int]:
    from reuse.rare import gram_ids, tokens

    return gram_ids(tokens(text), n)


def keepers() -> dict[str, dict]:
    """The card's rule set ``default``: registry works, kept copy, not sealed (registry year)."""
    return {
        r["work_id"]: r
        for r in registry.load().to_pylist()
        if r["kind"] == "work" and r["dup_keeper"] and not r["sealed"]
    }


def find_copies(patterns: dict[str, list[str]]) -> dict[str, list[str]]:
    from lab.claimed_sources import find_copies as fc

    cat = pq.read_table(CATALOG, columns=["work_id", "title", "author_norm"]).to_pylist()
    return fc(patterns, cat)


def topic_controls(c: dict, reg: dict[str, dict]) -> dict[str, list[str]]:
    """Era -> kept works with text whose catalogued title names the topic."""
    pat = re.compile(c["topic_pattern"], re.I)
    cat = door.catalog(set(reg))
    found: dict[str, list[str]] = {e: [] for e in c["eras"]}
    for w, r in reg.items():
        if not r["has_text"] or r["year"] is None or not pat.search(cat[w]["title"] or ""):
            continue
        for era, (lo, hi) in c["eras"].items():
            if lo <= r["year"] <= hi:
                found[era].append(w)
    return {e: sorted(v) for e, v in found.items()}


# ---- rare phrases -------------------------------------------------------------------------


def population(hits: Path, cfg: dict, sealed: set[str], want: set[int]) -> dict:
    """The stored scan's period population (as ``lab.claimed_sources.rare_table``), each volume's
    hits cut to ``want``, and every wanted gram's document frequency by text."""
    from metadata.dates import catalog_years, effective_year
    from reuse.rare import copy_clusters

    lo, hi = cfg["corpus"]["date_range"]
    years = catalog_years()
    recs = []
    for r in pq.read_table(hits).to_pylist():
        if not r["words"] or r["work_id"] in sealed:
            continue
        y = effective_year(r["work_id"], years.get(r["work_id"]))
        if y is not None and lo <= y <= hi:
            recs.append(r)
    key = copy_clusters(recs) if cfg["borrowing"]["df_by_text"] else {r["work_id"]: r["work_id"]
                                                                       for r in recs}  # fmt: skip
    by: dict[int, set] = {}
    cut: dict[str, set[int]] = {}
    for r in recs:
        h = set(r["hits"]) & want
        cut[r["work_id"]] = h
        for g in h:
            by.setdefault(g, set()).add(key[r["work_id"]])
    return {
        "hits": cut,
        "words": {r["work_id"]: r["words"] for r in recs},
        "key": key,
        "df": {g: len(v) for g, v in by.items()},
    }


def add_scan(pop: dict, extra: dict[str, set[int]]) -> None:
    """Merge another scan's hits (the plant grams) into the population and its frequencies."""
    by: dict[int, set] = {}
    for w, h in extra.items():
        if w not in pop["hits"]:
            continue
        pop["hits"][w] = pop["hits"][w] | h
        for g in h:
            by.setdefault(g, set()).add(pop["key"][w])
    for g, v in by.items():
        pop["df"][g] = len(v)


def densities(pop: dict, grams: set[int], max_df: int, per: int) -> dict[str, float]:
    rare = rare_grams(grams, pop["df"], max_df, outside=False)
    return {w: per * len(h & rare) / pop["words"][w] for w, h in pop["hits"].items()}


def outside_density(text: str, pop: dict, grams: set[int], cfg: dict) -> tuple[float, int, int]:
    """(density, rare shared grams, words) of a text that is not in the population."""
    from reuse.rare import gram_ids, tokens

    b = cfg["borrowing"]
    toks = tokens(text)
    shared = gram_ids(toks, b["ngram"]) & grams
    rare = rare_grams(shared, pop["df"], b["max_df"], outside=True)
    n = len(toks)
    return (b["per_words"] * len(rare) / n if n else 0.0), len(rare), n


def rare_place(score: float, pop_scores: np.ndarray, member: bool, n: int) -> dict:
    r = rank_against(score, pop_scores, member)
    return {"rank": r, "of": n, "top_share": round(r / n, 6), "per_10000_words": round(score, 4)}


# ---- plants -------------------------------------------------------------------------------


def draw_plants(cfg: dict) -> list[dict]:
    """Ten kept works in both populations with enough words; one index-cut passage from the
    middle of each. Returns rows with the passage text (private)."""
    from ocr_fix.normalize import norm_path
    from semantic.corpus import galleries
    from semantic.index import spans

    c = cfg["lab"]["nephi28_sources"]
    s = cfg["semantic"]
    reg = keepers()
    lo_y, hi_y = cfg["corpus"]["date_range"]
    in_scan = set(pq.read_table(BOM_HITS, columns=["work_id"])["work_id"].to_pylist())
    gallery = galleries(cfg)[0]["bom:window"]
    pool = sorted(w for w, r in reg.items() if w in in_scan and w in gallery and r["has_text"]
                  and r["year"] is not None and lo_y <= r["year"] <= hi_y
                  and (r["words"] or 0) >= c["plant_min_words"]
                  and r["in_passage_index"])  # fmt: skip
    rng = random.Random(c["seed"])
    rng.shuffle(pool)
    cat = door.catalog(set(pool[: c["plants"] * 5]))
    lo, hi = c["plant_middle"]
    plants = []
    for w in pool:
        if len(plants) == c["plants"]:
            break
        try:
            text = norm_path(cat[w]).read_text(encoding="utf-8", errors="replace")
        except (OSError, KeyError):
            continue  # unreadable: not drawn
        sp = spans(text, s["passage_words"], s["min_passage_words"])
        if len(sp) < 10:
            continue
        i = rng.randrange(int(len(sp) * lo), int(len(sp) * hi))
        a, b, _ = sp[i]
        plants.append({"plant": len(plants), "work_id": w, "passage": i,
                       "text": " ".join(text[a:b].split())})  # fmt: skip
    return plants


def _rows_for_scan(ids: set[str]) -> list[tuple[str, str]]:
    from ocr_fix.normalize import norm_path

    cat = door.catalog(ids)
    return [(w, str(norm_path(cat[w]))) for w in sorted(ids) if w in cat]


def plant_scan(cfg: dict) -> int:
    """Draw the plants (once) and scan the stored population for their 4-grams, in saved parts."""
    from reuse.rare import _scan_one

    c = cfg["lab"]["nephi28_sources"]
    n = cfg["borrowing"]["ngram"]
    if not PLANTS.exists():
        plants = draw_plants(cfg)
        out(PLANTS).write_text("".join(json.dumps(p) + "\n" for p in plants))
        print(f"{len(plants)} plants drawn -> {PLANTS}", flush=True)
    plants = [json.loads(ln) for ln in PLANTS.read_text().splitlines()]
    grams = set().union(*(grams_of(p["text"], n) for p in plants))
    gfile = out(WORK / "plant_grams.txt")
    gfile.write_text("\n".join(map(str, sorted(grams))))
    ids = set(pq.read_table(BOM_HITS, columns=["work_id"])["work_id"].to_pylist())
    rows = _rows_for_scan(ids)
    size = c["scan_part"]
    for k in range(0, len(rows), size):
        part = WORK / "plant_scan" / f"part_{k // size:04d}.parquet"
        if part.exists():
            continue
        jobs = [(w, p, n, str(gfile)) for w, p in rows[k : k + size]]
        with ProcessPoolExecutor(c["scan_workers"]) as pool:
            recs = [{"work_id": w, "words": m, "hits": h}
                    for w, m, h in pool.map(_scan_one, jobs, chunksize=32)]  # fmt: skip
        schema = pa.schema([("work_id", pa.string()), ("words", pa.int64()),
                            ("hits", pa.list_(pa.int64()))])  # fmt: skip
        tmp = out(part.with_suffix(".tmp"))
        pq.write_table(pa.Table.from_pylist(recs, schema=schema), tmp)
        tmp.rename(part)
        print(f"  part {k // size + 1}/{-(-len(rows) // size)}", flush=True)
    out(DONE).write_text(json.dumps({"volumes": len(rows), "plant_grams": len(grams)}) + "\n")
    print(f"plant scan done: {len(rows):,} volumes, {len(grams):,} plant grams")
    return 0


def plant_hits() -> dict[str, set[int]]:
    parts = sorted((WORK / "plant_scan").glob("part_*.parquet"))
    found: dict[str, set[int]] = {}
    for p in parts:
        for r in pq.read_table(p).to_pylist():
            if r["hits"]:
                found[r["work_id"]] = set(r["hits"])
    return found


# ---- meaning: one pass over the index -----------------------------------------------------


def query_sets(cfg: dict) -> dict[str, list[int]]:
    """Target -> the stored Book of Mormon query numbers with more than half their words in it."""
    from lab.claimed_sources import query_paragraphs, target_queries

    c = cfg["lab"]["nephi28_sources"]
    paras = query_paragraphs(cfg["semantic"]["passage_words"])
    return {k: target_queries(paras, seqs(c[k])) for k in ("target", "chapter_1830", "decoy")}


def plant_vectors(cfg: dict) -> tuple[np.ndarray, np.ndarray]:
    """The plant passages' vectors (the index's model) and their bars from the stored null."""
    from semantic.index import _model
    from semantic.search import _embed

    plants = [json.loads(ln) for ln in PLANTS.read_text().splitlines()]
    v = _embed(_model(cfg), [p["text"] for p in plants], cfg)
    null = np.load(SEARCH / "null_bom.npy").astype(np.float32)
    return v, (v @ null.T).max(axis=1)


def meaning_pass(cfg: dict) -> int:
    """Exact scores of every indexed passage against the targets' queries and the plants: each
    work's best passage per query, and each query's 100 best scores in the gallery."""
    from lab.passages import Index
    from semantic.corpus import galleries
    from semantic.index import INDEX

    if not PLANTS.exists():
        raise SystemExit("no plants yet: run `python -m lab.nephi28_sources plants` first")
    keep = cfg["semantic"]["keep"]
    qs = query_sets(cfg)
    stored = sorted(set().union(*qs.values()))
    z = np.load(SEARCH / "q_bom.npz")
    pv, pbar = plant_vectors(cfg)
    q = np.concatenate([z["q"][stored].astype(np.float32), pv]).astype(np.float32)
    ix = Index()
    ok = ix.allowed(galleries(cfg)[0]["bom:window"])
    nq = len(q)
    state = WORK / "meaning_state.npz"
    if state.exists():
        st = np.load(state)
        best, top, done = st["best"], st["top"], int(st["done"])
        if best.shape[1] != nq:
            raise SystemExit(f"{state}: made for {best.shape[1]} queries, now {nq}; move it aside")
    else:
        best = np.full((len(ix.works), nq), INF, dtype=np.float32)
        top = np.full((keep, nq), INF, dtype=np.float32)
        done = 0
    for si in range(done, len(ix.shards)):
        a, b = int(ix.starts[si]), int(ix.starts[si + 1])
        vec = np.load(INDEX / f"{ix.shards[si]['name']}.npy", mmap_mode="r")
        works = np.asarray(ix.rows[a:b])
        for c0 in range(0, b - a, 250_000):
            v = np.asarray(vec[c0 : c0 + 250_000], dtype=np.float32)
            w = works[c0 : c0 + 250_000]
            sc = v @ q.T
            starts = np.concatenate([[0], np.flatnonzero(np.diff(w)) + 1])
            np.maximum.at(best, w[starts], np.maximum.reduceat(sc, starts, axis=0))
            m = np.where(ok[w][:, None], sc, INF)
            k = min(keep, len(m))
            cand = np.concatenate([top, np.partition(m, len(m) - k, axis=0)[-k:]])
            top = np.partition(cand, len(cand) - keep, axis=0)[-keep:]
        if si % 10 == 9 or si == len(ix.shards) - 1:
            np.savez(out(WORK / "meaning_state.tmp.npz"), best=best, top=top, done=si + 1)
            (WORK / "meaning_state.tmp.npz").rename(state)
            print(f"  shard {si + 1}/{len(ix.shards)}", flush=True)
    np.savez(out(WORK / "meaning.npz"), best=best, cut=top.min(axis=0), stored=np.array(stored),
             plant_bar=pbar, works=np.array(ix.works))  # fmt: skip
    print(f"meaning pass done: {len(ix.works):,} works x {nq} queries -> {WORK / 'meaning.npz'}")
    return 0


class Meaning:
    """Each work's place for a set of query columns, from the index pass."""

    def __init__(self, cfg: dict) -> None:
        z = np.load(WORK / "meaning.npz")
        self.best, self.cut = z["best"], z["cut"]
        self.works = [str(w) for w in z["works"]]
        self.row = {w: i for i, w in enumerate(self.works)}
        self.stored = [int(x) for x in z["stored"]]
        qz = np.load(SEARCH / "q_bom.npz")
        self.col = {q: i for i, q in enumerate(self.stored)}
        n_plants = len(z["plant_bar"])
        self.bar = np.concatenate([qz["bar"][self.stored], z["plant_bar"]]).astype(np.float32)
        self.kjv = qz["kjv_share"]
        self.max_kjv = cfg["semantic"]["max_query_kjv_share"]
        self.plant_cols = list(range(len(self.stored), len(self.stored) + n_plants))
        self.stored_cut = np.load(SEARCH / "scan_state.npz")["bom|bom:window|s"].min(axis=1)

    def columns(self, queries: list[int]) -> tuple[list[int], int]:
        """Index columns of the scored queries, and how many were left out as King James."""
        scored = [q for q in queries if self.kjv[q] <= self.max_kjv]
        return [self.col[q] for q in scored], len(queries) - len(scored)

    def scores(self, cols: list[int], extra: np.ndarray | None = None) -> np.ndarray:
        """Every work's key for these columns; ``extra``: best scores of one more text."""
        b = self.best[:, cols] if extra is None else extra[None, :]
        places = ((b >= self.cut[cols]) & (b > self.bar[cols])).sum(axis=1)
        return meaning_key(places, b.mean(axis=1))

    def detail(self, w_or_scores: str | np.ndarray, cols: list[int]) -> dict:
        b = self.best[self.row[w_or_scores], cols] if isinstance(w_or_scores, str) else w_or_scores
        places = int(((b >= self.cut[cols]) & (b > self.bar[cols])).sum())
        return {"places": places, "mean_best": round(float(b.mean()), 4),
                "max_best": round(float(b.max()), 4)}  # fmt: skip


def outside_best(text: str, qv: np.ndarray, cfg: dict) -> np.ndarray | None:
    """A text outside the index: its passages' best score per query (None if too short)."""
    from semantic.index import _model
    from semantic.search import _embed, text_passages

    ps = text_passages(text, cfg)
    if not ps:
        return None
    v = _embed(_model(cfg), ps, cfg)
    return (qv @ v.T).max(axis=1)


# ---- the checks ---------------------------------------------------------------------------


def check_late_war(cfg: dict, n_words: int) -> dict:
    """Known answer: a chapter-size window of The Late War as the target; Hunt's other printings
    must come first."""
    from lab.claimed_sources import find_copies as fc
    from reuse.rare import STAND_IN, gram_ids, stand_in_text, tokens

    b = cfg["borrowing"]
    toks = tokens(stand_in_text())
    a, z = chapter_window(n_words, len(toks))
    want = gram_ids(toks[a:z], b["ngram"])
    pop = population(LATE_WAR_HITS, cfg, set(), want)
    dens = densities(pop, want, b["max_df"], b["per_words"])
    cat = pq.read_table(CATALOG, columns=["work_id", "title", "author_norm"]).to_pylist()
    printings = set(fc({"k": cfg["lab"]["claimed_sources"]["ka_late_war"]}, cat)["k"]) - {STAND_IN}
    printings &= set(dens)
    sharing = {w for w in printings if pop["hits"][w]}
    order = sorted(dens, key=lambda w: -dens[w])
    rank = {w: i + 1 for i, w in enumerate(order)}
    first_other = next((rank[w] for w in order if w not in printings), None)
    ranks = sorted(rank[w] for w in sharing)
    return {
        "window_words": z - a,
        "window_grams": len(want),
        "population": len(dens),
        "other_printings": len(printings),
        "printings_sharing_a_window_gram": len(sharing),
        "ranks": ranks,
        "printings_sharing_none": sorted(printings - sharing),
        "best_rank_of_any_other_volume": first_other,
        "passed": bool(ranks) and max(ranks) < (first_other or 10**9),
    }


def check_plants(cfg: dict, pop: dict, tgt: set[int], reg: dict, mean: Meaning,
                 tcols: list[int], gallery: set[str]) -> dict:  # fmt: skip
    """Known answer: each planted passage must bring its work into the top 1% of kept copies,
    on each search."""
    c = cfg["lab"]["nephi28_sources"]
    b = cfg["borrowing"]
    plants = [json.loads(ln) for ln in PLANTS.read_text().splitlines()]
    pop_ids = [w for w in pop["hits"] if w in reg]
    gal = [w for w in mean.works if w in reg and w in gallery]
    gal_rows = np.array([mean.row[w] for w in gal])
    rows = []
    for p, col in zip(plants, mean.plant_cols, strict=True):
        w = p["work_id"]
        pg = grams_of(p["text"], b["ngram"])
        dens = densities(pop, tgt | pg, b["max_df"], b["per_words"])
        scores = np.array([dens[x] for x in pop_ids])
        r_rare = rank_against(dens[w], scores, True) if w in dens else None
        key = mean.scores(tcols + [col])
        r_mean = rank_against(key[mean.row[w]], key[gal_rows], True) if w in mean.row else None
        rows.append({
            "plant": p["plant"], "work_id": w, "passage": p["passage"],
            "rare": None if r_rare is None else {"rank": r_rare, "of": len(pop_ids),
                                                 "top_share": round(r_rare / len(pop_ids), 6)},
            "meaning": None if r_mean is None else {"rank": r_mean, "of": len(gal),
                                                    "top_share": round(r_mean / len(gal), 6)},
        })  # fmt: skip
    hit = {k: sum(r[k] is not None and r[k]["top_share"] <= c["plant_top_share"] for r in rows)
           for k in ("rare", "meaning")}  # fmt: skip
    return {"plants": rows, "in_top_share": hit, "bar": c["plant_bar"],
            "passed": all(v >= c["plant_bar"] for v in hit.values())}  # fmt: skip


def check_cut(mean: Meaning, tol: float) -> dict:
    """Wiring: the pass's 100th-nearest score per stored query equals the study's stored one."""
    d = np.abs(mean.cut[: len(mean.stored)] - mean.stored_cut[mean.stored])
    return {"queries": len(mean.stored), "max_difference": round(float(d.max()), 6),
            "tolerance": tol, "passed": bool(d.max() <= tol)}  # fmt: skip


# ---- the run ------------------------------------------------------------------------------


def run(cfg: dict, only_check: bool = False) -> dict:
    from lab.claimed_sources import sealed_ids_of_scan
    from semantic.corpus import galleries

    c = cfg["lab"]["nephi28_sources"]
    b = cfg["borrowing"]
    if not DONE.exists():
        raise SystemExit("plant scan not finished: run `python -m lab.nephi28_sources plants`")
    if not (WORK / "meaning.npz").exists():
        raise SystemExit("no index pass yet: run `python -m lab.nephi28_sources meaning`")
    gallery = galleries(cfg)[0]["bom:window"]
    reg = keepers()
    years = dict(
        zip(*registry.load().select(["work_id", "year"]).to_pydict().values(), strict=True)
    )
    bom_grams = {int(x) for x in BOM_GRAMS.read_text().split()}
    targets = {k: seqs(c[k]) for k in ("target", "chapter_1830", "decoy")}
    words = {k: len(masked_text(v).split()) for k, v in targets.items()}
    grams = {k: grams_of(masked_text(v), b["ngram"]) & bom_grams for k, v in targets.items()}
    res: dict = {"settings": c, "known_answer": {}}
    ka = res["known_answer"]
    ka["late_war_window"] = check_late_war(cfg, words["target"])
    print("late war:", {k: v for k, v in ka["late_war_window"].items() if k != "ranks"}, flush=True)
    pop = population(BOM_HITS, cfg, sealed_ids_of_scan(), set().union(*grams.values()))
    add_scan(pop, plant_hits())
    mean = Meaning(cfg)
    ka["index_pass_reproduces_stored_cut"] = check_cut(mean, c["cut_tolerance"])
    print("cut:", ka["index_pass_reproduces_stored_cut"], flush=True)
    qsets = query_sets(cfg)
    cols = {k: mean.columns(v) for k, v in qsets.items()}
    ka["plants"] = check_plants(cfg, pop, grams["target"], reg, mean, cols["target"][0], gallery)
    print("plants:", ka["plants"]["in_top_share"], flush=True)
    checks = ("late_war_window", "index_pass_reproduces_stored_cut", "plants")
    ka["passed"] = all(ka[k]["passed"] for k in checks)
    if only_check or not ka["passed"]:
        if not ka["passed"]:
            res["stopped"] = "the known-answer check missed its bar; the chapter was not looked up"
        return res

    # populations of kept copies
    ctx = {
        "cfg": cfg, "reg": reg, "pop": pop, "mean": mean, "gallery": gallery, "years": years,
        "pop_ids": [w for w in pop["hits"] if w in reg],
        "gal": [w for w in mean.works if w in reg and w in gallery],
        "named": find_copies(c["named"]), "controls": topic_controls(c, reg),
        "q": np.load(SEARCH / "q_bom.npz"),
    }  # fmt: skip
    ctx["gal_rows"] = np.array([mean.row[w] for w in ctx["gal"]])
    ctx["cat"] = door.catalog(set().union(*ctx["named"].values(), *ctx["controls"].values()))
    res["populations"] = {
        "rare_phrases_kept_copies": len(ctx["pop_ids"]),
        "meaning_gallery_kept_copies": len(ctx["gal"]),
        "topic_controls": {e: len(v) for e, v in ctx["controls"].items()},
    }
    res["targets"] = {t: one_target(ctx, t, grams[t], words[t], qsets[t], cols[t]) for t in targets}
    tgt = res["targets"]["target"]
    named_rows = {**tgt["named"], **{k: v for k, v in tgt["outside"].items() if "verdict" in v}}
    dec = res["targets"]["decoy"]
    res["decoy_puts_named_high"] = {
        k: [s for s in ("rare", "meaning") if (v.get("best") or {}).get(s) is not None
            and v["best"][s]["top_share"] <= c["decoy_high_share"]]
        for k, v in {**dec["named"], **dec["outside"]}.items() if "best" in v
    }  # fmt: skip
    verdicts = {k: v["verdict"] for k, v in named_rows.items()}
    res["answer"] = (
        "yes: " + ", ".join(k for k, v in verdicts.items() if v == "yes")
        if "yes" in verdicts.values()
        else "no"
        if verdicts and all(v == "no" for v in verdicts.values())
        else "cannot tell"
    )
    res["not_done"] = [
        f"{k}: not held (Google Books only); link in settings.outside"
        for k in c["outside"]
        if "verdict" not in tgt["outside"].get(k, {})
    ]
    return res


def era_of(year: int | None, eras: dict[str, list[int]]) -> str:
    for e, (lo, hi) in eras.items():
        if year is not None and lo <= year <= hi:
            return e
    return "late"


def one_target(ctx: dict, t: str, grams: set[int], n_words: int, queries: list[int],
               cols: tuple[list[int], int]) -> dict:  # fmt: skip
    """Every named text, outside text and topic control placed for one target."""
    cfg, reg, pop, mean = ctx["cfg"], ctx["reg"], ctx["pop"], ctx["mean"]
    c, b = cfg["lab"]["nephi28_sources"], cfg["borrowing"]
    pop_ids, gal, gallery = ctx["pop_ids"], ctx["gal"], ctx["gallery"]
    tc, left_out = cols
    dens = densities(pop, grams, b["max_df"], b["per_words"])
    rare_scores = np.array([dens[w] for w in pop_ids])
    key = mean.scores(tc)
    gal_keys = key[ctx["gal_rows"]]
    z = ctx["q"]
    qv = z["q"][[q for q in queries if z["kjv_share"][q] <= mean.max_kjv]].astype(np.float32)

    def meaning_place(kk: float, member: bool, detail: dict, **flags) -> dict:
        r = rank_against(kk, gal_keys, member)
        return {"rank": r, "of": len(gal), "top_share": round(r / len(gal), 6), **detail, **flags}

    def place(w: str, text: str | None = None) -> dict:
        row: dict = {"work_id": w}
        if text is None and w in dens:
            row["rare"] = rare_place(dens[w], rare_scores, w in reg, len(pop_ids))
            row["rare"]["shared_rare_grams"] = round(dens[w] * pop["words"][w] / b["per_words"])
        else:
            try:
                txt = text if text is not None else door.text_of(ctx["cat"][w])
            except (OSError, KeyError):
                txt = None
            if txt is None:
                row["rare"] = "unreadable: not attempted"
            else:
                d, k, n = outside_density(txt, pop, grams, cfg)
                row["rare"] = rare_place(d, rare_scores, False, len(pop_ids))
                row["rare"] |= {"shared_rare_grams": k, "outside_population": True, "words": n}
        if text is None and w in mean.row:
            member = w in reg and w in gallery
            row["meaning"] = meaning_place(float(key[mean.row[w]]), member, mean.detail(w, tc),
                                           in_gallery=w in gallery)  # fmt: skip
        elif text is not None:
            ob = outside_best(text, qv, cfg)
            if ob is None:
                row["meaning"] = "too short: not attempted"
            else:
                kk = float(mean.scores(tc, ob)[0])
                row["meaning"] = meaning_place(kk, False, mean.detail(ob, tc), outside_index=True)
        else:
            row["meaning"] = "not in the passage index: not attempted"
        return row

    ctl = {e: [place(w) for w in ids] for e, ids in ctx["controls"].items()}

    def against_controls(row: dict, era: str) -> dict:
        got = {}
        for s in ("rare", "meaning"):
            if not isinstance(row.get(s), dict):
                continue
            cr = [r[s]["rank"] for r in ctl[era] if isinstance(r[s], dict)]
            beaten = sum(row[s]["rank"] < x for x in cr)
            got[s] = {"above_every_control": beaten == len(cr),
                      "share_of_controls_beaten": round(beaten / max(len(cr), 1), 4)}  # fmt: skip
        return got

    res: dict = {
        "paragraphs_1830": c[t], "masked_words": n_words, "grams": len(grams),
        "rare_grams": len(rare_grams(grams, pop["df"], b["max_df"], False)),
        "queries": len(queries), "queries_scored": len(tc),
        "queries_left_out_as_king_james": left_out,
        "rare_top": [{"work_id": w, "per_10000_words": round(dens[w], 4)}
                     for w in sorted(pop_ids, key=lambda w: -dens[w])[:15]],
        "meaning_top": [{"work_id": gal[i], **mean.detail(gal[i], tc)}
                        for i in np.argsort(-gal_keys, kind="stable")[:15]],
        "named": {}, "outside": {}, "controls": {},
    }  # fmt: skip
    for e, rows in ctl.items():
        summ = {}
        for s in ("rare", "meaning"):
            ok = [r for r in rows if isinstance(r[s], dict)]
            shares = [r[s]["top_share"] for r in ok]
            summ[s] = {
                "placed": len(ok),
                "not_attempted": len(rows) - len(ok),
                "best": sorted(({"work_id": r["work_id"], **r[s]} for r in ok),
                               key=lambda x: x["rank"])[:10],
                "median_top_share": round(float(np.median(shares)), 6) if ok else None,
                "in_top_yes_share": sum(x <= c["yes_share"] for x in shares),
                "in_top_no_share": sum(x <= c["no_share"] for x in shares),
            }  # fmt: skip
        res["controls"][e] = summ
    for k, ids in ctx["named"].items():
        copies = []
        for w in ids:
            r = place(w)
            r["year"] = ctx["years"].get(w)
            r["kept_copy"] = w in reg
            r["controls"] = against_controls(r, era_of(r["year"], c["eras"]))
            copies.append(r)
        res["named"][k] = summarise(copies, c)
    for k, link in c["outside"].items():
        p = Path(c["outside_dir"]) / f"{k}.txt"
        if not p.exists():
            res["outside"][k] = {"status": "not held: not attempted", "link": link}
            continue
        r = place(k, p.read_text(encoding="utf-8", errors="replace"))
        r["controls"] = against_controls(r, "late")
        res["outside"][k] = summarise([r], c)
    return res


def summarise(copies: list[dict], c: dict) -> dict:
    """A named text: every copy, its best copy per search, and the card's verdict."""
    best, above = {}, {}
    for s in ("rare", "meaning"):
        ok = [x for x in copies if isinstance(x.get(s), dict)]
        if not ok:
            best[s] = None
            continue
        top = min(ok, key=lambda x: x[s]["rank"])
        best[s] = {"work_id": top["work_id"], **top[s]}
        above[s] = top.get("controls", {}).get(s, {}).get("above_every_control", False)
    shares = {s: (v["top_share"] if v else None) for s, v in best.items()}
    return {"copies": copies, "best": best, "verdict": verdict(shares, above, c)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["plants", "meaning", "check", "run"])
    a = ap.parse_args(argv)
    cfg = config.load()
    if a.cmd == "plants":
        return plant_scan(cfg)
    if a.cmd == "meaning":
        return meaning_pass(cfg)
    res = run(cfg, only_check=a.cmd == "check")
    res["config_sha256"] = config.sha256_of_config()
    res["commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    name = "check.json" if a.cmd == "check" else "result.json"
    out(OUT / name).write_text(json.dumps(res, indent=1, default=_plain) + "\n")
    print(json.dumps({k: res[k] for k in ("answer", "decoy_puts_named_high") if k in res}))
    return 0


def _plain(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    raise TypeError(type(x))


if __name__ == "__main__":
    raise SystemExit(main())
