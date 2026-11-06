"""The transformer cross-check of the dating classifier (BOM-29; Amendments 2, 17 and 29).

The same segments, bins, author split and decision rule as ``dating.classifier``, with the
features replaced by a transformer's: the time-locked ``dating.transformer_size`` model (BOM-27;
the Book of Mormon never entered its training), each segment folded as the grammar model reads it
(``dating.features.tokens``), cut into ``dating.transformer_window``-token windows, final hidden
states mean-pooled. The same regularised multinomial logistic regression (``fit_one``) is fitted on
the training segments and validated as the registered models are (held-out authors by era, 6.4 as
amended per volume, King James imitation, Amendment 9's separation), plus a leakage check: held-out
1780-1830 volumes the language model trained on against those it did not.

Reported beside the grammar model, which alone decides H3. Writes numbers only.

Usage::

    python -m dating.transformer embed      # -> data/corpus/dating/transformer_segments.npy
    python -m dating.transformer fit        # -> data/dating/transformer.json
    python -m dating.transformer validate   # -> data/dating/transformer_validation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from dating import classifier as C
from dating import features as F
from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

VECS = C.LEX / "transformer_segments.npy"


def embedder(cfg: dict):
    """folded text -> mean final hidden state of the time-locked model."""
    from tokenizers import Tokenizer

    from alm.benchmark import _base, _device
    from alm.variants import hidden
    from timelocked_lm.release import TOKENIZER

    d = cfg["dating"]
    dev = _device()
    model = _base(d["transformer_size"], cfg).to(dev).eval()
    tok = Tokenizer.from_file(str(TOKENIZER))
    w = d["transformer_window"]

    @torch.no_grad()
    def vec(text: str) -> np.ndarray:
        ids = tok.encode(" ".join(F.tokens(text))).ids
        n = max(1, len(ids) // w)
        x = torch.tensor((ids + [0] * w)[: n * w] if len(ids) >= w else ids, device=dev)
        h = hidden(model, x.view(n, -1))
        return h.mean(dim=(0, 1)).float().cpu().numpy().astype(np.float64)

    return vec


def embed() -> int:
    cfg = load_config()
    d = cfg["dating"]
    seg = C._segments()
    vec = embedder(cfg)
    part = C.LEX / "transformer_part.npz"
    got: dict[int, np.ndarray] = {}
    if part.exists():  # resume
        z = np.load(part)
        got = dict(zip(z["i"].tolist(), z["v"], strict=True))
    by: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(seg):
        if i not in got:
            by[s["work_id"]].append(i)
    import pyarrow.parquet as pq

    cat = {r["work_id"]: r for r in pq.read_table(
        "data/catalog/catalog.parquet", columns=["work_id", "source", "text_path"]
    ).to_pylist() if r["work_id"] in by}  # fmt: skip
    size = d["segment_words"]
    print(f"{sum(map(len, by.values())):,} segments to embed ({len(got):,} done)", flush=True)
    for k, (w, idx) in enumerate(sorted(by.items()), 1):
        toks = F.tokens(C.printed(cat[w]))
        for i in idx:
            c = seg[i]["chunk"]
            got[i] = vec(" ".join(toks[c * size : (c + 1) * size]))
        if k % 500 == 0 or k == len(by):
            ii = sorted(got)
            np.savez(part, i=np.array(ii), v=np.stack([got[j] for j in ii]))
            print(f"  {k:,}/{len(by):,} volumes", flush=True)
    np.save(VECS, np.stack([got[i] for i in range(len(seg))]).astype(np.float32))
    print(f"{len(seg):,} vectors -> {VECS}")
    return 0


def fit() -> int:
    import joblib

    cfg = load_config()
    d = cfg["dating"]
    seg = C._segments()
    x = np.load(VECS).astype(np.float64)
    tr = np.array([s["split"] == "train" for s in seg])
    y = np.array([s["bin"] for s in seg])
    groups = np.array([s["group"] for s in seg])
    r = C.fit_one(x[tr], y[tr], groups[tr], d, derive_seed("bom29-transformer", cfg))
    joblib.dump(r["model"], C.LEX / "transformer.joblib")
    (C.OUT / "transformer.json").write_text(json.dumps({**stamp(), "size": d["transformer_size"],
                                                      "C": r["C"], "cv": r["cv"]},
                                                     indent=1) + "\n")  # fmt: skip
    print(f"transformer model: C={r['C']} -> {C.OUT / 'transformer.json'}")
    return 0


def validate() -> int:
    import joblib
    import pyarrow.parquet as pq

    from eval.known_answer import separation
    from reuse.exact import masked_text

    cfg = load_config()
    d = cfg["dating"]
    edges = C.bin_edges(d)
    seg = C._segments()
    m = joblib.load(C.LEX / "transformer.joblib")
    x = np.load(VECS).astype(np.float64)
    val = [i for i, s in enumerate(seg) if s["split"] == "validation"]
    vs = [seg[i] for i in val]
    years = np.array([s["year"] for s in vs])
    p = C._proba(m, x[val], d)
    res: dict = {**stamp(), "size": d["transformer_size"], "bins": edges, "held_out": {}}
    eras = {"1473-1699": (0, 1699), "1700-1779": (1700, 1779), "1780-1830": (1780, 1830)}
    r = {"all": C._describe(p, years, d)}
    wid = np.array([s["work_id"] for s in vs])
    meds = np.array([C.summary(q, edges, d["interval"])[0] for q in p])
    for era, (a, b) in eras.items():
        k = (years >= a) & (years <= b)
        r[era] = C._describe(p[k], years[k], d)
        r[era]["volume_calls"] = C._calls({w: meds[wid == w] for w in np.unique(wid[k])}, d)
    # leakage: held-out 1780-1830 volumes in the language model's training split against the rest
    lm_train = {w for w, sp in zip(*pq.read_table("data/timelocked_lm/training_set.parquet",
                                                  columns=["work_id", "split"]).to_pydict()
                                   .values(), strict=True) if sp == "train"}  # fmt: skip
    k = (years >= 1780) & (years <= 1830)
    seen = np.array([w in lm_train for w in wid])
    r["leakage_1780_1830"] = {"in_lm_training": C._describe(p[k & seen], years[k & seen], d)
                              if (k & seen).any() else None,
                              "not_in_lm_training": C._describe(p[k & ~seen], years[k & ~seen], d)
                              if (k & ~seen).any() else None}  # fmt: skip
    res["held_out"]["transformer"] = r
    vec = embedder(cfg)
    size = d["segment_words"]

    def probs(texts: list[str]) -> np.ndarray:
        return C._proba(m, np.stack([vec(t) for t in texts]), d)

    pb = [json.loads(ln) for ln in Path("data/controls/pseudo_biblical_primary.jsonl")
          .read_text().splitlines()]  # fmt: skip
    pb_texts, pb_vol = [], []
    for row in pb:
        if (row["words"] or 0) < size:
            continue
        try:
            t = masked_text([row["work_id"]])
        except SystemExit:
            continue
        for s in C.text_segments(t, size):
            if len(s.split()) >= size:
                pb_texts.append(s), pb_vol.append(row["work_id"])
    pbp = probs(pb_texts)
    kjv = " ".join(json.loads(ln)["text"] for ln in Path("data/kjv/kjv.jsonl").read_text()
                   .splitlines())  # fmt: skip
    kp = probs(C.text_segments(kjv, size))
    vol_pb: dict[str, list[float]] = {}
    for w, q in zip(pb_vol, pbp, strict=True):
        vol_pb.setdefault(w, []).append(C.summary(q, edges, d["interval"])[0])
    a = np.array([np.mean(v) for v in vol_pb.values()])
    ov: dict[str, list[float]] = {}
    for w, mm in zip(wid[k], meds[k], strict=True):
        ov.setdefault(w, []).append(mm)
    b = np.array([np.mean(v) for v in ov.values()])
    res["kjv_imitation"] = {
        "pseudo_biblical": {**C._describe(pbp, None, d), "volumes": len(a),
                            "volume_calls": C._calls(vol_pb, d)},
        "ordinary_1780_1830": {"volumes": len(b), "mean_median_year": float(b.mean())},
        "shift_years": float(a.mean() - b.mean()),
        "permutation_p": C._perm(a, b, d["permutations"], derive_seed(d["permutation_seed"], cfg)),
        "king_james_text": C._describe(kp, None, d),
    }  # fmt: skip
    ka = [json.loads(ln) for ln in Path("data/known_answer/set.jsonl").read_text().splitlines()]
    scores, per = {}, {}
    for t in ka:
        try:
            body = masked_text([v["work_id"] for v in t["volumes"]])
        except SystemExit:
            continue
        segs, year = C.text_segments(body, size), min(v["year"] for v in t["volumes"])
        md = np.array([C.summary(q, edges, d["interval"])[0] for q in probs(segs)])
        scores[t["key"]] = float(np.median(md)) - year
        per[t["key"]] = {"year": year, "median_predicted": float(np.median(md)),
                         "segments": len(segs), "call": C.h3_call(md, d)}  # fmt: skip
    res["known_answer"] = {"texts": per, "separation": separation(scores, cfg)}
    out = C.OUT / "transformer_validation.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(f"transformer: held-out MAE {r['all']['mae_years']:.1f} y, coverage "
          f"{r['all']['interval_coverage']:.2f}; 1780-1830 median in window "
          f"{r['1780-1830']['share_median_window']:.2f}; KJV shift "
          f"{res['kjv_imitation']['shift_years']:+.1f} y; known-answer p "
          f"{res['known_answer']['separation']['p']:.3f} -> {out}")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=("embed", "fit", "validate"))
    a = ap.parse_args(argv)
    return {"embed": embed, "fit": fit, "validate": validate}[a.cmd]()


if __name__ == "__main__":
    sys.exit(main())
