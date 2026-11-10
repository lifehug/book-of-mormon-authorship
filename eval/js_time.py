"""Joseph Smith's prose over time against the Book of Mormon's style (BOM-73, Amendment 46).

Did Joseph Smith's ordinary prose, and that of readers who followed the book, move toward its style
after 1830 while religious writers who had not read it did not? Plan and attribution rule:
``docs/js-over-time-plan.md``; values: ``js_time`` in the config. Groups:

- ``joseph_smith``: the Joseph Smith Papers documents of 1833-44 in ``data/js_time/sources.json``.
  Handwritten and mixed documents give only the words the edition marks in his hand
  (``ingest.jsp.transcript_words``), line ``js_hand``; dictated documents give all their words,
  line ``js_dictated``; ``js_pooled`` is both.
- ``readers``: Cowdery, Pratt, Phelps and Rigdon, from the cleaned candidate items dated in
  ``data/js_time/exposed_items.json`` (masked and quotation-checked as in Amendment 43).
- ``unexposed`` and ``campbell``: the comparison texts of ``data/js_time/controls.json``
  (``ingest.js_time``); Campbell is reported beside the others and never enters the rule.

Steps: ``assemble`` writes Joseph Smith's words per document (private) and the units table;
``python -m kjv_mask.run js_time`` masks his documents and the comparison texts; ``measure`` drops
Book of Mormon quotations (``eval.bom_quotes``), drops comparison blocks that mention Mormonism,
cuts each writer-period into blocks, and measures each block's distance to the masked Book of
Mormon narrative by Burrows' and Cosine Delta and by the 297M and 590M style encoders, each
separately. Slopes of distance on period are compared with the unexposed group's by permuting
period labels within writer.

Writes ``data/js_time/units.csv`` (names, years, counts) and ``data/js_time/results.json``
(numbers only); Joseph Smith's texts go to ``data/private/js_time/units/`` (copyrighted
transcripts).

Usage::

    python -m eval.js_time assemble
    python -m eval.js_time measure [--encoders base,mid]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

SOURCES = Path("data/js_time/sources.json")
CONTROLS = Path("data/js_time/controls.json")
EXPOSED = Path("data/js_time/exposed_items.json")
JS_DIR = Path("data/private/js_time/units")
CTRL_DIR = Path("data/corpus/js_time/text")
UNITS = Path("data/js_time/units.csv")
RESULTS = Path("data/js_time/results.json")
CHUNKS = Path("data/bom/segments/chunks.jsonl")
CLEAN = (Path("data/candidates/clean"), Path("data/private/candidates/clean"))


def period_of(year: int, bins: list[list[int]]) -> int | None:
    for i, (a, b) in enumerate(bins):
        if a <= year <= b:
            return i
    return None


def assemble() -> int:
    from ingest import jsp

    cfg = load_config()["js_time"]
    rows = []
    JS_DIR.mkdir(parents=True, exist_ok=True)
    for e in json.loads(SOURCES.read_text()):
        recs = [json.loads(ln) for ln in Path(f"data/private/candidates/{e['id']}.jsonl")
                .read_text().splitlines()]  # fmt: skip
        html = "\n".join(r["clear_html"] for r in sorted(recs, key=lambda r: r["page"]))
        toks = jsp.transcript_words(html)
        if e["provenance"] == "dictated":
            line, words = "js_dictated", [w for w, _ in toks]
        else:  # handwritten or mixed: his own hand only
            line, words = "js_hand", [w for w, mine in toks if mine]
        (JS_DIR / f"{e['id']}.txt").write_text(" ".join(words), encoding="utf-8")
        y = int(e["date_written"][:4])
        rows.append({"unit": f"js:{e['id']}", "group": "joseph_smith", "writer": "Joseph Smith",
                     "line": line, "year": y, "period": period_of(y, cfg["bins"]),
                     "raw_words": len(words), "status": "ok"})  # fmt: skip
    for e in json.loads(CONTROLS.read_text()):
        p = CTRL_DIR / f"{e['id']}.txt"
        ok = p.exists()
        n = len(p.read_text(encoding="utf-8", errors="replace").split()) if ok else 0
        rows.append({"unit": f"ctl:{e['id']}", "group": e["group"], "writer": e["writer"],
                     "line": e["writer"], "year": e["year"],
                     "period": period_of(e["year"], cfg["bins"]), "raw_words": n,
                     "status": "ok" if ok else "not fetched"})  # fmt: skip
    for e in json.loads(EXPOSED.read_text()):
        if e["kind"] == "excluded" or e["year"] is None:
            continue
        stem = e["source"] if e["kind"] == "book" else f"{e['source']}__{e['start']}-{e['end']}"
        p = next((d / f"{stem}.txt" for d in CLEAN if (d / f"{stem}.txt").exists()), None)
        n = len(p.read_text(encoding="utf-8").split()) if p else 0
        rows.append({"unit": f"cand:{stem}", "group": "readers", "writer": e["writer"],
                     "line": e["writer"], "year": e["year"],
                     "period": period_of(e["year"], cfg["bins"]), "raw_words": n,
                     "status": "ok" if p else "no cleaned text"})  # fmt: skip
    with UNITS.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    by = defaultdict(int)
    for r in rows:
        if r["status"] == "ok":
            by[(r["group"], r["line"], r["period"])] += r["raw_words"]
    for k in sorted(by, key=str):
        print(k, by[k])
    print(f"-> {UNITS}: {len(rows)} units")
    return 0


def _unit_text(unit: str) -> str:
    kind, name = unit.split(":", 1)
    if kind == "js":
        return (JS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    if kind == "ctl":
        from ocr_fix.normalize import artifacts

        raw = (CTRL_DIR / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
        return artifacts(raw)[0]
    for d in CLEAN:
        if (d / f"{name}.txt").exists():
            return (d / f"{name}.txt").read_text(encoding="utf-8")
    raise FileNotFoundError(unit)


def unit_words(unit: str, spans: dict, cand_quotes: dict, q: dict) -> list[str]:
    """Masked original words, Book of Mormon quotations dropped (Amendment 43's rule)."""
    from alm.candidates import drop_quotations
    from eval.bom_quotes import passages
    from segment.build import original_words

    text = _unit_text(unit)
    ws = original_words(text, spans.get(unit, []))
    quotes = cand_quotes.get(unit) if unit.startswith("cand:") else passages(text)
    return drop_quotations(ws, quotes, q["ngram"]) if quotes else ws


def _slope(d: np.ndarray, per: np.ndarray, writer: np.ndarray) -> float:
    """Within-writer OLS slope of distance on period (each writer's means removed)."""
    dd, pp = d.copy(), per.astype(float).copy()
    for w in np.unique(writer):
        m = writer == w
        dd[m] -= dd[m].mean()
        pp[m] -= pp[m].mean()
    den = (pp * pp).sum()
    return float((pp * dd).sum() / den) if den else float("nan")


def measure(encoders: list[str]) -> int:
    from classic.delta import burrows_delta, cosine_delta, fit_zscore, zscore

    full = load_config()
    cfg, q = full["js_time"], full["candidates"]["bom_quotation"]
    units = [r for r in csv.DictReader(UNITS.open()) if r["status"] == "ok" and r["period"] != ""]
    spans: dict = {}
    for f in (
        Path("data/kjv_mask/js_time/spans.jsonl"),
        Path("data/kjv_mask/candidates/spans.jsonl"),
    ):  # noqa: E501
        for ln in f.read_text().splitlines():
            r = json.loads(ln)
            spans[r["id"]] = r["spans"]
    cand_quotes = json.loads(Path("data/corpus/candidates/bom_quotations.json").read_text())
    missing = [u["unit"] for u in units
               if not u["unit"].startswith("cand:") and u["unit"] not in spans]  # fmt: skip
    if missing:
        raise SystemExit(f"{len(missing)} units not masked: run python -m kjv_mask.run js_time")

    # pool each line's words per period (units in year order), then cut blocks
    pooled: dict[tuple, list[str]] = defaultdict(list)
    meta: dict[tuple, tuple] = {}
    for u in sorted(units, key=lambda r: (r["year"], r["unit"])):
        ws = unit_words(u["unit"], spans, cand_quotes, q)
        keys = [(u["group"], u["writer"], u["line"], int(u["period"]))]
        if u["group"] == "joseph_smith":
            keys.append(("joseph_smith", "Joseph Smith", "js_pooled", int(u["period"])))
        for k in keys:
            pooled[k] += ws
            meta[k] = (k[0], k[1], k[2])
    n, floor = cfg["block_words"], cfg["floor_words"]
    blocks, cells = [], {}
    for k, ws in sorted(pooled.items(), key=lambda kv: str(kv[0])):
        cut = [ws[i : i + n] for i in range(0, len(ws) - n + 1, n)]
        dropped = 0
        if k[0] in ("unexposed", "campbell"):
            keep = [b for b in cut if not any(cfg["exclude_topic"] in w.lower() for w in b)]
            dropped, cut = len(cut) - len(keep), keep
        kept_words = len(cut) * n
        cells[k] = {"words": len(ws), "blocks": len(cut), "topic_dropped": dropped,
                    "empty": kept_words < floor}  # fmt: skip
        if kept_words >= floor:
            blocks += [(k, b) for b in cut]
    print(f"{len(blocks)} blocks in {sum(not c['empty'] for c in cells.values())} writer-periods")

    bom = [json.loads(ln) for ln in CHUNKS.read_text().splitlines()]
    bom = [c["text"].split() for c in bom if c["scheme"] == "narrator" and c["chunk_words"] == n
           and not c["partial"]]  # fmt: skip
    dist: dict[str, np.ndarray] = {}
    # Delta: MFW and z-scores over all comparison blocks; the Book of Mormon as their centroid
    from collections import Counter

    lower = [[w.lower() for w in b] for _, b in blocks]
    fit = [b for (k, _), b in zip(blocks, lower, strict=True) if k[2] != "js_pooled"]  # no repeats
    tot = Counter(w for b in fit for w in b)
    vocab = [w for w, _ in tot.most_common(cfg["mfw"])]
    vi = {w: i for i, w in enumerate(vocab)}

    def rel(ws: list[str]) -> np.ndarray:
        v = np.zeros(len(vocab))
        for w in ws:
            j = vi.get(w.lower())
            if j is not None:
                v[j] += 1
        return v / max(1, len(ws))

    X = np.stack([rel(b) for b in lower])
    mean, std = fit_zscore(np.stack([rel(b) for b in fit]))
    Z = zscore(X, mean, std)
    ref = zscore(np.stack([rel(b) for b in bom]), mean, std).mean(axis=0)
    dist["burrows_delta"] = np.array([burrows_delta(z, ref) for z in Z])
    dist["cosine_delta"] = np.array([cosine_delta(z, ref) for z in Z])
    for size in encoders:
        from style_embed.benchmark import embedder
        from style_embed.names import run_dir

        embed = embedder(run_dir(size) / "style.pt", full, size)
        r = np.stack([embed(b) for b in bom]).mean(axis=0)
        r /= np.linalg.norm(r)
        V = np.stack([embed(b) for _, b in blocks])
        dist[f"style_{size}"] = 1.0 - V @ r
        print(f"style {size}: {len(V)} blocks", flush=True)

    keys = [k for k, _ in blocks]
    group = np.array([k[0] for k in keys])
    line = np.array([k[2] for k in keys])
    per = np.array([k[3] for k in keys])
    writer = np.array([f"{k[1]}|{k[2]}" for k in keys])
    rng = np.random.default_rng(derive_seed(cfg["seed"], full))
    out: dict = {}
    for m, d in dist.items():
        cell_stats = {}
        for k in sorted(set(keys), key=str):
            sel = np.array([kk == k for kk in keys])
            x = d[sel]
            boots = [rng.choice(x, len(x)).mean() for _ in range(cfg["bootstrap"])]
            cell_stats["|".join(map(str, k))] = {
                "blocks": int(sel.sum()), "mean": float(x.mean()),
                "ci95": [float(np.percentile(boots, 2.5)),
                         float(np.percentile(boots, 97.5))]}  # fmt: skip
        tests = {}
        unex = group == "unexposed"
        comparisons = {"js_hand": line == "js_hand", "js_dictated": line == "js_dictated",
                       "js_pooled": line == "js_pooled", "readers": group == "readers",
                       "campbell": group == "campbell"}  # fmt: skip
        s_unex = _slope(d[unex], per[unex], writer[unex])
        for name, sel in comparisons.items():
            s = _slope(d[sel], per[sel], writer[sel])
            res = {"slope": s, "slope_unexposed": s_unex, "difference": s - s_unex}
            if name != "campbell" and not np.isnan(s):
                both = sel | unex
                dd, ww, pp, gg = d[both], writer[both], per[both].copy(), sel[both]
                obs, hits = s - s_unex, 0
                prng = random.Random(derive_seed(f"{cfg['seed']}:{m}:{name}", full))
                for _ in range(cfg["permutations"]):
                    for w in np.unique(ww):
                        idx = np.where(ww == w)[0]
                        pp[idx] = np.array(prng.sample(list(pp[idx]), len(idx)))
                    diff = _slope(dd[gg], pp[gg], ww[gg]) - _slope(dd[~gg], pp[~gg], ww[~gg])
                    hits += abs(diff) >= abs(obs)
                res["p_two_sided"] = (hits + 1) / (cfg["permutations"] + 1)
            tests[name] = res
        out[m] = {"cells": cell_stats, "tests": tests}
        print(m, {k: (round(v["difference"], 4), round(v.get("p_two_sided", float("nan")), 4))
                  for k, v in tests.items()})  # fmt: skip
    doc = {**stamp(), "bins": cfg["bins"], "vocab_size": len(vocab), "bom_chunks": len(bom),
           "writer_periods": {"|".join(map(str, k)): v for k, v in cells.items()},
           "measures": out}  # fmt: skip
    RESULTS.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"-> {RESULTS}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["assemble", "measure"])
    ap.add_argument("--encoders", help="style encoders, comma-separated (default: the config's)")
    a = ap.parse_args(argv)
    if a.cmd == "assemble":
        return assemble()
    enc = load_config()["js_time"]["encoders"] if a.encoders is None else a.encoders.split(",")
    return measure([e for e in enc if e])


if __name__ == "__main__":
    sys.exit(main())
