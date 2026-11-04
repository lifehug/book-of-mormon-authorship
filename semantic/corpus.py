"""Whole-corpus semantic search (BOM-25; plan ``docs/semantic-plan.md``, Amendment 14).

Every target's query passages are searched against the passage index (``semantic.index``) in one
pass: exact inner product, the ``semantic.keep`` nearest passages per query and gallery, scores
recomputed in full precision. The galleries are the Book of Mormon's window (1780-1830, its
sealed copies out; volumes BOM-64 moved past 1830 kept and flagged) and each target's three
matched draws of BOM-23 (``data/reuse/exact/searches.json``), re-read through the corrected
dates. A retrieved passage is a parallel when it beats the query's own bar, the best of
``semantic.null_passages`` random passages from the target's window.

Targets: the Book of Mormon (1830 text, King James share labelled per passage), each
known-answer text processed the same way (Amendment 9's score: the strongest source in each
draw, mean over draws), and the three retellings with their King James spans masked, searched
against their draws with the King James Bible added as one more volume (the positive controls).

Usage::

    python -m semantic.corpus queries    # query passages, vectors and bars
    python -m semantic.corpus scan       # one pass over the index; resumable
    python -m semantic.corpus score      # -> data/semantic/corpus_bom.json, known_answer.json
"""

from __future__ import annotations

import argparse
import bisect
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/semantic")
WORK = Path("data/corpus/semantic/search")  # vectors and top lists: derived, local only
SEARCHES = Path("data/reuse/exact/searches.json")
KNOWN = Path("data/known_answer/set.jsonl")
SPANS = Path("data/kjv_mask/known_answer/spans.jsonl")
RETELLINGS = ("josephus", "twelve_patriarchs", "jasher")
KJV_ID = "kjv"
CELLS = 200_000_000  # query x gallery-row similarities per block (GPU memory)


def _cat(ids: set[str]) -> dict[str, dict]:
    cols = ["work_id", "source", "text_path", "title", "year", "author_norm"]
    t = pq.read_table("data/catalog/catalog.parquet", columns=cols)
    return {r["work_id"]: r for r in t.to_pylist() if r["work_id"] in ids}


def labelled_passages(ids: list[str], cfg: dict) -> list[dict]:
    """The volumes' full normalised text cut as the index cuts it, each passage with the share of
    its words inside the volume's King James spans (BOM-16 masks): the Book of Mormon's
    treatment, applied to a known-answer text."""
    from ocr_fix.normalize import norm_path
    from semantic.index import _WORD, spans

    s = cfg["semantic"]
    want, masks = set(ids), {}
    for ln in SPANS.read_text().splitlines():
        if any(w in ln[:200] for w in want):
            r = json.loads(ln)
            if r["id"] in want:
                masks[r["id"]] = r["spans"]
    cat = _cat(want)
    out = []
    for w in ids:
        text = norm_path(cat[w]).read_text(encoding="utf-8", errors="replace")
        merged: list[list[int]] = []
        for sp in sorted(masks.get(w, []), key=lambda x: x["start"]):
            if merged and sp["start"] <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], sp["end"])
            else:
                merged.append([sp["start"], sp["end"]])
        starts = [m[0] for m in merged]

        def inside(pos: int, starts: list[int] = starts, merged: list = merged) -> bool:
            i = bisect.bisect_right(starts, pos) - 1
            return i >= 0 and pos < merged[i][1]

        for a, b, n in spans(text, s["passage_words"], s["min_passage_words"]):
            ws = [m.start() + a for m in _WORD.finditer(text[a:b])]
            out.append({"text": " ".join(text[a:b].split()), "words": n,
                        "kjv_share": sum(inside(p) for p in ws) / len(ws)})  # fmt: skip
    return out


def targets(cfg: dict) -> dict[str, dict]:
    """key -> {"year", "null": (lo, hi, exclude), "galleries", "null_key"}; queries are built by
    ``queries``. Known-answer windows are the draws' (``reuse.window_years`` before the text)."""
    from metadata.sealed import sealed_ids
    from reuse.exact import eligible_any_year, own_copies

    lo, hi = cfg["corpus"]["date_range"]
    srch = json.loads(SEARCHES.read_text())
    rows = eligible_any_year(cfg)
    draws = [f"draw{i}" for i in range(cfg["reuse"]["matched_draws"])]
    out = {"bom": {"year": hi, "null": (lo, hi, sealed_ids()), "null_key": "bom",
                   "galleries": ["bom:window", *[f"bom:{d}" for d in draws]]}}  # fmt: skip
    for ln in KNOWN.read_text().splitlines():
        r = json.loads(ln)
        key, ids = r["key"], [v["work_id"] for v in r["volumes"]]
        year = srch["targets"][key]["year"]
        own = own_copies(key, {"ids": ids}, rows)
        null = (year - cfg["reuse"]["window_years"], year - 1, own)
        gal = [f"{key}:{d}" for d in draws]
        out[key] = {"year": year, "ids": ids, "null": null, "null_key": key, "galleries": gal}
        if key in RETELLINGS:
            out[f"ctl_{key}"] = {"year": year, "ids": ids, "null": null, "null_key": key,
                                 "galleries": gal, "masked": True}  # fmt: skip
    return out


def galleries(cfg: dict) -> tuple[dict[str, set[str]], set[str]]:
    """Gallery name -> volume ids, and the volumes BOM-64 moved out of the Book of Mormon's window
    (kept in it, flagged)."""
    from metadata.dates import catalog_years
    from metadata.sealed import sealed_ids
    from reuse.exact import eligible_any_year

    lo, hi = cfg["corpus"]["date_range"]
    cy = catalog_years()
    rows = eligible_any_year(cfg)
    eff = {r["work_id"]: r["year"] for r in rows}
    sealed = sealed_ids()
    moved = {w for w, y in eff.items() if y > hi and lo <= (cy.get(w) or 0) <= hi}
    out = {"bom:window": {w for w, y in eff.items() if (lo <= y <= hi or w in moved)
                          and w not in sealed}}  # fmt: skip
    srch = json.loads(SEARCHES.read_text())
    for name, ids in srch["searches"].items():
        if ":draw" in name:
            top = srch["targets"][name.split(":")[0]]["year"] - 1
            out[name] = {w for w in ids if w in eff and eff[w] <= top}
    return out, moved


def _null_passages(lo: int, hi: int, exclude: set[str], seed_key: str, cfg: dict) -> list[str]:
    from semantic.search import null_passages

    return null_passages(seed_key, lo, hi, exclude, cfg)


def queries() -> int:
    from reuse.exact import masked_text
    from semantic.index import _model
    from semantic.search import _embed, bom_queries, text_passages

    cfg = load_config()
    WORK.mkdir(parents=True, exist_ok=True)
    model = _model(cfg)
    for key, t in targets(cfg).items():
        path = WORK / f"q_{key}.npz"
        if path.exists():
            continue
        if key == "bom":
            qs = bom_queries(cfg["semantic"]["passage_words"])
        elif t.get("masked"):
            qs = [{"text": p, "words": len(p.split()), "kjv_share": 0.0}
                  for p in text_passages(masked_text(t["ids"]), cfg)]  # fmt: skip
        else:
            qs = labelled_passages(t["ids"], cfg)
        npath = WORK / f"null_{t['null_key']}.npy"
        if not npath.exists():
            lo, hi, exclude = t["null"]
            # the Book of Mormon's null is the one ``semantic.search named`` drew (same key)
            nv = _embed(model, _null_passages(lo, hi, exclude, t["null_key"], cfg), cfg)
            np.save(npath, nv.astype(np.float16))
        nv = np.load(npath).astype(np.float32)
        qv = _embed(model, [q["text"] for q in qs], cfg).astype(np.float16)
        bar = (qv.astype(np.float32) @ nv.T).max(axis=1)
        np.savez(path, q=qv, bar=bar, words=np.array([q["words"] for q in qs]),
                 kjv_share=np.array([q["kjv_share"] for q in qs]))  # fmt: skip
        print(f"{key}: {len(qs)} query passages, null {len(nv)}", flush=True)
    return 0


def scan() -> int:
    """One pass over every finished shard: per (target, gallery) the ``keep`` nearest passages
    of each query, found in half precision and rescored in full precision. Checkpointed."""
    import torch

    from semantic.index import _done

    cfg = load_config()
    keep = cfg["semantic"]["keep"]
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    gal, _ = galleries(cfg)
    tg = targets(cfg)
    names = sorted({g for t in tg.values() for g in t["galleries"]})
    assert len(names) <= 63, "gallery bitmask is 64 bits"
    bit = {g: 1 << i for i, g in enumerate(names)}
    vol_bits: dict[str, int] = defaultdict(int)
    for g in names:
        for w in gal[g]:
            vol_bits[w] |= bit[g]
    jobs = [(k, g) for k, t in tg.items() for g in t["galleries"]]
    qv = {k: torch.from_numpy(np.load(WORK / f"q_{k}.npz")["q"]).to(dev) for k in tg}
    shards = [d.with_suffix("") for d in _done()]
    state_path, done_path = WORK / "scan_state.npz", WORK / "scan_done.json"
    top: dict[tuple[str, str], list] = {}
    done: list[str] = []
    if done_path.exists():
        info = json.loads(done_path.read_text())
        done, shards = info["done"], [Path(p) for p in info["shards"]]
        st = np.load(state_path)
        for k, g in jobs:
            top[(k, g)] = [torch.from_numpy(st[f"{k}|{g}|s"]).to(dev),
                           torch.from_numpy(st[f"{k}|{g}|i"]).to(dev)]  # fmt: skip
    else:
        for k, g in jobs:
            n = qv[k].shape[0]
            top[(k, g)] = [torch.full((n, keep), -2.0, device=dev),
                           torch.full((n, keep), -1, dtype=torch.int64, device=dev)]  # fmt: skip
    print(f"{len(jobs)} searches over {len(shards)} shards ({len(done)} done) on {dev}", flush=True)

    def save() -> None:
        arrays = {}
        for (k, g), (s_, i_) in top.items():
            arrays[f"{k}|{g}|s"], arrays[f"{k}|{g}|i"] = s_.cpu().numpy(), i_.cpu().numpy()
        np.savez(WORK / "scan_state.tmp.npz", **arrays)
        (WORK / "scan_state.tmp.npz").rename(state_path)
        done_path.write_text(json.dumps({"shards": [str(p) for p in shards], "done": done}))

    start, last = time.time(), time.time()
    for si, base in enumerate(shards):
        if base.name in done:
            continue
        wids = pq.read_table(base.with_suffix(".parquet"), columns=["work_id"])["work_id"]
        enc = wids.dictionary_encode().combine_chunks()
        dict_bits = np.array([vol_bits.get(w, 0) for w in enc.dictionary.to_pylist()],
                             dtype=np.int64)  # fmt: skip
        row_bits = dict_bits[enc.indices.to_numpy()]
        vec = np.load(base.with_suffix(".npy"), mmap_mode="r")
        for g in names:
            rows = np.flatnonzero(row_bits & bit[g])
            if not len(rows):
                continue
            nq = max(qv[k].shape[0] for k, g2 in jobs if g2 == g)
            step = max(4096, CELLS // nq)  # similarity block of at most CELLS entries
            for c in range(0, len(rows), step):
                rc = rows[c : c + step]
                v = torch.from_numpy(np.ascontiguousarray(vec[rc])).to(dev)
                gid = torch.from_numpy((si << 32) | rc.astype(np.int64)).to(dev)
                for k, g2 in jobs:
                    if g2 != g:
                        continue
                    q = qv[k]
                    kk = min(keep, len(rc))
                    _, idx = torch.topk(q @ v.T, kk, dim=1)
                    exact = torch.einsum("qd,qkd->qk", q.float(), v[idx].float())
                    s_, i_ = top[(k, g)]
                    alls = torch.cat([s_, exact], dim=1)
                    alli = torch.cat([i_, gid[idx]], dim=1)
                    best, pos = torch.topk(alls, keep, dim=1)
                    top[(k, g)] = [best, torch.gather(alli, 1, pos)]
        done.append(base.name)
        if dev == "mps":
            torch.mps.empty_cache()
        if time.time() - last > 600:
            save()
            last = time.time()
        rate = (time.time() - start) / max(1, len(done))
        print(f"  {base.name}: {len(done)}/{len(shards)}, ~{rate:.0f} s/shard", flush=True)
    save()
    print("scan complete")
    return 0


def _decode(ids: np.ndarray, shards: list[Path]) -> dict[int, tuple]:
    """Global passage id -> (work_id, passage, char_begin, char_end)."""
    out: dict[int, tuple] = {}
    want: dict[int, set[int]] = defaultdict(set)
    for x in np.unique(ids[ids >= 0]):
        want[int(x) >> 32].add(int(x) & 0xFFFFFFFF)
    for si, rows in want.items():
        t = pq.read_table(shards[si].with_suffix(".parquet"),
                          columns=["work_id", "passage", "char_begin", "char_end"])  # fmt: skip
        r = sorted(rows)
        sub = t.take(r).to_pylist()
        for row, m in zip(r, sub, strict=True):
            out[(si << 32) | row] = (m["work_id"], m["passage"], m["char_begin"], m["char_end"])
    return out


def _source_scores(hit_vol: list[set[str]], scored: np.ndarray, scored_words: int) -> dict:
    counts: dict[str, int] = defaultdict(int)
    for i in np.flatnonzero(scored):
        for w in hit_vol[i]:
            counts[w] += 1
    return {w: 10000 * c / scored_words for w, c in counts.items()}


def _genre() -> dict[str, str]:
    g = {r["work_id"]: (r["genre"] or "uncertain").split(",")[0]
         for r in pq.read_table("data/catalog/genre.parquet").to_pylist()}  # fmt: skip
    return {w: ("uncertain" if x in ("PARSE_FAIL", "uncertain") else x) for w, x in g.items()}


def _volume_words() -> dict[str, int]:
    from semantic.index import _done

    path = WORK / "volume_words.json"
    if path.exists():
        return json.loads(path.read_text())
    out: dict[str, int] = defaultdict(int)
    for d in _done():
        t = pq.read_table(d.with_suffix(".parquet"), columns=["work_id", "words"])
        g = t.group_by("work_id").aggregate([("words", "sum")]).to_pylist()
        for r in g:  # a volume held twice (the split's overlap) counts once
            out[r["work_id"]] = max(out[r["work_id"]], int(r["words_sum"]))
    path.write_text(json.dumps(out))
    return out


def _kjv_passages(cfg: dict) -> tuple[list[str], list[str]]:
    """The King James Bible cut book by book as the index cuts a volume: (passages, books)."""
    from semantic.index import spans

    s = cfg["semantic"]
    books: dict[str, list[str]] = {}
    for ln in Path("data/kjv/kjv.jsonl").read_text().splitlines():
        r = json.loads(ln)
        books.setdefault(r["book"], []).append(r["text"])
    ps, bk = [], []
    for b, verses in books.items():
        text = " ".join(verses)
        for a, e, _ in spans(text, s["passage_words"], s["min_passage_words"]):
            ps.append(" ".join(text[a:e].split()))
            bk.append(b)
    return ps, bk


def score() -> int:
    from eval.known_answer import separation
    from reuse.exact import BIBLE, MISSED_OWN_COPIES
    from semantic.skeleton import RETELLINGS as BOOKS

    cfg = load_config()
    s = cfg["semantic"]
    info = json.loads((WORK / "scan_done.json").read_text())
    shards = [Path(p) for p in info["shards"]]
    assert len(info["done"]) == len(shards), "scan not finished"
    st = np.load(WORK / "scan_state.npz")
    tg = targets(cfg)
    gal, moved = galleries(cfg)
    allids = np.concatenate([st[k] for k in st.files if k.endswith("|i")])
    where = _decode(allids, shards)
    cat = _cat({w for w, *_ in where.values()} | set().union(*gal.values()))
    title = {w: (c["title"] or "") for w, c in cat.items()}
    bible = {w for w, t in title.items() if BIBLE.search(t)}

    def load_q(k: str) -> dict:
        z = np.load(WORK / f"q_{k}.npz")
        return {x: z[x] for x in z.files}

    def hits(k: str, g: str, extra: tuple | None = None) -> tuple[list[set[str]], list[list]]:
        """Per query: volumes holding a parallel, and the parallels (volume, passage, span,
        score). ``extra``: (scores, volume) of an added gallery merged into the top ``keep``."""
        q = load_q(k)
        sc, ix = st[f"{k}|{g}|s"], st[f"{k}|{g}|i"]
        vols, pars = [], []
        for i in range(len(sc)):
            cand, seen = [], set()
            for a, b in zip(sc[i], ix[i], strict=True):
                m = where.get(int(b)) if b >= 0 else None
                if m and m[:2] not in seen:  # a volume held in two shards counts once
                    seen.add(m[:2])
                    cand.append((float(a), m))
            if extra is not None:
                es, ep = extra
                cand += [(float(es[i, j]), (KJV_ID, int(j), None, None)) for j in
                         np.argsort(-es[i])[: s["keep"]]]  # fmt: skip
                cand = sorted(cand, key=lambda x: -x[0])[: s["keep"]]
            ok = [(a, m) for a, m in cand if a > q["bar"][i]]
            vols.append({m[0] for _, m in ok})
            pars.append(ok)
        return vols, pars

    def boot_ci(hit_vol: list[set[str]], scored: np.ndarray, words: np.ndarray,
                ids: list[str], seed: str) -> dict[str, list[float]]:  # fmt: skip
        widx = np.flatnonzero(scored)
        col = {w: j for j, w in enumerate(ids)}
        h = np.zeros((len(widx), len(ids)), dtype=np.float32)
        for r, i in enumerate(widx):
            for w in hit_vol[i]:
                if w in col:
                    h[r, col[w]] = 1
        rng = np.random.default_rng(derive_seed(seed, cfg))
        b = rng.integers(0, len(widx), (s["bootstrap"], len(widx)))
        mult = np.zeros((s["bootstrap"], len(widx)), dtype=np.float32)
        np.add.at(mult, (np.arange(s["bootstrap"])[:, None], b), 1)
        bw = mult @ words[widx].astype(np.float32)
        out: dict[str, list[float]] = {}
        for c in range(0, len(ids), 2000):  # sources in chunks: 10,000 x 2,000 at a time
            bs = 10000 * (mult @ h[:, c : c + 2000]) / bw[:, None]
            lo_hi = np.percentile(bs, [2.5, 97.5], axis=0)
            out |= {w: [float(lo_hi[0, j]), float(lo_hi[1, j])]
                    for j, w in enumerate(ids[c : c + 2000])}  # fmt: skip
        return out

    # --- the Book of Mormon against its window
    q = load_q("bom")
    scored = q["kjv_share"] <= s["max_query_kjv_share"]
    sw = int(q["words"][scored].sum())
    hv, pars = hits("bom", "bom:window")
    src = _source_scores(hv, scored, sw)
    genre, vwords = _genre(), _volume_words()
    pool: dict[str, list[str]] = defaultdict(list)
    for w in sorted(gal["bom:window"] - bible):
        if w in vwords:
            pool[genre.get(w, "uncertain")].append(w)
    ranked = sorted((w for w in src if w not in bible), key=lambda w: -src[w])
    ci = boot_ci(hv, scored, q["words"], ranked, s["bootstrap_seed"])
    rows = []
    for rank, w in enumerate(ranked, 1):
        g, n = genre.get(w, "uncertain"), vwords.get(w, 0)
        f = s["null_length_factor"]
        cands = [x for x in pool[g] if x != w and n / f <= vwords[x] <= n * f]
        rng = random.Random(derive_seed(f"{s['null_seed']}:bom:{w}", cfg))
        null = np.array([src.get(x, 0.0) for x in
                         rng.sample(cands, min(s["null_volumes"], len(cands)))])  # fmt: skip
        p99 = float(np.percentile(null, 99)) if len(null) else None
        rows.append({"rank": rank, "work_id": w, "title": title.get(w, "")[:100],
                     "year": (cat.get(w) or {}).get("year"), "moved_past_1830": w in moved,
                     "genre": g, "words": n, "score": src[w], "score_ci95": ci[w],
                     "parallels": int(sum(w in hv[i] for i in np.flatnonzero(scored))),
                     "null_volumes": len(null), "null_p99": p99,
                     "percentile": float(100 * (null < src[w]).mean()) if len(null) else None,
                     "stands_out": bool(p99 is not None and ci[w][0] > p99)})  # fmt: skip
    listed_bible = sorted({w for w in src if w in bible}, key=lambda w: -src[w])
    import pyarrow as pa

    prow = [{"query": i, "work_id": m[0], "passage": m[1], "char_begin": m[2], "char_end": m[3],
             "score": a, "bar": float(q["bar"][i]), "query_kjv_share": float(q["kjv_share"][i])}
            for i, ok in enumerate(pars) for a, m in ok]  # fmt: skip
    pq.write_table(pa.Table.from_pylist(prow), OUT / "parallels_bom.parquet", compression="zstd")
    out = {"queries": len(scored), "scored_queries": int(scored.sum()), "scored_words": sw,
           "gallery_volumes": len(gal["bom:window"]), "moved_in_gallery": len(moved &
           gal["bom:window"]), "parallels": len(prow),
           "queries_with_a_parallel": int(sum(bool(v) for v in hv)),
           "sources": len(rows), "stand_out": sum(r["stands_out"] for r in rows),
           "bible_volumes_listed": [{"work_id": w, "title": title.get(w, "")[:100],
                                     "score": src[w]} for w in listed_bible[:50]],
           "top_search_sources": [r["work_id"] for r in rows
                                  [: cfg["skeleton"]["top_search_sources"]]],
           "ranking": rows}  # fmt: skip
    (OUT / "corpus_bom.json").write_text(json.dumps({**stamp(), **out}, indent=1) + "\n")
    print(f"bom: {out['parallels']} parallels, {out['sources']} sources, "
          f"{out['stand_out']} stand out")  # fmt: skip
    for r in rows[:20]:
        print(f"  {r['rank']:>3} {r['score']:7.2f} {r['score_ci95']} p99 {r['null_p99']} "
              f"{r['work_id']} {r['title'][:50]}")  # fmt: skip

    # --- Amendment 9: the strongest period source in each matched draw, mean over draws
    missed = {k: set(v) for k, v in MISSED_OWN_COPIES.items()}
    texts = {}
    for k, t in tg.items():
        if t.get("masked"):
            continue
        q = load_q(k)
        scored = q["kjv_share"] <= s["max_query_kjv_share"]
        sw = int(q["words"][scored].sum())
        draws = []
        for g in t["galleries"]:
            hv, _ = hits(k, g)
            sc = _source_scores(hv, scored, sw) if sw else {}
            row = {"volumes": len(gal[g])}
            for name, drop in (("", set()), ("_own_copies_out", missed.get(k, set()))):
                kept = {w: v for w, v in sc.items() if w not in drop}
                best = max(kept, key=kept.get) if kept else None
                row |= {f"best{name}": best, f"score{name}": kept.get(best, 0.0)}
            draws.append(row)
        texts[k] = {"draws": draws, "score": float(np.mean([d["score"] for d in draws])),
                    "score_own_copies_out": float(np.mean([d["score_own_copies_out"]
                                                           for d in draws])),
                    "scored_words": sw}  # fmt: skip
    res = separation({k: v["score"] for k, v in texts.items() if k != "bom"}, cfg)
    res_out = separation({k: v["score_own_copies_out"] for k, v in texts.items()
                          if k != "bom"}, cfg)  # fmt: skip

    # --- positive controls: the masked retellings with the King James Bible added to each draw
    from semantic.index import _model
    from semantic.search import _embed

    kp, kb = _kjv_passages(cfg)
    kv = _embed(_model(cfg), kp, cfg).astype(np.float16).astype(np.float32)
    controls = {}
    for k in RETELLINGS:
        q = load_q(f"ctl_{k}")
        es = q["q"].astype(np.float32) @ kv.T
        right = set(BOOKS[k][1])
        draws = []
        for g in tg[k]["galleries"]:
            hv, pr = hits(f"ctl_{k}", g, extra=(es, KJV_ID))
            sc = _source_scores(hv, np.ones(len(hv), bool), int(q["words"].sum()))
            best = max(sc, key=sc.get) if sc else None
            kept = {w: v for w, v in sc.items() if w not in missed.get(k, set())}
            best_out = max(kept, key=kept.get) if kept else None
            kjv_best = [max(ok, key=lambda x: x[0])[1] for ok in pr if ok]
            in_kjv = [m for m in kjv_best if m[0] == KJV_ID]
            draws.append(
                {
                    "best": best,
                    "kjv_strongest": best == KJV_ID,
                    "best_own_copies_out": best_out,
                    "kjv_strongest_own_copies_out": best_out == KJV_ID,
                    "kjv_score": sc.get(KJV_ID, 0.0),
                    "best_other": max((v for w, v in sc.items() if w != KJV_ID), default=0.0),
                    "queries_with_parallel": len(kjv_best),
                    "best_parallel_in_kjv": len(in_kjv),
                    "best_parallel_right_book": sum(kb[m[1]] in right for m in in_kjv),
                }
            )
        ok_out = all(d["kjv_strongest_own_copies_out"] for d in draws)
        controls[k] = {"draws": draws, "passes": (all(d["kjv_strongest"] for d in draws)
                                                  if k != "jasher" else None),
                       "passes_own_copies_out": ok_out if k != "jasher" else None}  # fmt: skip
    shown = bool(controls["josephus"]["passes"] and controls["twelve_patriarchs"]["passes"])
    shown_out = bool(controls["josephus"]["passes_own_copies_out"]
                     and controls["twelve_patriarchs"]["passes_own_copies_out"])  # fmt: skip
    ka = {**stamp(), "score": "strongest period source's semantic score s(T, v) in each matched "
          "draw (BOM-23's samples, corrected dates); mean over draws", "texts": texts,
          "separation": res, "separation_own_copies_out": res_out,
          "retelling_controls": controls, "shown_to_find_paraphrase": shown,
          "shown_to_find_paraphrase_own_copies_out": shown_out}  # fmt: skip
    (OUT / "corpus_known_answer.json").write_text(json.dumps(ka, indent=1) + "\n")
    for k, v in texts.items():
        print(f"  {k}: {v['score']:.2f}")
    print(f"U = {res['U']}/{res['of']}, p = {res['p']:.3f}, separates: {res['separates']}")
    for k, v in controls.items():
        print(f"  control {k}: passes {v['passes']} (own copies out "
              f"{v['passes_own_copies_out']}): "
              + "; ".join(f"{d['best']} kjv {d['kjv_score']:.1f} vs {d['best_other']:.1f}"
                          for d in v["draws"]))  # fmt: skip
    print(f"shown to find paraphrase: {shown} (own copies out {shown_out})")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("queries", "scan", "score"):
        sub.add_parser(c)
    a = ap.parse_args(argv)
    return {"queries": queries, "scan": scan, "score": score}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
