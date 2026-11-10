"""The linguistic dating classifier (BOM-29; pre-registration 5.3, 6.4, Amendments 2 and 17).

Two models, kept separate as 5.3 registers: **grammar** (``dating.features``, 61 rates per 1,000
tokens read from the printed text) and **lexical** (word frequencies from the registered
normalised text, with every word the grammar model reads left out). Each is a regularised
multinomial logistic regression over date bins (``dating.bins``); a segment's output is a
probability over the bins, from which come its median year and 90% interval. The grammar model
decides 6.4 and H3; the lexical model is reported beside it.

``sample``: every eligible dated volume (``reuse.exact.eligible_any_year``) from 1473 to 1830,
less Bibles, the Book of Mormon (4.2) and every text a later test scores
(``timelocked_lm.data.exclusions``: benchmark, candidates, known-answer texts) and the
pseudo-biblical controls. Authors (or, without one, volumes) go to a validation group by a
seeded hash, so no author is on both sides; each bin then takes a seeded draw of volumes from
each side and up to ``segments_per_volume`` 2,000-token segments from each volume, skipping its
first and last segment where it has four or more. Writes ids, positions and feature rates only.

``fit``: the lexical vocabulary (training segments only), then each model with its penalty chosen
by author-grouped cross-validation on the training segments.

``validate``: held-out segments (accuracy, interval coverage, 6.4's interval rule and Amendment
19's median rule, per segment and per volume), keyed against OCR text of the same decades, King
James imitation (the pseudo-biblical controls and the King James text itself), and Amendment 9's
known-answer separation. No Book of Mormon text is read here.

Usage::

    python -m dating.classifier sample [--workers 6]   # -> data/dating/segments.parquet
    python -m dating.classifier fit                     # -> data/dating/models.json
    python -m dating.classifier validate                # -> data/dating/validation.json
    python -m dating.classifier h3c                     # -> data/dating/h3c.json (after unblinding)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from dating import features as F
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

OUT = Path("data/dating")
LEX = Path("data/corpus/dating")  # lexical count matrices: vocabulary counts per segment
_WORD = re.compile(r"[a-z]+")


def _function_words() -> frozenset[str]:
    from classic.features import FUNCTION_WORDS

    return frozenset(F.fold(w) for w in FUNCTION_WORDS)


_FUNCTION = _function_words()


# ---- bins and the predicted-year distribution ------------------------------------------------


def bin_edges(d: dict) -> list[int]:
    """[first, merged_until, ..., last + 1]: the earliest years share one bin, then bins of
    ``bin_years``, the last running to ``last_year`` inclusive (1820-1830)."""
    inner = range(d["merged_until"], d["last_year"] - d["bin_years"] + 1, d["bin_years"])
    return [d["first_year"], *inner, d["last_year"] + 1]


def bin_of(year: int, edges: list[int]) -> int:
    return int(np.searchsorted(edges, year, side="right")) - 1


def quantile(prob: np.ndarray, edges: list[int], q: float) -> float:
    """The year below which ``q`` of the probability lies, uniform within each bin."""
    cum = np.concatenate([[0.0], np.cumsum(prob)])
    i = int(np.clip(np.searchsorted(cum, q, side="left") - 1, 0, len(prob) - 1))
    inside = (q - cum[i]) / prob[i] if prob[i] > 0 else 0.0
    return edges[i] + inside * (edges[i + 1] - edges[i])


def summary(prob: np.ndarray, edges: list[int], interval: float) -> tuple[float, float, float]:
    """(median year, interval low, interval high) of one segment's distribution."""
    tail = (1 - interval) / 2
    return quantile(prob, edges, 0.5), quantile(prob, edges, tail), quantile(prob, edges, 1 - tail)


# ---- reading text ------------------------------------------------------------------------------


def printed(row: dict) -> str:
    """The text as printed (keyed or BOM-14-cleaned OCR), before any spelling normalisation."""
    from ocr_fix.normalize import _input_path

    return _input_path(row).read_text(encoding="utf-8", errors="replace")


def normalised(row: dict) -> str:
    from ocr_fix.normalize import norm_path

    return norm_path(row).read_text(encoding="utf-8", errors="replace")


def lex_tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def chunks(n: int, size: int) -> list[int]:
    """The usable segment indexes of a text of ``n`` tokens: all whole segments, less the first
    and last (title pages, indexes) when there are four or more."""
    k = n // size
    return list(range(1, k - 1)) if k >= 4 else list(range(k))


def _pick(work_id: str, n: int, d: dict, salt: int) -> list[int]:
    avail = chunks(n, d["segment_words"])
    rng = random.Random(f"{salt}:{work_id}")
    return sorted(rng.sample(avail, min(len(avail), d["segments_per_volume"])))


def _segments_of(job: tuple[dict, dict, int]) -> list[dict]:
    """One volume's sampled segments: position and grammar rates."""
    row, d, salt = job
    try:
        toks = F.tokens(printed(row))
    except OSError:
        return []
    size, n = d["segment_words"], len(toks)
    out = []
    for c in _pick(row["work_id"], n, d, salt):
        seg = toks[c * size : (c + 1) * size]
        if is_prose(seg, d):
            out.append({"work_id": row["work_id"], "chunk": c, "chunks": n // size,
                        "rates": F.rates(seg).tolist()})  # fmt: skip
    return out


def is_prose(toks: list[str], d: dict) -> bool:
    """Running prose, not a table, index or OCR debris: enough function words."""
    return sum(t in _FUNCTION for t in toks) >= d["min_function_share"] * max(1, len(toks))


# ---- sample -------------------------------------------------------------------------------------


def _group(row: dict) -> str:
    from timelocked_lm.data import GENERIC_AUTHORS

    a = (row.get("author_norm") or "").strip()
    return f"author:{a}" if a and a not in GENERIC_AUTHORS else f"volume:{row['work_id']}"


def _held_out(group: str, salt: int, share: float) -> bool:
    h = hashlib.sha256(f"{salt}:{group}".encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64 < share


def controls_excluded() -> set[str]:
    """The pseudo-biblical controls (every list, BOM-18): the KJV-imitation test's texts."""
    out = set()
    for p in Path("data/controls").glob("pseudo_biblical*.jsonl"):
        out |= {json.loads(ln)["work_id"] for ln in p.read_text().splitlines() if ln.strip()}
    return out


def eligible(cfg: dict) -> tuple[list[dict], dict[str, str]]:
    """Dated rows in range, and the reason each left-out one is out."""
    from metadata.sealed import sealed_ids
    from reuse.exact import BIBLE, eligible_any_year
    from timelocked_lm.data import exclusions

    d = cfg["dating"]
    rows = [r for r in eligible_any_year(cfg) if d["first_year"] <= r["year"] <= d["last_year"]]
    reason = exclusions(rows)
    sealed, ctrl = sealed_ids(), controls_excluded()
    seal_hits = json.loads(Path("data/timelocked_lm/selection.json").read_text())["excluded_ids"]
    for r in rows:
        w = r["work_id"]
        if w in sealed or seal_hits.get(w, "").startswith("Book of Mormon"):
            reason[w] = "Book of Mormon"
        elif BIBLE.search(r["title"] or ""):
            reason.setdefault(w, "Bible")
        elif w in ctrl:
            reason.setdefault(w, "pseudo-biblical control")
    return [r for r in rows if r["work_id"] not in reason], reason


def sample(workers: int) -> int:
    cfg = load_config()
    d = cfg["dating"]
    edges = bin_edges(d)
    rows, reason = eligible(cfg)
    vsalt = derive_seed(d["validation_seed"], cfg)
    ssalt = derive_seed(d["sample_seed"], cfg)
    by_bin: dict[tuple[int, str], list[dict]] = {}
    for r in sorted(rows, key=lambda r: r["work_id"]):
        split = "validation" if _held_out(_group(r), vsalt, d["validation_share"]) else "train"
        by_bin.setdefault((bin_of(r["year"], edges), split), []).append({**r, "split": split})
    cap = {"train": d["train_volumes_per_bin"], "validation": d["validation_volumes_per_bin"]}
    out: list[dict] = []
    for (b, split), vols in sorted(by_bin.items()):
        random.Random(f"{ssalt}:{b}:{split}").shuffle(vols)
        got, i = 0, 0
        # draw in batches until the bin has its volumes (short or unreadable ones yield none)
        while got < cap[split] and i < len(vols):
            batch = vols[i : i + max(64, (cap[split] - got) * 2)]
            i += len(batch)
            with ProcessPoolExecutor(workers) as ex:
                res = list(ex.map(_segments_of, [(r, d, ssalt) for r in batch], chunksize=4))
            for r, segs in zip(batch, res, strict=True):
                if segs and got < cap[split]:
                    got += 1
                    out += [{**s, "source": r["source"], "year": r["year"], "bin": b,
                             "split": split, "group": _group(r)} for s in segs]  # fmt: skip
        print(f"bin {edges[b]}-{edges[b + 1] - 1} {split}: {got} volumes of {len(vols):,}",
              flush=True)  # fmt: skip
    table = pa.table({
        "work_id": [s["work_id"] for s in out],
        "source": [s["source"] for s in out],
        "year": pa.array([s["year"] for s in out], pa.int16()),
        "bin": pa.array([s["bin"] for s in out], pa.int8()),
        "split": [s["split"] for s in out],
        "group": [s["group"] for s in out],
        "chunk": pa.array([s["chunk"] for s in out], pa.int32()),
        "chunks": pa.array([s["chunks"] for s in out], pa.int32()),
        **{f"g_{n}": pa.array([s["rates"][j] for s in out], pa.float32())
           for j, n in enumerate(F.NAMES)},
    })  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, OUT / "segments.parquet")
    report = {**stamp(), "bins": edges, "eligible": len(rows),
              "excluded": dict(Counter(v.split(" (")[0] for v in reason.values())),
              "segments": dict(Counter(table.column("split").to_pylist())),
              "volumes": {s: len({o["work_id"] for o in out if o["split"] == s})
                          for s in ("train", "validation")}}  # fmt: skip
    (OUT / "sample.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))
    return 0


# ---- lexical features ---------------------------------------------------------------------------


def lexical_excluded() -> set[str]:
    """Words the lexical model may not use: every word the grammar model reads, the
    function-word list, and every standard spelling MorphAdorner put in place of a grammatical
    form (``maketh`` -> ``makes``), so the normalisation cannot leak grammar back in."""
    from classic.features import FUNCTION_WORDS

    out = set(FUNCTION_WORDS) | {w for w in F.GRAMMAR_WORDS}
    for ln in Path("data/normalization/applied_map.tsv").read_text().splitlines()[1:]:
        variant, standard = ln.split("\t")[:2]
        v = F.fold(variant.lower())
        if v in F.GRAMMAR_WORDS or v.endswith("eth") or v.endswith("est"):
            out |= set(lex_tokens(standard))
    return out


def _lex_counts(job: tuple[dict, list[tuple[int, int]], int]) -> list[Counter]:
    """Each segment's word counts from the normalised text, at the same relative position as the
    printed segment (normalisation can split or merge tokens, so positions are proportional)."""
    row, segs, size = job
    try:
        toks = lex_tokens(normalised(row))
    except OSError:
        return [Counter() for _ in segs]
    out = []
    for chunk, nchunks in segs:
        start = int(len(toks) * chunk / max(1, nchunks))
        out.append(Counter(toks[start : start + size]))
    return out


def lexical_matrix(seg: list[dict], vocab: list[str] | None, d: dict, workers: int,
                   excluded: set[str]):  # fmt: skip
    """Counts over ``vocab`` per segment (rows in ``seg`` order); with ``vocab`` None, choose it
    first from the training segments' document frequencies."""
    from scipy import sparse

    from metadata.pseudo_biblical import CATALOG

    by_vol: dict[str, list[int]] = {}
    for i, s in enumerate(seg):
        by_vol.setdefault(s["work_id"], []).append(i)
    cat = {r["work_id"]: r for r in pq.read_table(CATALOG).to_pylist() if r["work_id"] in by_vol}
    jobs = [(cat[w], [(seg[i]["chunk"], seg[i]["chunks"]) for i in idx], d["segment_words"])
            for w, idx in by_vol.items()]  # fmt: skip
    counters: list[Counter] = [Counter()] * len(seg)
    with ProcessPoolExecutor(workers) as ex:
        for idx, cs in zip(by_vol.values(), ex.map(_lex_counts, jobs, chunksize=4), strict=True):
            for i, c in zip(idx, cs, strict=True):
                counters[i] = Counter({k: v for k, v in c.items()
                                       if len(k) >= 3 and k not in excluded})  # fmt: skip
    if vocab is None:
        df = Counter()
        for s, c in zip(seg, counters, strict=True):
            if s["split"] == "train":
                df.update(c.keys())
        vocab = [w for w, _ in sorted(df.items(), key=lambda x: (-x[1], x[0]))]
        vocab = vocab[: d["lexical_vocabulary"]]
    col = {w: j for j, w in enumerate(vocab)}
    r, c, v = [], [], []
    for i, cnt in enumerate(counters):
        for w, n in cnt.items():
            if w in col:
                r.append(i), c.append(col[w]), v.append(n)
    m = sparse.csr_matrix((v, (r, c)), shape=(len(seg), len(vocab)), dtype=np.float32)
    return m, vocab


# ---- models -------------------------------------------------------------------------------------


def fit_one(x: np.ndarray, y: np.ndarray, groups: np.ndarray, d: dict, seed: int) -> dict:
    """Standardise, choose the L2 penalty by author-grouped CV (mean log loss), refit on all."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    def model(c: float):
        return make_pipeline(StandardScaler(), LogisticRegression(
            C=c, max_iter=d["max_iter"], random_state=seed))  # fmt: skip

    labels = np.unique(y)
    cv = []
    for c in d["penalty_grid"]:
        losses = []
        for tr, te in GroupKFold(d["cv_folds"]).split(x, y, groups):
            m = model(c).fit(x[tr], y[tr])
            p = np.full((len(te), len(labels)), 1e-12)
            p[:, np.searchsorted(labels, m.classes_)] = m.predict_proba(x[te])
            losses.append(-np.mean(np.log(p[np.arange(len(te)), np.searchsorted(labels, y[te])])))
        cv.append({"C": c, "log_loss": float(np.mean(losses))})
        print(f"  C={c}: cv log loss {cv[-1]['log_loss']:.4f}", flush=True)
    best = min(cv, key=lambda r: r["log_loss"])["C"]
    m = model(best).fit(x, y)
    return {"model": m, "C": best, "cv": cv}


def _segments() -> list[dict]:
    return pq.read_table(OUT / "segments.parquet").to_pylist()


def grammar_x(seg: list[dict]) -> np.ndarray:
    return np.log1p(np.array([[s[f"g_{n}"] for n in F.NAMES] for s in seg], dtype=np.float64))


def lexical_x(m, size: int) -> np.ndarray:
    return np.log1p(m.toarray() * (1000.0 / size))


def fit(workers: int) -> int:
    import joblib

    cfg = load_config()
    d = cfg["dating"]
    seg = _segments()
    tr = [s for s in seg if s["split"] == "train"]
    y = np.array([s["bin"] for s in tr])
    groups = np.array([s["group"] for s in tr])
    seed = derive_seed(d["fit_seed"], cfg) % 2**31
    print("grammar model", flush=True)
    g = fit_one(grammar_x(tr), y, groups, d, seed)
    print("lexical model: counting", flush=True)
    excluded = lexical_excluded()
    m, vocab = lexical_matrix(seg, None, d, workers, excluded)
    LEX.mkdir(parents=True, exist_ok=True)
    from scipy import sparse

    sparse.save_npz(LEX / "lexical_segments.npz", m)
    idx = [i for i, s in enumerate(seg) if s["split"] == "train"]
    lx = fit_one(lexical_x(m[idx], d["segment_words"]), y, groups, d, seed)
    joblib.dump({"grammar": g["model"], "lexical": lx["model"]}, LEX / "models.joblib")
    report = {**stamp(), "bins": bin_edges(d), "train_segments": len(tr),
              "grammar": {"C": g["C"], "cv": g["cv"], "features": F.NAMES},
              "lexical": {"C": lx["C"], "cv": lx["cv"], "vocabulary": vocab,
                          "excluded_words": len(excluded)}}  # fmt: skip
    (OUT / "models.json").write_text(json.dumps(report, indent=1) + "\n")
    coef = g["model"][-1].coef_
    (OUT / "grammar_coefficients.json").write_text(json.dumps(
        {"bins": bin_edges(d), "classes": g["model"][-1].classes_.tolist(),
         "features": {n: coef[:, j].round(4).tolist() for j, n in enumerate(F.NAMES)}},
        indent=1) + "\n")  # fmt: skip
    print(f"grammar C={g['C']}, lexical C={lx['C']} ({len(vocab)} words)")
    return 0


# ---- prediction on arbitrary text ---------------------------------------------------------------


def text_segments(text: str, size: int) -> list[str]:
    """Consecutive whole segments of a (masked) text; the last partial segment is dropped unless
    it is the only one."""
    toks = text.split()
    k = max(1, len(toks) // size)
    return [" ".join(toks[i * size : (i + 1) * size]) for i in range(k)]


def predict_texts(texts: list[str], models: dict, vocab: list[str], d: dict) -> dict:
    """Per segment probabilities from both models, for texts already cut to segments. The
    grammar model reads the text's own forms through the fold; the lexical model its words."""
    from scipy import sparse

    gx = np.log1p(np.array([F.rates(F.tokens(t)) for t in texts]))
    col = {w: j for j, w in enumerate(vocab)}
    r, c, v = [], [], []
    for i, t in enumerate(texts):
        for w, n in Counter(lex_tokens(t)).items():
            if w in col:
                r.append(i), c.append(col[w]), v.append(n)
    lm = sparse.csr_matrix((v, (r, c)), shape=(len(texts), len(vocab)), dtype=np.float32)
    lens = np.array([max(1, len(t.split())) for t in texts], dtype=np.float64)
    lx = np.log1p(lm.toarray() * (1000.0 / lens[:, None]))
    return {
        "grammar": _proba(models["grammar"], gx, d),
        "lexical": _proba(models["lexical"], lx, d),
    }


def _proba(m, x: np.ndarray, d: dict) -> np.ndarray:
    """Probabilities over every bin (a bin absent from training gets 0)."""
    edges = bin_edges(d)
    p = np.zeros((len(x), len(edges) - 1))
    p[:, m[-1].classes_] = m.predict_proba(x)
    return p


# ---- validation ---------------------------------------------------------------------------------


def median_shares(medians: np.ndarray, d: dict) -> dict[str, float]:
    """Shares of segments whose median year falls in the window and in the early window."""
    out = {}
    for k in ("window", "early_window"):
        lo, hi = d[k]
        out[k] = float(np.mean((medians >= lo) & (medians < hi + 1))) if len(medians) else 0.0
    return out


def h3_call(medians: np.ndarray, d: dict) -> str:
    """6.4 as amended (Amendment 19): H3a if more than ``majority_share`` of segments' median
    years fall in the window, H3b if they fall in the early window, otherwise neither."""
    sh = median_shares(medians, d)
    if sh["window"] > d["majority_share"]:
        return "H3a"
    if sh["early_window"] > d["majority_share"]:
        return "H3b"
    return "neither"


def _describe(prob: np.ndarray, years: np.ndarray | None, d: dict) -> dict:
    edges = bin_edges(d)
    s = np.array([summary(p, edges, d["interval"]) for p in prob])
    lo_w, hi_w = d["window"]
    inside = (s[:, 1] >= lo_w) & (s[:, 2] <= hi_w + 1)
    out = {"segments": len(prob), "median_year": float(np.median(s[:, 0])),
           "median_year_iqr": [float(np.percentile(s[:, 0], 25)),
                               float(np.percentile(s[:, 0], 75))],
           "share_interval_in_window": float(inside.mean()),
           **{f"share_median_{k}": v for k, v in median_shares(s[:, 0], d).items()},
           "call": h3_call(s[:, 0], d)}  # fmt: skip
    if years is not None:
        err = s[:, 0] - years
        out |= {"mae_years": float(np.mean(np.abs(err))), "bias_years": float(np.mean(err)),
                "interval_coverage": float(np.mean((s[:, 1] <= years) & (years <= s[:, 2] + 1))),
                "bin_accuracy": float(np.mean(prob.argmax(1) == [bin_of(y, edges)
                                                                 for y in years]))}  # fmt: skip
    return out


def _calls(by_volume: dict[str, list[float]], d: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for v in by_volume.values():
        c = h3_call(np.array(v), d)
        out[c] = out.get(c, 0) + 1
    return out


def _perm(a: np.ndarray, b: np.ndarray, n: int, seed: int) -> float:
    """Two-sided permutation p for a difference in means."""
    rng = np.random.default_rng(seed)
    pool, k = np.concatenate([a, b]), len(a)
    obs = abs(a.mean() - b.mean())
    hits = sum(
        abs(p[:k].mean() - p[k:].mean()) >= obs for p in (rng.permutation(pool) for _ in range(n))
    )
    return (hits + 1) / (n + 1)


def validate(workers: int) -> int:
    import joblib

    from eval.known_answer import separation
    from reuse.exact import masked_text

    cfg = load_config()
    d = cfg["dating"]
    edges = bin_edges(d)
    seg = _segments()
    models = joblib.load(LEX / "models.joblib")
    vocab = json.loads((OUT / "models.json").read_text())["lexical"]["vocabulary"]
    from scipy import sparse

    lm = sparse.load_npz(LEX / "lexical_segments.npz")
    val = [i for i, s in enumerate(seg) if s["split"] == "validation"]
    vs = [seg[i] for i in val]
    years = np.array([s["year"] for s in vs])
    probs = {
        "grammar": _proba(models["grammar"], grammar_x(vs), d),
        "lexical": _proba(models["lexical"], lexical_x(lm[val], d["segment_words"]), d),
    }
    res: dict = {**stamp(), "bins": edges, "held_out": {}}
    eras = {"1473-1699": (0, 1699), "1700-1779": (1700, 1779), "1780-1830": (1780, 1830)}
    for name, p in probs.items():
        r = {"all": _describe(p, years, d)}
        for era, (a, b) in eras.items():
            k = (years >= a) & (years <= b)
            r[era] = _describe(p[k], years[k], d)
        # 6.4 as amended applied to each held-out volume (its segments, usually two)
        wid = np.array([s["work_id"] for s in vs])
        meds = np.array([summary(q, edges, d["interval"])[0] for q in p])
        for era, (a, b) in eras.items():
            calls: dict[str, int] = {}
            for w in np.unique(wid[(years >= a) & (years <= b)]):
                c = h3_call(meds[wid == w], d)
                calls[c] = calls.get(c, 0) + 1
            r[era]["volume_calls"] = calls
        ybin = np.array([bin_of(y, edges) for y in years])
        r["by_bin"] = {f"{edges[b]}-{edges[b + 1] - 1}":
                       _describe(p[ybin == b], years[ybin == b], d)
                       for b in np.unique(ybin)}  # fmt: skip
        # keyed against OCR text in the decades that have both
        lo_k, hi_k = d["keyed_check_years"]
        k = (years >= lo_k) & (years <= hi_k)
        src = np.array([s["source"] for s in vs])
        r["keyed_vs_ocr"] = {"keyed": _describe(p[k & (src == "tcp")], years[k & (src == "tcp")],
                                                d),
                             "ocr": _describe(p[k & (src != "tcp")], years[k & (src != "tcp")],
                                              d)}  # fmt: skip
        res["held_out"][name] = r
    # King James imitation: pseudo-biblical controls (KJV spans removed, as the Book of Mormon
    # will be) against held-out ordinary volumes of the same years; and the King James text
    size, perms = d["segment_words"], d["permutations"]
    pb = [json.loads(ln) for ln in Path("data/controls/pseudo_biblical_primary.jsonl")
          .read_text().splitlines()]  # fmt: skip
    pb = [r for r in pb if (r["words"] or 0) >= size]
    pb_texts, pb_vol = [], []
    for r in pb:
        try:
            t = masked_text([r["work_id"]])
        except SystemExit:
            continue
        for s in text_segments(t, size):
            if len(s.split()) >= size:
                pb_texts.append(s), pb_vol.append(r["work_id"])
    pbp = predict_texts(pb_texts, models, vocab, d)
    kjv = " ".join(json.loads(ln)["text"] for ln in Path("data/kjv/kjv.jsonl").read_text()
                   .splitlines())  # fmt: skip
    kp = predict_texts(text_segments(kjv, size), models, vocab, d)
    ordinary = (years >= d["window"][0]) & (years <= d["window"][1])
    res["kjv_imitation"] = {}
    for name in probs:
        med_pb = np.array([summary(p, edges, d["interval"])[0] for p in pbp[name]])
        vol_pb = {}
        for w, m in zip(pb_vol, med_pb, strict=True):
            vol_pb.setdefault(w, []).append(m)
        a = np.array([np.mean(v) for v in vol_pb.values()])
        ov = {}
        for s, p in zip(np.array(vs)[ordinary], probs[name][ordinary], strict=True):
            ov.setdefault(s["work_id"], []).append(summary(p, edges, d["interval"])[0])
        b = np.array([np.mean(v) for v in ov.values()])
        res["kjv_imitation"][name] = {
            "pseudo_biblical": {
                **_describe(pbp[name], None, d),
                "volumes": len(a),
                "volume_calls": _calls(vol_pb, d),
            },
            "ordinary_1780_1830": {"volumes": len(b), "mean_median_year": float(b.mean())},
            "shift_years": float(a.mean() - b.mean()),
            "permutation_p": _perm(a, b, perms, derive_seed(d["permutation_seed"], cfg)),
            "king_james_text": _describe(kp[name], None, d),
        }
    # Amendment 9: score = median predicted year less the English text's year (higher: own time)
    ka = [json.loads(ln) for ln in Path("data/known_answer/set.jsonl").read_text().splitlines()]
    res["known_answer"] = {}
    texts = {}
    for t in ka:
        try:
            body = masked_text([v["work_id"] for v in t["volumes"]])
        except SystemExit:
            continue
        texts[t["key"]] = (text_segments(body, size), min(v["year"] for v in t["volumes"]))
    for name in probs:
        scores, per = {}, {}
        for key, (segs, year) in texts.items():
            p = predict_texts(segs, models, vocab, d)[name]
            med = float(np.median([summary(q, edges, d["interval"])[0] for q in p]))
            scores[key] = med - year
            per[key] = {"year": year, "median_predicted": med, "segments": len(segs),
                        "call": h3_call(np.array([summary(q, edges, d["interval"])[0]
                                                  for q in p]), d)}  # fmt: skip
        res["known_answer"][name] = {"texts": per, "separation": separation(scores, cfg)}
    (OUT / "validation.json").write_text(json.dumps(res, indent=1) + "\n")
    for name in probs:
        h = res["held_out"][name]
        print(f"{name}: held-out MAE {h['all']['mae_years']:.1f} y, coverage "
              f"{h['all']['interval_coverage']:.2f}; 1780-1830 in window "
              f"{h['1780-1830']['share_interval_in_window']:.2f}; KJV imitation shift "
              f"{res['kjv_imitation'][name]['shift_years']:+.1f} y "
              f"(p {res['kjv_imitation'][name]['permutation_p']:.4f}); known-answer p "
              f"{res['known_answer'][name]['separation']['p']:.3f}")  # fmt: skip
    return 0


def h3c(workers: int = 0) -> int:
    """6.4's H3c, after unblinding: a permutation test (``dating.permutations``, seed
    ``dating.permutation_seed``) on the predicted years of the Book of Mormon and of the
    pseudo-biblical control set, accepted if p exceeds ``dating.h3c_min_p``. One value per unit:
    each Book of Mormon chunk's mean segment median (``data/blind/unblinded.json``), each control
    volume's mean segment median (scored exactly as in ``validate``). Grammar decides; lexical
    beside. Writes ``data/dating/h3c.json``."""
    import joblib

    from reuse.exact import masked_text

    cfg = load_config()
    d = cfg["dating"]
    edges = bin_edges(d)
    size = d["segment_words"]
    models = joblib.load(LEX / "models.joblib")
    vocab = json.loads((OUT / "models.json").read_text())["lexical"]["vocabulary"]
    pb = [json.loads(ln) for ln in Path("data/controls/pseudo_biblical_primary.jsonl")
          .read_text().splitlines()]  # fmt: skip
    texts, vol = [], []
    for r in pb:
        if (r["words"] or 0) < size:
            continue
        try:
            t = masked_text([r["work_id"]])
        except SystemExit:
            continue
        for seg in text_segments(t, size):
            if len(seg.split()) >= size:
                texts.append(seg), vol.append(r["work_id"])
    pbp = predict_texts(texts, models, vocab, d)
    bom = json.loads(Path("data/blind/unblinded.json").read_text())["methods"]["dating"]["bom"]
    book_of = {
        json.loads(ln)["seq"]: json.loads(ln).get("book")
        for ln in Path("data/bom/1830/edition_1830.jsonl").read_text().splitlines()
    }
    chunk_seq = {
        json.loads(ln)["chunk_id"]: json.loads(ln)["seq_first"]
        for ln in Path("data/bom/segments/chunks.jsonl").read_text().splitlines()
    }
    out: dict = {**stamp(), "rule": f"accepted if p > {d['h3c_min_p']}", "models": {}}
    for name in ("grammar", "lexical"):
        meds = [summary(p, edges, d["interval"])[0] for p in pbp[name]]
        by: dict[str, list[float]] = {}
        for w, m in zip(vol, meds, strict=True):
            by.setdefault(w, []).append(m)
        b = np.array([np.mean(v) for v in by.values()])
        a = np.array([np.mean([seg[0] for seg in r[name]]) for r in bom.values()])
        p = _perm(a, b, d["permutations"], derive_seed(d["permutation_seed"], cfg))
        # robustness (BOM-38: chunks of one book are not independent): one value per book
        books: dict[str, list[float]] = {}
        for cid, v in zip(bom, a, strict=True):
            books.setdefault(book_of[chunk_seq[cid]], []).append(float(v))
        ab = np.array([np.mean(v) for v in books.values()])
        pb = _perm(ab, b, d["permutations"], derive_seed(d["permutation_seed"], cfg))
        out["models"][name] = {"book_of_mormon": {"chunks": len(a), "mean": float(a.mean()),
                                                  "median": float(np.median(a))},
                               "pseudo_biblical": {"volumes": len(b), "mean": float(b.mean()),
                                                   "median": float(np.median(b))},
                               "difference_years": float(a.mean() - b.mean()),
                               "permutation_p": p, "h3c": bool(p > d["h3c_min_p"]),
                               "by_book": {"books": len(ab), "mean": float(ab.mean()),
                                           "permutation_p": pb}}  # fmt: skip
        print(f"{name}: Book of Mormon {a.mean():.0f} ({len(a)} chunks) vs pseudo-biblical "
              f"{b.mean():.0f} ({len(b)} volumes); p {p:.4f}; H3c "
              f"{'accepted' if p > d['h3c_min_p'] else 'rejected'}; by book ({len(ab)}): "
              f"{ab.mean():.0f}, p {pb:.4f}", flush=True)  # fmt: skip
    out["h3c"] = out["models"]["grammar"]["h3c"]
    (OUT / "h3c.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"-> {OUT / 'h3c.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=("sample", "fit", "validate", "h3c"))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    return {"sample": sample, "fit": fit, "validate": validate, "h3c": h3c}[a.cmd](a.workers)


if __name__ == "__main__":
    sys.exit(main())
