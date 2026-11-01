"""Rare-phrase scoring, and sizing the null it is judged against (BOM-45; part of BOM-24).

5.5: for each 4-gram in a target text, its document frequency across the corpus; a volume's score
is the length-normalised count of shared 4-grams whose document frequency is at most
``borrowing.max_df`` (5). 6.5: a source is a significant parallel if its score is above the 99th
percentile of a null built from at least 500 period volumes, stratified by genre.

BOM-45 asks how big that null must be for its 99th percentile not to be mostly noise. The
answer depends on the shape of the score distribution, not on which text is the target, so it is
measured against a stand-in, Gilbert Hunt's *The Late War* (KJV-masked), and the Book of Mormon
is not touched until the null is fixed.

``scan`` makes one pass over every period volume and records which target 4-grams each contains;
document frequencies and every volume's score follow from that. ``size`` draws genre-stratified
samples of n volumes from those scores, 1,000 times per n, and reports the spread of the 99th
percentile. The chosen n is the smallest whose 95% interval lies within ``tolerance`` of the
threshold (Amendment 7 Change 6).

``score`` and ``known`` are BOM-24 (plan ``docs/rare-plan.md``): the ranked source list of the
Book of Mormon against the whole period population, and the known-answer score of Amendment 9.

Usage::

    python -m reuse.rare scan [--workers 8]
    python -m reuse.rare size
    python -m reuse.rare score                 # -> data/reuse/bom/rare.json
    python -m reuse.rare known [--workers 8]   # -> data/reuse/rare_known/known_answer.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kjv_mask.align import _WORD
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/reuse/null_sizing")
HITS = OUT / "hits.parquet"
STAND_IN = "internet_archive:latewarbetween_00hunt"


def tokens(text: str) -> list[str]:
    """Amendment 2's tokenisation (as KJV masking): NFKC, lowercase, word characters."""
    import unicodedata

    return [m.group(0).lower() for m in _WORD.finditer(unicodedata.normalize("NFKC", text))]


def gram_ids(toks: list[str], n: int) -> set[int]:
    """Hashed ``n``-grams (``borrowing.ngram``; 5.5 registers 4)."""
    out = set()
    for i in range(len(toks) - n + 1):
        h = hashlib.blake2b(" ".join(toks[i : i + n]).encode(), digest_size=8).digest()
        out.add(int.from_bytes(h, "big") >> 1)
    return out


def stand_in_text() -> str:
    from ocr_fix.normalize import norm_path
    from segment.build import original_words

    cat = pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
    ).to_pylist()
    row = next(r for r in cat if r["work_id"] == STAND_IN)
    prefix = json.dumps({"id": STAND_IN})[:-1]
    spans_file = Path("data/kjv_mask/controls/spans.jsonl")
    spans = next(json.loads(ln)["spans"] for ln in spans_file.open() if ln.startswith(prefix))
    text = norm_path(row).read_text(encoding="utf-8", errors="replace")
    return " ".join(original_words(text, spans))


def bom_text() -> str:
    """The 1830 text with BOM-16's KJV spans removed (the Johnsons removed biblical matches)."""
    from segment.build import original_words

    spans = {}
    for ln in Path("data/kjv_mask/bom/spans.jsonl").read_text().splitlines():
        r = json.loads(ln)
        spans[r["id"]] = r["spans"]
    words = []
    for ln in Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines():
        r = json.loads(ln)
        if r["book"]:
            words += original_words(r["text"], spans.get(f"bom:{r['seq']}", []))
    return " ".join(words)


# target -> (output directory, its text, the ids of its own copies to leave out of the scan)
TARGETS = {
    "stand_in": (OUT, stand_in_text, lambda: {STAND_IN}),
    "bom": (
        Path("data/reuse/bom"),
        bom_text,
        lambda: __import__("metadata.sealed", fromlist=["sealed_ids"]).sealed_ids(),
    ),
}

_TARGET: dict[str, set[int]] = {}


def _scan_one(job: tuple[str, str, int, str]) -> tuple[str, int, list[int]]:
    wid, path, n, grams = job
    if grams not in _TARGET:
        _TARGET[grams] = {int(x) for x in Path(grams).read_text().split()}
    try:
        toks = tokens(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return wid, 0, []
    return wid, len(toks), sorted(gram_ids(toks, n) & _TARGET[grams])


def scan(workers: int, target_name: str = "stand_in") -> int:
    from metadata.pseudo_biblical import eligible_rows
    from ocr_fix.normalize import norm_path

    out_dir, text_of, copies_of = TARGETS[target_name]
    out_dir.mkdir(parents=True, exist_ok=True)
    n = load_config()["borrowing"]["ngram"]
    target = gram_ids(tokens(text_of()), n)
    grams = out_dir / "target_grams.txt"
    grams.write_text("\n".join(map(str, sorted(target))))
    own = copies_of()
    rows = [r for r in eligible_rows(load_config()) if r["work_id"] not in own]
    jobs = [(r["work_id"], str(norm_path(r)), n, str(grams)) for r in rows]
    print(
        f"{target_name}: {len(target):,} distinct {n}-grams; {len(jobs):,} volumes "
        f"({len(own)} own copies left out)",
        flush=True,
    )
    start, recs = time.time(), []
    with ProcessPoolExecutor(workers) as pool:
        for i, (wid, n, hit) in enumerate(pool.map(_scan_one, jobs, chunksize=32), 1):
            recs.append({"work_id": wid, "words": n, "hits": hit})
            if i % 20000 == 0:
                print(f"  {i:,}/{len(jobs):,}  {i / (time.time() - start):.0f}/s", flush=True)
    schema = pa.schema(
        [("work_id", pa.string()), ("words", pa.int64()), ("hits", pa.list_(pa.int64()))]
    )
    pq.write_table(
        pa.Table.from_pylist(recs, schema=schema).replace_schema_metadata(
            {"config_sha256": stamp()["config_sha256"]}
        ),
        out_dir / "hits.parquet",
    )
    print(f"scanned {len(recs):,} in {time.time() - start:.0f}s -> {out_dir / 'hits.parquet'}")
    return 0


def target_copies(recs: list[dict]) -> set[str]:
    """The stand-in's own copies and editions. They must not count towards a 4-gram's document
    frequency: seven missed copies of The Late War made its distinctive phrases look common
    (document frequency 6-9) and the null collapsed to zero. For the Book of Mormon the sealed
    copies (4.2) play this part."""
    import re

    meta = {
        r["work_id"]: r
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "author_norm", "title"]
        ).to_pylist()
    }
    late_war = re.compile(r"late war.{0,80}(1812|britain)", re.I)
    return {
        r["work_id"]
        for r in recs
        if (meta[r["work_id"]]["author_norm"] or "").startswith("hunt, gilbert")
        or late_war.search(meta[r["work_id"]]["title"] or "")
    }


def scores(recs: list[dict], max_df: int, per_words: int) -> dict[str, float]:
    """Rare shared 4-grams per ``per_words`` words of the volume (5.5's length normalisation)."""
    df: Counter = Counter()
    for r in recs:
        df.update(r["hits"])
    rare = {g for g, n in df.items() if n <= max_df}
    return {
        r["work_id"]: per_words * sum(g in rare for g in r["hits"]) / r["words"]
        for r in recs
        if r["words"] > 0
    }


def size() -> int:
    cfg = load_config()
    b = cfg["borrowing"]
    from metadata.dates import effective_year

    lo, hi = cfg["corpus"]["date_range"]
    years = {
        r["work_id"]: r["year"]
        for r in pq.read_table(
            "data/catalog/catalog.parquet", columns=["work_id", "year"]
        ).to_pylist()
    }
    # BOM-56: the scan predates the date check; volumes whose corrected year is out of the window
    # still count towards document frequency (they are real books) but are not drawn for the null
    recs = pq.read_table(HITS).to_pylist()
    copies = target_copies(recs)
    recs = [r for r in recs if r["work_id"] not in copies]
    sc = scores(recs, b["max_df"], b["per_words"])
    sc = {
        w: v
        for w, v in sc.items()
        if (y := effective_year(w, years.get(w))) is not None and lo <= y <= hi
    }
    genre = {
        r["work_id"]: (r["genre"] or "uncertain").split(",")[0]
        for r in pq.read_table("data/catalog/genre.parquet").to_pylist()
    }
    strata: dict[str, list[float]] = defaultdict(list)
    for w, s in sc.items():
        strata[genre.get(w, "uncertain")].append(s)
    total = sum(len(v) for v in strata.values())
    arrays = {g: np.array(v) for g, v in strata.items()}
    rng = np.random.default_rng(derive_seed("null-sizing", cfg))
    population = np.percentile(np.concatenate(list(arrays.values())), b["null_percentile"])
    curve = {}
    for n in b["null_sizing"]["sizes"]:
        q = []
        for _ in range(b["null_sizing"]["draws"]):
            draw = np.concatenate(
                [
                    rng.choice(a, size=max(1, round(n * len(a) / total)), replace=False)
                    for a in arrays.values()
                    if len(a)
                ]
            )
            q.append(np.percentile(draw, b["null_percentile"]))
        q = np.array(q)
        lo, hi = np.percentile(q, [2.5, 97.5])
        med = float(np.median(q))
        curve[str(n)] = {
            "median": med,
            "sd": float(q.std()),
            "ci95": [float(lo), float(hi)],
            "half_width_rel": float((hi - lo) / 2 / med) if med > 0 else None,
        }
    tol = b["null_sizing"]["tolerance"]
    chosen = next(
        (
            int(n)
            for n, c in curve.items()
            if c["half_width_rel"] is not None and c["half_width_rel"] <= tol
        ),
        None,
    )
    result = {
        **stamp(),
        "stand_in": STAND_IN,
        "volumes": total,
        "population_threshold": float(population),
        "per_stratum": {g: len(v) for g, v in strata.items()},
        "curve": curve,
        "tolerance": tol,
        "chosen_n": chosen,
        "target_copies_excluded": len(copies),
        "share_nonzero": float(np.mean(np.concatenate(list(arrays.values())) > 0)),
    }
    (OUT / "sizing.json").write_text(json.dumps(result, indent=1) + "\n")
    for n, c in curve.items():
        hw = "n/a" if c["half_width_rel"] is None else f"+/-{c['half_width_rel']:.0%}"
        print(
            f"  n={int(n):>6,}  99th pct {c['median']:.3f}  95% CI {c['ci95'][0]:.3f}-"
            f"{c['ci95'][1]:.3f}  ({hw})"
        )
    print(f"population threshold {population:.3f}; chosen n = {chosen}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--target", choices=sorted(TARGETS), default="stand_in")
    s.add_argument("--workers", type=int, default=8)
    sub.add_parser("size")
    sub.add_parser("score")
    k = sub.add_parser("known")
    k.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    if a.cmd == "score":
        return score()
    if a.cmd == "known":
        return known(a.workers)
    return scan(a.workers, a.target) if a.cmd == "scan" else size()


def copy_clusters(recs: list[dict]) -> dict[str, str]:
    """Each volume's copy group, by content: two volumes are copies of one text when the sets of
    target grams they share overlap by ``borrowing.copy_jaccard`` or more. Titles cannot
    decide this (a multi-volume work's volumes share a title and differ in text; a periodical's
    issues too), and the deduplication missed the nine printings of Hunt's *The Late War*.
    Candidate pairs come from grams few volumes carry, so the comparison stays tractable.
    Returns volume -> group id (the smallest member id)."""
    from collections import Counter

    rp = load_config()["borrowing"]  # Amendment 8 Change 3
    jaccard, min_hits = rp["copy_jaccard"], rp["copy_min_hits"]
    index_df, min_common = rp["copy_index_df"], rp["copy_min_common"]
    hits = {r["work_id"]: set(r["hits"]) for r in recs if len(r["hits"]) >= min_hits}
    index: dict[int, list[str]] = {}
    for w, h in hits.items():
        for g in h:
            index.setdefault(g, []).append(w)
    pairs: Counter = Counter()
    for vols in index.values():
        if 1 < len(vols) <= index_df:
            vols = sorted(vols)
            for i, a in enumerate(vols):
                for b in vols[i + 1 :]:
                    pairs[(a, b)] += 1
    parent = {w: w for w in (r["work_id"] for r in recs)}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), n in pairs.items():
        if n < min_common:
            continue
        ha, hb = hits[a], hits[b]
        if len(ha & hb) / len(ha | hb) >= jaccard:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[max(ra, rb)] = min(ra, rb)
    return {w: find(w) for w in parent}


# BOM-24 --------------------------------------------------------------------------------------

BOM_OUT = Path("data/reuse/bom/rare.json")
KNOWN = Path("data/reuse/rare_known")
CURATED = Path("data/controls/pseudo_biblical_curated.txt")
SPALDING = Path("data/candidates/clean/ss-manuscript-story-1885.txt")
SEAL_CHECK = Path("data/reuse/bom/sealed_check.json")


def _seal_one(job: tuple[str, str]) -> tuple[str, int]:
    from metadata.sealed import shared_strings

    wid, path = job
    try:
        return wid, shared_strings(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return wid, -1


def seal_check(ids: list[str], workers: int = 6) -> dict[str, int]:
    """4.2's contamination check on every scanned volume: distinct 12-token Book of Mormon
    original strings each holds (cached; ids and counts only). Volumes at or over
    ``metadata.sealed.MIN_SHARED`` are kept out of the population, null and frequencies."""
    from metadata.pseudo_biblical import CATALOG
    from ocr_fix.normalize import norm_path

    done = json.loads(SEAL_CHECK.read_text())["counts"] if SEAL_CHECK.exists() else {}
    todo = [w for w in ids if w not in done]
    if todo:
        want = set(todo)
        rows = [r for r in pq.read_table(CATALOG).to_pylist() if r["work_id"] in want]
        print(f"seal check: {len(rows):,} volumes", flush=True)
        with ProcessPoolExecutor(workers) as pool:
            jobs = [(r["work_id"], str(norm_path(r))) for r in rows]
            for i, (w, c) in enumerate(pool.map(_seal_one, jobs, chunksize=64), 1):
                done[w] = c
                if i % 20000 == 0:
                    print(f"  {i:,}/{len(rows):,}", flush=True)
        SEAL_CHECK.write_text(json.dumps({**stamp(), "counts": done}) + "\n")
    return done


def doc_freq(recs: list[dict], by_text: bool) -> Counter:
    """Document frequency of each gram over ``recs``: by volume, or by text (copies collapsed by
    ``copy_clusters``, Amendment 8 Change 3)."""
    if not by_text:
        df: Counter = Counter()
        for r in recs:
            df.update(r["hits"])
        return df
    key = copy_clusters(recs)
    by: dict[int, set] = {}
    for r in recs:
        for g in r["hits"]:
            by.setdefault(g, set()).add(key[r["work_id"]])
    return Counter({g: len(v) for g, v in by.items()})


def densities(recs: list[dict], rare: set[int], per: int) -> dict[str, float]:
    return {r["work_id"]: per * sum(g in rare for g in r["hits"]) / r["words"] for r in recs}


def p_value(null: np.ndarray, x: float) -> float:
    """Empirical p, ties counted against the source (Amendment 7 Change 6)."""
    return float(((null >= x).sum() + 1) / (len(null) + 1))


def _blocks(text: str, n: int, size: int) -> list[set[int]]:
    toks = tokens(text)
    return [gram_ids(toks[i : i + size + n - 1], n) for i in range(0, len(toks), size)]


def _bootstrap(recs, rare, blocks, cfg, wanted):
    """Resample the target's blocks; each resample re-counts every volume's rare shared grams by
    the resampled multiplicities (document frequencies unchanged). Returns, for each wanted
    volume, the 95% intervals of its density and of its p-value in the population."""
    b = cfg["borrowing"]
    from scipy.sparse import csr_matrix

    gid = {g: i for i, g in enumerate(sorted(rare))}
    member = np.zeros((len(blocks), len(gid)), dtype=np.float32)
    for j, bl in enumerate(blocks):
        for g in bl & rare:
            member[j, gid[g]] = 1
    rows, cols = [], []
    for i, r in enumerate(recs):
        for g in r["hits"]:
            if g in gid:
                rows.append(i)
                cols.append(gid[g])
    m = csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                   shape=(len(recs), len(gid)))  # fmt: skip
    words = np.array([r["words"] for r in recs], dtype=float)
    pos = {r["work_id"]: i for i, r in enumerate(recs)}
    rng = np.random.default_rng(derive_seed(b["bootstrap_seed"], cfg))
    dens: dict[str, list[float]] = {w: [] for w in wanted}
    ps: dict[str, list[float]] = {w: [] for w in wanted}
    for _ in range(b["bootstrap"]):
        weight = member[rng.integers(0, len(blocks), len(blocks))].sum(axis=0)
        d = b["per_words"] * (m @ weight) / words
        srt = np.sort(d)
        for w in wanted:
            x = d[pos[w]]
            dens[w].append(x)
            ps[w].append((len(srt) - np.searchsorted(srt, x, "left") + 1) / (len(srt) + 1))
    ci = lambda v: [float(q) for q in np.percentile(v, [2.5, 97.5])]  # noqa: E731
    return {w: {"density_ci95": ci(dens[w]), "p_ci95": ci(ps[w])} for w in wanted}


def score() -> int:
    """The ranked source list (docs/rare-plan.md): registered score and p by text, the by-volume
    count beside it, the genre percentile, bootstrap intervals, the volumes BOM-64 moved, the
    named sources, and imitation scripture as a group (points 2-5 post hoc)."""
    import re

    from eval.replicate import NAMED_SOURCES
    from metadata.dates import catalog_years, effective_year
    from metadata.pseudo_biblical import CATALOG, VOLUMES

    cfg = load_config()
    b = cfg["borrowing"]
    n, per = b["ngram"], b["per_words"]
    lo, hi = cfg["corpus"]["date_range"]
    years = catalog_years()
    from metadata.sealed import MIN_SHARED

    all_recs = [r for r in pq.read_table("data/reuse/bom/hits.parquet").to_pylist() if r["words"]]
    seal = seal_check([r["work_id"] for r in all_recs])
    sealed = {w for w, c in seal.items() if c >= MIN_SHARED}
    sealed_rows = [{"work_id": r["work_id"], "strings": seal[r["work_id"]]}
                   for r in all_recs if r["work_id"] in sealed]  # fmt: skip
    all_recs = [r for r in all_recs if r["work_id"] not in sealed]
    eff = {r["work_id"]: effective_year(r["work_id"], years.get(r["work_id"])) for r in all_recs}
    recs = [r for r in all_recs if eff[r["work_id"]] is not None and lo <= eff[r["work_id"]] <= hi]
    moved = [r for r in all_recs if not (eff[r["work_id"]] and lo <= eff[r["work_id"]] <= hi)]
    cols = ["work_id", "title", "author_norm"]
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG, columns=cols).to_pylist()}
    genre = {r["work_id"]: (r["genre"] or "uncertain").split(",")[0]
             for r in pq.read_table("data/catalog/genre.parquet").to_pylist()}  # fmt: skip
    genre = {w: ("uncertain" if g in ("PARSE_FAIL", "uncertain") else g) for w, g in genre.items()}
    cer = {r["work_id"]: r["est_cer_clean"] for r in pq.read_table(VOLUMES).to_pylist()}

    variants = {}
    for name, by_text in (("by_text", True), ("by_volume", False)):
        df = doc_freq(recs, by_text)
        rare = {g for g, c in df.items() if c <= b["max_df"]}
        variants[name] = (rare, densities(recs, rare, per), densities(moved, rare, per))
    rare, dens, dens_moved = variants["by_text" if b["df_by_text"] else "by_volume"]
    null = np.array(list(dens.values()))
    strata: dict[str, list[float]] = defaultdict(list)
    for w, d in dens.items():
        strata[genre.get(w, "uncertain")].append(d)
    strata_a = {g: np.array(v) for g, v in strata.items()}
    order = sorted(dens, key=lambda w: -dens[w])
    rank = {w: i + 1 for i, w in enumerate(order)}
    hits = {r["work_id"]: r["hits"] for r in all_recs}

    # phrases: the target's own 4-grams by hash (Book of Mormon text, at most 4 words each)
    toks = tokens(bom_text())
    phrase = {}
    for i in range(len(toks) - n + 1):
        g = " ".join(toks[i : i + n])
        phrase.setdefault(next(iter(gram_ids(g.split(), n))), g)

    def row(w: str, d: dict = dens) -> dict:
        g = genre.get(w, "uncertain")
        shared = sorted(phrase.get(x, "?") for x in hits[w] if x in rare)
        return {"work_id": w, "title": (cat[w]["title"] or "")[:120],
                "author": cat[w]["author_norm"],
                "catalog_year": years.get(w), "year": eff[w], "genre": g, "est_cer": cer.get(w),
                "density": d[w], "shared": len(shared),
                "p": p_value(null, d[w]), "genre_p": p_value(strata_a.get(g, null), d[w]),
                "by_volume": {"density": variants["by_volume"][1].get(w),
                              "p": p_value(np.array(list(variants["by_volume"][1].values())),
                                           variants["by_volume"][1][w]) if w in dens else None},
                "rank": rank.get(w), "phrases": shared[:60]}  # fmt: skip

    named = {}
    pats = {**NAMED_SOURCES, "view_of_the_hebrews": r"view of the hebrews"}
    for key, pat in pats.items():
        cands = [w for w in dens if re.search(pat, cat[w]["title"] or "", re.I)]
        best = min(cands, key=lambda w: rank[w]) if cands else None
        named[key] = None if best is None else {**row(best), "copies_in_population": len(cands)}
    target = gram_ids(toks, n)

    def outside(text: str) -> dict:
        tt = tokens(text)
        shared = gram_ids(tt, n) & target & rare
        d = per * len(shared) / len(tt)
        return {"words": len(tt), "shared": len(shared), "density": d, "p": p_value(null, d),
                "phrases": sorted(phrase.get(x, "?") for x in shared)[:60]}  # fmt: skip

    luke = " ".join(json.loads(x)["text"] for x in Path("data/kjv/kjv.jsonl").read_text()
                    .splitlines() if json.loads(x)["book"] == "LUK")  # fmt: skip
    named["luke_kjv"] = outside(luke)
    named["spalding_manuscript_story"] = outside(SPALDING.read_text(encoding="utf-8"))

    curated = [w for w in CURATED.read_text().split() if w in dens]
    lw = named["the_late_war"]
    group = sorted([w for w in curated] + ([lw["work_id"]] if lw else []), key=lambda w: -dens[w])
    imitation = {"members": len(curated), "ranking": [
        {"work_id": w, "title": (cat[w]["title"] or "")[:80], "density": dens[w],
         "shared": sum(x in rare for x in hits[w])} for w in group]}  # fmt: skip

    top = order[:100]
    wanted = sorted(set(top) | {v["work_id"] for v in named.values() if v and "work_id" in v}
                    | set(curated))  # fmt: skip
    blocks = _blocks(bom_text(), n, b["block_words"])
    ci = _bootstrap(recs, rare, blocks, cfg, wanted)
    sig = [w for w in order if p_value(null, dens[w]) <= 1 - b["null_percentile"] / 100]
    out = {
        **stamp(), "population": len(recs), "moved_volumes": len(moved),
        "sealed_out": len(sealed_rows),
        "rare_grams": len(rare), "rare_rule": f"df <= {b['max_df']} "
        + ("by text" if b["df_by_text"] else "by volume"),
        "null_p99_density": float(np.percentile(null, b["null_percentile"])),
        "significant": len(sig),
        "top": [{**row(w), **ci[w]} for w in top],
        "named": {k: (None if v is None else {**v, **ci.get(v.get("work_id"), {})})
                  for k, v in named.items()},
        "imitation_scripture": imitation,
        "sealed": [{**x, "title": (cat[x["work_id"]]["title"] or "")[:100],
                    "catalog_year": years.get(x["work_id"])}
                   for x in sorted(sealed_rows, key=lambda x: -x["strings"])],
        "moved": [row(w, dens_moved)
                  for w in sorted(dens_moved, key=lambda w: -dens_moved[w])[:50]],
    }  # fmt: skip
    BOM_OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"{len(recs):,} volumes, {len(rare):,} rare grams, {len(sig)} significant; "
          f"99th pct {out['null_p99_density']:.3f}")  # fmt: skip
    for k, v in out["named"].items():
        if v:
            print(f"  {k}: density {v['density']:.3f}, shared {v['shared']}, p {v['p']:.4f}")
    print(f"-> {BOM_OUT}")
    return 0


def _known_one(job: tuple[str, str, list[str], str]) -> tuple[str, int, dict[str, list[int]]]:
    wid, path, keys, gram_dir = job
    if gram_dir not in _TARGET:
        for p in Path(gram_dir).glob("*.txt"):
            _TARGET[f"{gram_dir}/{p.stem}"] = {int(x) for x in p.read_text().split()}
        _TARGET[gram_dir] = set()
    try:
        toks = tokens(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return wid, 0, {}
    g = gram_ids(toks, load_config()["borrowing"]["ngram"])
    return wid, len(toks), {k: sorted(g & _TARGET[f"{gram_dir}/{k}"]) for k in keys}


def known(workers: int) -> int:
    """Amendment 9's score for rare phrases: in each of BOM-23's matched draws, document frequency
    counted within the draw (by text), the strongest source's rare shared 4-grams per 10,000
    words; mean over draws; then the separation rule."""
    from eval.known_answer import separation
    from metadata.dates import catalog_years, effective_year
    from ocr_fix.normalize import norm_path
    from reuse.exact import MISSED_OWN_COPIES, eligible_any_year, targets

    cfg = load_config()
    b = cfg["borrowing"]
    missed = {k: set(v) for k, v in MISSED_OWN_COPIES.items()}
    KNOWN.mkdir(parents=True, exist_ok=True)
    srch = json.loads(Path("data/reuse/exact/searches.json").read_text())
    tg = targets(cfg)
    hits_path = KNOWN / "hits.parquet"
    if not hits_path.exists():
        gram_dir = KNOWN / "target_grams"
        gram_dir.mkdir(exist_ok=True)
        for key, t in tg.items():
            g = gram_ids(tokens(t["text"]), b["ngram"])
            (gram_dir / f"{key}.txt").write_text("\n".join(map(str, sorted(g))))
        keys_of: dict[str, set[str]] = defaultdict(set)
        for name, ids in srch["searches"].items():
            if ":draw" in name:
                for w in ids:
                    keys_of[w].add(name.split(":")[0])
        by_id = {r["work_id"]: r for r in eligible_any_year(cfg)}
        jobs = [(w, str(norm_path(by_id[w])), sorted(k), str(gram_dir))
                for w, k in keys_of.items() if w in by_id]  # fmt: skip
        print(f"{len(jobs):,} volumes to scan", flush=True)
        recs, start = [], time.time()
        with ProcessPoolExecutor(workers) as pool:
            for i, (wid, words, h) in enumerate(pool.map(_known_one, jobs, chunksize=32), 1):
                recs += [{"work_id": wid, "target": k, "words": words, "hits": v}
                         for k, v in h.items()]  # fmt: skip
                if i % 10000 == 0:
                    print(f"  {i:,}/{len(jobs):,}  {i / (time.time() - start):.0f}/s", flush=True)
        schema = pa.schema([("work_id", pa.string()), ("target", pa.string()),
                            ("words", pa.int64()), ("hits", pa.list_(pa.int64()))])  # fmt: skip
        pq.write_table(pa.Table.from_pylist(recs, schema=schema), hits_path)
    by_key: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in pq.read_table(hits_path).to_pylist():
        by_key[r["target"]][r["work_id"]] = r
    years = catalog_years()
    texts = {}
    for key in tg:
        draws = []
        for i in range(cfg["reuse"]["matched_draws"]):
            top = srch["targets"][key]["year"] - 1
            ids = srch["searches"].get(f"{key}:draw{i}", [])
            recs = [by_key[key][w] for w in ids if w in by_key[key] and by_key[key][w]["words"]
                    and (effective_year(w, years.get(w)) or top + 1) <= top]  # fmt: skip
            row = {"volumes": len(recs)}
            for name, drop in (("", set()), ("_own_copies_out", missed.get(key, set()))):
                kept = [r for r in recs if r["work_id"] not in drop]
                df = doc_freq(kept, b["df_by_text"])
                rare = {g for g, c in df.items() if c <= b["max_df"]}
                d = densities(kept, rare, b["per_words"])
                best = max(d, key=d.get) if d else None
                row |= {f"rare_grams{name}": len(rare), f"best{name}": best,
                        f"best_words{name}": next((r["words"] for r in kept
                                                   if r["work_id"] == best), None),
                        f"score{name}": d.get(best, 0.0)}  # fmt: skip
            draws.append(row)
        if draws and any(x["volumes"] for x in draws):
            texts[key] = {"draws": draws, "score": sum(x["score"] for x in draws) / len(draws),
                          "score_own_copies_out": sum(x["score_own_copies_out"] for x in draws)
                          / len(draws)}  # fmt: skip
    res = separation({k: v["score"] for k, v in texts.items()}, cfg)
    res_out = separation({k: v["score_own_copies_out"] for k, v in texts.items()}, cfg)
    out = {**stamp(), "score": "strongest source's rare shared 4-grams per 10,000 words in each "
           "matched draw, document frequency within the draw by text; mean over draws",
           "texts": texts, "separation": res,
           "separation_own_copies_out": res_out}  # fmt: skip
    (KNOWN / "known_answer.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in texts.items():
        print(f"  {k}: {v['score']:.3f}")
    rowley = res.get("rowley_at_genuine_median", {}).get("separates")
    print(f"U = {res['U']}/{res['of']}, p = {res['p']:.3f}, separates: {res['separates']}; "
          f"Rowley at the genuine median: {rowley}")  # fmt: skip
    print(f"own copies out: U = {res_out['U']}/{res_out['of']}, p = {res_out['p']:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
