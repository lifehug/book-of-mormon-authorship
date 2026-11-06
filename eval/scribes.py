"""Do style shifts track narrators, or scribes and dictation order? (6.3, H1c; BOM-34).

6.3: narrators are *separable* if the classical methods distinguish them with accuracy at or above
the benchmark's accuracy for distinct known authors at the same sample size, and the dictation-order
and scribe segmentations do not explain the same variance better, by the same accuracy measure.

For each segmentation (``narrator``, ``scribe``, ``dictation_order``; BOM-17's chunks, whole
chunks of one size, labels with at least ``--min-chunks`` chunks; the scribe scheme without
``not_extant``), every chunk is classified by leave-one-out nearest centroid under Cosine Delta on
the middle registered MFW count, the vocabulary and z-scores fitted without the held-out chunk.
Reported per segmentation: accuracy, a label-permutation null (mean and p) and chance-corrected
accuracy, (accuracy - null mean) / (1 - null mean). The benchmark accuracy is Cosine Delta's at
the chunk size in ``data/benchmark/power.json``, averaged over the benchmark corpora. Verdict:
narrators separable when narrator accuracy reaches it and neither other segmentation's accuracy
is higher (the registered reading); chance-corrected accuracies beside it.

The chunks are Book of Mormon text, sealed until the blind run: this refuses to run before
``data/blind/unblinded.json`` exists. Writes numbers only.

Usage::

    python -m eval.scribes run [--size 2000 --permutations 1000 --min-chunks 3]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from metadata.config import derive_seed, stamp
from metadata.config import load as load_config

CHUNKS = Path("data/bom/segments/chunks.jsonl")
POWER = Path("data/benchmark/power.json")
UNBLINDED = Path("data/blind/unblinded.json")
OUT = Path("data/benchmark/scribes.json")
SCHEMES = ("narrator", "scribe", "dictation_order")


def loo_accuracy(docs: list[list[str]], labels: list[str], mfw: int,
                 min_frac: float = 0.2) -> float:  # fmt: skip
    """Leave-one-out nearest-centroid accuracy under Cosine Delta (vocabulary, centroids and
    z-scores from the other documents only)."""
    from classic.features import build_vocabulary, frequency_matrix

    counts = [Counter(d) for d in docs]
    hits = 0
    for i in range(len(docs)):
        rest = [j for j in range(len(docs)) if j != i]
        vocab = build_vocabulary([counts[j] for j in rest], top_n=mfw, min_doc_fraction=min_frac)
        x = frequency_matrix([counts[j] for j in rest], vocab)
        mu, sd = x.mean(axis=0), x.std(axis=0, ddof=1)
        sd[sd == 0] = 1.0
        z = (x - mu) / sd
        q = (frequency_matrix([counts[i]], vocab)[0] - mu) / sd
        labs = sorted({labels[j] for j in rest})
        best, best_d = None, np.inf
        for lab in labs:
            c = z[[k for k, j in enumerate(rest) if labels[j] == lab]].mean(axis=0)
            den = np.linalg.norm(c) * np.linalg.norm(q)
            dist = 1.0 - (c @ q) / den if den else 1.0
            if dist < best_d:
                best, best_d = lab, dist
        hits += best == labels[i]
    return hits / len(docs)


def assess(docs: list[list[str]], labels: list[str], mfw: int, perms: int, seed: int,
           min_frac: float = 0.2) -> dict:  # fmt: skip
    acc = loo_accuracy(docs, labels, mfw, min_frac)
    rng = random.Random(seed)
    null = []
    for _ in range(perms):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        null.append(loo_accuracy(docs, shuffled, mfw, min_frac))
    mean = float(np.mean(null)) if null else None
    p = (sum(n >= acc for n in null) + 1) / (len(null) + 1) if null else None
    corrected = (acc - mean) / (1 - mean) if null and mean < 1 else None
    return {"chunks": len(docs), "labels": dict(Counter(labels)), "accuracy": acc,
            "null_mean": mean, "p": p, "chance_corrected": corrected}  # fmt: skip


def verdict(results: dict[str, dict], benchmark_accuracy: float) -> dict:
    n = results["narrator"]["accuracy"]
    others = {k: v["accuracy"] for k, v in results.items() if k != "narrator"}
    cc = {k: v["chance_corrected"] for k, v in results.items()}
    return {"benchmark_accuracy": benchmark_accuracy,
            "narrator_reaches_benchmark": n >= benchmark_accuracy,
            "no_other_explains_better": all(a <= n for a in others.values()),
            "separable": n >= benchmark_accuracy and all(a <= n for a in others.values()),
            "chance_corrected_ranking": sorted(cc, key=lambda k: -(cc[k] or -9))}  # fmt: skip


def benchmark_accuracy(size: int) -> float:
    corp = json.loads(POWER.read_text())["corpora"]
    vals = [c["test_size"]["points"][str(size)]["cosine_delta"] for c in corp.values()
            if str(size) in c.get("test_size", {}).get("points", {})
            and c["test_size"]["points"][str(size)].get("cosine_delta") is not None]  # fmt: skip
    return float(np.mean(vals))


def run(size: int, perms: int, min_chunks: int) -> int:
    if not UNBLINDED.exists():
        raise SystemExit(f"{UNBLINDED} missing: the chunks are sealed until BOM-32 unblinds")
    from classic.features import tokenize

    cfg = load_config()
    mfw = sorted(cfg["classic"]["mfw"])[len(cfg["classic"]["mfw"]) // 2]
    chunks = [json.loads(ln) for ln in CHUNKS.read_text().splitlines()]
    results = {}
    for scheme in SCHEMES:
        sel = [c for c in chunks if c["scheme"] == scheme and c["chunk_words"] == size
               and not c["partial"] and c["label"] != "not_extant"]  # fmt: skip
        keep = {lab for lab, n in Counter(c["label"] for c in sel).items() if n >= min_chunks}
        sel = [c for c in sel if c["label"] in keep]
        results[scheme] = assess([tokenize(c["text"]) for c in sel], [c["label"] for c in sel],
                                 mfw, perms, derive_seed(f"bom34-scribes:{scheme}", cfg),
                                 cfg["classic"]["mfw_min_doc_fraction"])  # fmt: skip
        print(f"  {scheme}: {results[scheme]['chunks']} chunks, accuracy "
              f"{results[scheme]['accuracy']:.3f}, null {results[scheme]['null_mean']:.3f}",
              flush=True)  # fmt: skip
    doc = {**stamp(), "size": size, "mfw": mfw, "permutations": perms, "results": results,
           "verdict": verdict(results, benchmark_accuracy(size))}  # fmt: skip
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"narrators separable: {doc['verdict']['separable']} -> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--size", type=int, default=2000)
    ap.add_argument("--permutations", type=int, default=1000)
    ap.add_argument("--min-chunks", type=int, default=3)
    a = ap.parse_args(argv)
    return run(a.size, a.permutations, a.min_chunks)


if __name__ == "__main__":
    sys.exit(main())
