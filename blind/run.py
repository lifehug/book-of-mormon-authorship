"""Score the sealed set with every method (BOM-32; section 8). Never reads the key.

Each method's scorer takes the sealed rows (id, words, text) and returns, per id, numbers only:
per-candidate scores and the method's call where it attributes, the date distribution's summary
where it dates, distances to every swept author for the sweep. Model-based scorers take the
model size picked by the benchmark (``--size``). Each method's output goes to
``data/blind/outputs/<method>.json`` (or ``data/corpus/blind/`` where large) and every file's
SHA-256 to ``data/blind/outputs.json``, to be committed before ``blind.unblind`` is run.

Every method has a scorer (``classic.blind_score``, ``style_embed.blind_score``,
``alm.blind_score``, and dating and the sweep here); 6.1's calls use ``data/blind/thresholds.json``
(``blind.thresholds``, from benchmark data only), which must be committed first. ``--only`` runs a
subset (for a dry run on a test set, not for the real run).

Usage::

    python -m blind.run --size base|large [--only dating,sweep] [--sealed <path>]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np

from blind.seal import SEALED, sha256

OUTPUTS = Path("data/blind/outputs")
BIG = Path("data/corpus/blind")


def dating(rows: list[dict], cfg: dict, size: str) -> dict:
    """Grammar (decides H3) and lexical models, plus the transformer cross-check if fitted:
    each id's median year and 90% interval (6.4, Amendments 17, 19, 29). Ids of other lengths
    than ``dating.segment_words`` are cut into its segments and summarised by their medians."""
    import joblib

    from dating import classifier as C

    d = cfg["dating"]
    edges = C.bin_edges(d)
    models = joblib.load(C.LEX / "models.joblib")
    vocab = json.loads((C.OUT / "models.json").read_text())["lexical"]["vocabulary"]
    trans = None
    if (C.LEX / "transformer.joblib").exists():
        from dating.transformer import embedder

        trans = (joblib.load(C.LEX / "transformer.joblib"), embedder(cfg))
    out = {}
    for r in rows:
        segs = C.text_segments(r["text"], d["segment_words"])
        probs = C.predict_texts(segs, models, vocab, d)
        if trans:
            probs["transformer"] = C._proba(trans[0], np.stack([trans[1](s) for s in segs]), d)
        out[r["id"]] = {name: [list(C.summary(q, edges, d["interval"])) for q in p]
                        for name, p in probs.items()}  # fmt: skip
    return out


def sweep(rows: list[dict], cfg: dict, size: str) -> dict:
    """Each id's distance to every swept author under both signals (Amendment 28). The
    discovery half's mean and the leads are formed only after unblinding, from these."""
    from classic.features import relative_frequencies, tokenize
    from style_embed.benchmark import MODEL, embedder
    from sweep.calibrate import _load, distances
    from sweep.units import OUT as SWEEP

    vocab = json.loads((SWEEP / "vocabulary.json").read_text())["vocabulary"]
    mfw, sty = _load("mfw.npz", "X"), _load("style.npz", "V")
    authors = sorted(u.split(":", 1)[1] for u in mfw if u.startswith("profile:"))
    gm = np.stack([mfw[f"profile:{a}"] for a in authors]).astype(np.float64)
    gs = np.stack([sty[f"profile:{a}"] for a in authors]).astype(np.float64)
    mean, std = gm.mean(axis=0), gm.std(axis=0, ddof=1)
    std[std == 0] = 1.0
    emb = embedder(MODEL, cfg)
    from collections import Counter

    ids = [r["id"] for r in rows]
    dm = np.zeros((len(rows), len(authors)), dtype=np.float32)
    ds = np.zeros_like(dm)
    for i, r in enumerate(rows):
        toks = tokenize(r["text"])
        dm[i] = distances(gm, relative_frequencies(Counter(toks), vocab)[None, :], "mfw", mean, std)
        ds[i] = distances(gs, emb(toks)[None, :], "style")
    BIG.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(BIG / "sweep_distances.npz", ids=np.array(ids), authors=np.array(authors),
                        mfw=dm, style=ds)  # fmt: skip
    return {"file": str(BIG / "sweep_distances.npz"), "ids": len(ids), "authors": len(authors)}


_shared: dict = {}


def _refs_pool(cfg: dict) -> tuple[dict, list]:
    """Candidate references (withheld spans removed) and the imposter pool, built once."""
    if not _shared:
        from classic.blind_score import pool, references

        _shared["refs"], _shared["pool"] = references(), pool(cfg)
    return _shared["refs"], _shared["pool"]


def classic(rows: list[dict], cfg: dict, size: str) -> dict:
    """Burrows and Cosine Delta, General Imposters (6.1 call) and ENSC per id (BOM-20/21)."""
    from blind.thresholds import load
    from classic.blind_score import score, units_table

    refs, imp = _refs_pool(cfg)
    return {"units": units_table(refs), "ids": score(rows, cfg, refs, imp, load())}


def style(rows: list[dict], cfg: dict, size: str) -> dict:
    """Cosine distance to each unit's profile and GI on the vectors (6.1 call) per id (BOM-30)."""
    from blind.thresholds import load
    from classic.blind_score import units_table
    from style_embed.blind_score import score

    refs, imp = _refs_pool(cfg)
    return {"units": units_table(refs), "ids": score(rows, cfg, refs, imp, load())}


def alm(rows: list[dict], cfg: dict, size: str) -> dict:
    """Each candidate and control model's score, the closed set and 6.1's margin call (BOM-28)."""
    from alm.blind_score import score
    from blind.thresholds import load

    th = load()
    if not th.get("alm"):
        raise SystemExit("no ALM thresholds: run alm.candidates validate, then blind.thresholds")
    return {"ids": score(rows, cfg, size, th)}


METHODS: dict[str, Callable] = {
    "classic": classic,
    "alm": alm,
    "style": style,
    "dating": dating,
    "sweep": sweep,
}


def run(rows: list[dict], cfg: dict, size: str, only: list[str] | None,
        out: Path = OUTPUTS) -> dict:  # fmt: skip
    from metadata.config import stamp

    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in only or list(METHODS):
        res = METHODS[name](rows, cfg, size)
        p = out / f"{name}.json"
        p.write_text(json.dumps({**stamp(), "method": name, "size": size, "scores": res},
                                indent=1) + "\n")  # fmt: skip
        files[str(p)] = sha256(p)
        if isinstance(res, dict) and "file" in res:
            files[res["file"]] = sha256(Path(res["file"]))
        print(f"  {name}: {len(res)} entries", flush=True)
    manifest = {"size": size, "methods": only or list(METHODS), "sha256": files}
    (out.parent / "outputs.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    from metadata.config import load as load_config

    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--size", required=True, choices=["pilot", "base", "large"])
    ap.add_argument("--only", default="")
    ap.add_argument("--sealed", type=Path, default=SEALED)
    a = ap.parse_args(argv)
    rows = [json.loads(ln) for ln in a.sealed.read_text().splitlines()]
    only = [m for m in a.only.split(",") if m] or None
    m = run(rows, load_config(), a.size, only)
    print(f"{len(m['sha256'])} outputs hashed -> data/blind/outputs.json; commit before unblinding")
    return 0


if __name__ == "__main__":
    sys.exit(main())
