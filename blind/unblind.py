"""Unblind the run (BOM-32; section 8): check every hash, apply the key, score the decoys, form the
sweep's discovery-half result, and run leave-one-candidate-out.

Refuses unless the key and sealed set match ``data/blind/seal.json`` and every output matches
``data/blind/outputs.json``, and both files are committed with no local changes (so the outputs
were fixed before the key was read). Decoys must be attributed at the method's benchmark accuracy
(section 8); a shortfall is reported and the run is repeated with the fault documented.

Writes names and numbers only: ``data/blind/unblinded.json``.

Usage::

    python -m blind.unblind [--key ~/.bom-blind/key.json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from blind.seal import KEY, OUT, SEALED, sha256


def committed(paths: list[Path]) -> bool:
    """Each path is tracked by git and unchanged since the last commit."""
    for p in paths:
        if subprocess.run(["git", "ls-files", "--error-unmatch", str(p)],
                          capture_output=True).returncode:  # fmt: skip
            return False
        if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(p)]).returncode:
            return False
    return True


def verify(seal_doc: dict, key: Path, sealed: Path, manifest: dict) -> list[str]:
    """Every hash problem found (empty when all match)."""
    bad = []
    if sha256(key) != seal_doc["key_sha256"]:
        bad.append("key does not match seal.json")
    if sha256(sealed) != seal_doc["sealed_sha256"]:
        bad.append("sealed set does not match seal.json")
    for f, h in manifest["sha256"].items():
        if not Path(f).exists() or sha256(Path(f)) != h:
            bad.append(f"output {f} does not match outputs.json")
    return bad


def decoy_accuracy(per_id: dict[str, dict], key: dict[str, dict]) -> dict:
    """Share of decoys (whose author the method can name) the method attributes correctly."""
    hits, n = 0, 0
    for i, r in per_id.items():
        k = key[i]
        if k["kind"] != "decoy" or "predicted" not in r or k["author"] not in r.get("scores", {}):
            continue
        n += 1
        hits += r["predicted"] == k["author"]
    return {"decoys": n, "correct": hits, "accuracy": hits / n if n else None}


def leave_one_out(per_id: dict[str, dict], key: dict[str, dict], lower_is_closer: bool = True
                  ) -> dict[str, dict[str, int]]:  # fmt: skip
    """For each candidate removed in turn, how the Book of Mormon ids' closed-set calls move."""
    cands = sorted({c for r in per_id.values() for c in r.get("scores", {})})
    out = {}
    for drop in cands:
        calls: dict[str, int] = {}
        for i, r in per_id.items():
            if key[i]["kind"] != "bom" or not r.get("scores"):
                continue
            s = {c: v for c, v in r["scores"].items() if c != drop}
            best = (min if lower_is_closer else max)(s, key=lambda c: (s[c], c))
            calls[best] = calls.get(best, 0) + 1
        out[drop] = calls
    return out


def sweep_result(dist: Path, key: dict[str, dict], split: dict[str, str],
                 calibration: dict) -> dict:  # fmt: skip
    """The discovery half's mean distance per author under both signals; leads beat both
    thresholds (6.6, Amendment 28); reported against the expected false-lead count."""
    z = np.load(dist)
    ids = z["ids"].tolist()
    disc = [j for j, i in enumerate(ids) if key[i]["kind"] == "bom"
            and split.get(key[i]["chunk_id"]) == "discovery"]  # fmt: skip
    m, s = z["mfw"][disc].mean(axis=0), z["style"][disc].mean(axis=0)
    t = calibration["lead_threshold"]
    lead = (m < t["mfw"]) & (s < t["style"])
    authors = z["authors"].tolist()
    order = np.argsort(m + s)
    return {"discovery_chunks": len(disc), "leads": [authors[j] for j in np.where(lead)[0]],
            "lead_count": int(lead.sum()),
            "expected_false_leads": calibration["expected_false_leads"],
            "nearest_20": [{"author": authors[j], "mfw": float(m[j]), "style": float(s[j])}
                           for j in order[:20]]}  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--key", type=Path, default=KEY)
    a = ap.parse_args(argv)
    seal_doc = json.loads((OUT / "seal.json").read_text())
    manifest = json.loads((OUT / "outputs.json").read_text())
    if not committed([OUT / "seal.json", OUT / "outputs.json"]):
        raise SystemExit("commit data/blind/seal.json and outputs.json before unblinding")
    bad = verify(seal_doc, a.key.expanduser(), SEALED, manifest)
    if bad:
        raise SystemExit("; ".join(bad))
    key = json.loads(a.key.expanduser().read_text())
    res: dict = {"seal": seal_doc, "methods": {}}
    for f in manifest["sha256"]:
        if not f.endswith(".json"):
            continue
        doc = json.loads(Path(f).read_text())
        per = doc["scores"]
        if doc["method"] == "sweep":
            split = json.loads(Path("data/bom/segments/split.json").read_text())["assignment"]
            cal = json.loads(Path("data/sweep/calibration.json").read_text())
            res["methods"]["sweep"] = sweep_result(Path(per["file"]), key, split, cal)
            continue
        r = {"decoys": decoy_accuracy(per, key)}
        if any("scores" in v for v in per.values()):
            r["leave_one_candidate_out"] = leave_one_out(per, key)
        r["bom"] = {key[i]["chunk_id"]: v for i, v in per.items() if key[i]["kind"] == "bom"}
        res["methods"][doc["method"]] = r
    (OUT / "unblinded.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"unblinded {len(res['methods'])} methods -> {OUT / 'unblinded.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
