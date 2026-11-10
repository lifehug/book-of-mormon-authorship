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

from blind.seal import KEY, OUT, PLAN, SEALED, sha256


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


# ---- each scorer's records, read per candidate ------------------------------------------------
#
# The scorers return their own records per sealed id, keyed by candidate *unit* (candidate x sample
# type x period, Amendment 30): ``classic`` Burrows and Cosine Delta distances, General Imposters
# shares with 6.1's call, ENSC's label and posteriors; ``style`` cosine distances, GI on the
# vectors and the call; ``alm`` each candidate unit's margin over the best control model and the
# call. A view reads one closed-set statistic (and 6.1's call where the method verifies) from those
# records; a candidate's score is its best unit's, and its call that unit's call (as the synthesis
# reads them, ``synth.model.observations``).

# method -> view name -> (record -> (scores by unit, lower is closer, calls by unit or None))
VIEWS = {
    "classic": {
        "burrows_delta": lambda r: (r["burrows_delta"], True, None),
        "cosine_delta": lambda r: (r["cosine_delta"], True, None),
        "general_imposters": lambda r: (r["general_imposters"], False, r["gi_call"]),
        "general_imposters_achievable": lambda r: (
            r["general_imposters"],
            False,
            r.get("gi_call_achievable"),
        ),
        "ensc": lambda r: (r["ensc_posteriors"], False, None),
    },
    "style": {
        "style": lambda r: (r["cosine"], True, r["call"]),
        "style_achievable": lambda r: (r["cosine"], True, r.get("call_achievable")),
    },
    "style_mid": {
        "style_mid": lambda r: (r["cosine"], True, r["call"]),
        "style_mid_achievable": lambda r: (r["cosine"], True, r.get("call_achievable")),
    },
    "alm": {
        "alm": lambda r: (r["margins"], False, r.get("call")),  # larger margin is closer
        "alm_achievable": lambda r: (r["margins"], False, r.get("call_achievable")),
    },
}


# method -> record -> verification scores by unit (higher counts toward a match), for the ladder
LADDER = {
    "classic": lambda r: r["general_imposters"],
    "style": lambda r: r["general_imposters"],  # GI on the style vectors
    "style_mid": lambda r: r["general_imposters"],
    "alm": lambda r: r["margins"],  # best control model minus candidate model
}


def ladder_steps(method: str, size: str | None, thresholds: dict) -> list[dict] | None:
    th = {"classic": thresholds.get("general_imposters"), "style": thresholds.get("style"),
          "style_mid": thresholds.get("style_mid"),
          "alm": (thresholds.get("alm") or {}).get(size) if size else None}.get(method)  # fmt: skip
    return th.get("ladder") if th else None


def ladder_report(per: dict[str, dict], score_of, steps: list[dict], key: dict[str, dict],
                  units: dict[str, str], split: dict[str, str]) -> dict:  # fmt: skip
    """Owner, 2026-11-07: objective data. For every id and candidate (its best unit), the lowest
    rung at which it counts as a match. Book of Mormon chunks: per chunk, and per half and
    candidate the number of chunks matching at or below each rung. Decoys, beside them: candidate
    decoys, the rung at which their true candidate matches and whether another candidate matches
    at the same rung or lower; control decoys, the lowest rung at which any candidate matches
    (a false match). Rungs carry their real benchmark false- and true-match rates."""
    from blind.thresholds import rung

    rates = [st["rate"] for st in sorted(steps, key=lambda st: st["rate"])]
    table = [{k: st[k] for k in ("rate", "threshold", "false_match", "true_match")}
             for st in sorted(steps, key=lambda st: st["rate"])]  # fmt: skip

    def best(scores: dict[str, float]) -> dict[str, float]:
        out: dict[str, float] = {}
        for u, v in scores.items():
            c = units.get(u)
            if c is not None and (c not in out or v > out[c]):
                out[c] = float(v)
        return out

    def counts(rs: list[float | None]) -> dict[str, int]:
        return {**{str(r): sum(1 for x in rs if x is not None and x <= r) for r in rates},
                "none": sum(1 for x in rs if x is None)}  # fmt: skip

    chunks: dict[str, dict] = {}
    by_half: dict[str, dict[str, list]] = {}
    cand_decoys, control_decoys = [], []
    for i, rec in per.items():
        k = key.get(i)
        if k is None:
            continue
        sc = best(score_of(rec))
        rg = {c: rung(v, steps) for c, v in sc.items()}
        lowest = {c: (st["rate"] if st else None) for c, st in rg.items()}
        if k["kind"] == "bom":
            chunks[k["chunk_id"]] = {c: ({"rate": st["rate"], "false_match": st["false_match"]}
                                         if st else None) for c, st in rg.items()}  # fmt: skip
            half = split.get(k["chunk_id"], "unsplit")
            for c, r in lowest.items():
                by_half.setdefault(half, {}).setdefault(c, []).append(r)
        elif k["author"].startswith("control:"):
            hits = [r for r in lowest.values() if r is not None]
            control_decoys.append(min(hits) if hits else None)
        elif k["author"] in lowest:
            own = lowest[k["author"]]
            rival = [r for c, r in lowest.items() if c != k["author"] and r is not None]
            cand_decoys.append({"own": own, "rival_at_or_below": own is not None and any(
                r <= own for r in rival)})  # fmt: skip
    return {"ladder": table, "chunks": chunks,
            "by_half": {h: {c: counts(rs) for c, rs in cs.items()} for h, cs in by_half.items()},
            "decoys": {"candidate": {"decoys": len(cand_decoys),
                                     "own_match": counts([d["own"] for d in cand_decoys]),
                                     "rival_at_or_below": sum(d["rival_at_or_below"]
                                                              for d in cand_decoys)},
                       "control": {"decoys": len(control_decoys),
                                   "false_match": counts(control_decoys)}}}  # fmt: skip


def unit_candidates(plan: dict) -> dict[str, str]:
    """Candidate unit key -> candidate name (BOM-28's plan; controls have no candidate)."""
    return {u["key"]: u["candidate"] for u in plan["units"] if u["kind"] == "candidate"}


def by_candidate(scores: dict[str, float], lower: bool, calls: dict[str, str] | None,
                 units: dict[str, str]) -> dict:  # fmt: skip
    """One record read per candidate: its best unit's score and call, and the closed-set pick."""
    best: dict[str, str] = {}
    for u, v in scores.items():
        c = units.get(u)
        if c is None:
            continue
        if c not in best or (v < scores[best[c]] if lower else v > scores[best[c]]):
            best[c] = u
    cs = {c: float(scores[u]) for c, u in best.items()}
    first = ((min if lower else max)(cs, key=lambda c: (cs[c], c))) if cs else None
    calls_c = {c: calls[u] for c, u in best.items() if u in calls} if calls else None
    return {"first": first, "scores": cs, "lower_is_closer": lower, "calls": calls_c}


def normalise(per: dict[str, dict], view, units: dict[str, str]) -> dict[str, dict]:
    return {i: by_candidate(*view(r), units) for i, r in per.items()}


def decoy_accuracy(per_id: dict[str, dict], key: dict[str, dict]) -> dict:
    """Section 8 / Amendment 32: a candidate decoy is identified when attributed to its candidate;
    a control decoy when the method says no candidate. Closed set: candidate decoys whose
    candidate the method can name, first pick correct. Verification (methods with 6.1's call):
    a candidate decoy needs a *match* for its candidate and none for any other; a control decoy
    needs no *match* at all."""
    closed = [per_id[i]["first"] == k["author"] for i, k in key.items()
              if k["kind"] == "decoy" and i in per_id
              and k["author"] in per_id[i]["scores"]]  # fmt: skip
    out = {"closed_set": {"decoys": len(closed), "correct": sum(closed),
                          "accuracy": sum(closed) / len(closed) if closed else None}}  # fmt: skip
    ver = []
    for i, k in key.items():
        if k["kind"] != "decoy" or i not in per_id or per_id[i]["calls"] is None:
            continue
        matched = {c for c, b in per_id[i]["calls"].items() if b == "match"}
        if k["author"].startswith("control:"):
            ver.append(("control", not matched))
        elif k["author"] in per_id[i]["scores"]:
            ver.append(("candidate", matched == {k["author"]}))
    out["verification"] = ({kind: {"decoys": sum(1 for x, _ in ver if x == kind),
                                   "correct": sum(ok for x, ok in ver if x == kind)}
                            for kind in ("candidate", "control")} if ver else None)  # fmt: skip
    return out


def leave_one_out(per_id: dict[str, dict], key: dict[str, dict]) -> dict[str, dict[str, int]]:
    """For each candidate removed in turn, how the Book of Mormon ids' closed-set picks move."""
    cands = sorted({c for r in per_id.values() for c in r["scores"]})
    out = {}
    for drop in cands:
        calls: dict[str, int] = {}
        for i, r in per_id.items():
            s = {c: v for c, v in r["scores"].items() if c != drop}
            if key[i]["kind"] != "bom" or not s:
                continue
            best = (min if r["lower_is_closer"] else max)(s, key=lambda c: (s[c], c))
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


def unblind(files: list[str], key: dict[str, dict], plan: dict, split: dict[str, str],
            calibration: dict | None, thresholds: dict | None = None) -> dict:  # fmt: skip
    """Every output file read against the key: per method (model-based ones per size,
    ``alm_<size>``) the raw Book of Mormon records by chunk (what ``synth.model`` reads) and, for
    each view, decoy accuracy and leave-one-candidate-out; the sweep's discovery-half result."""
    units = unit_candidates(plan)
    methods: dict = {}
    for f in files:
        if not f.endswith(".json"):
            continue
        doc = json.loads(Path(f).read_text())
        name = f"{doc['method']}_{doc['size']}" if doc.get("size") else doc["method"]
        per = doc["scores"]
        if doc["method"] == "sweep":  # before the unwrap below: its "ids" is a count
            if calibration is not None:
                methods["sweep"] = sweep_result(Path(per["file"]), key, split, calibration)
            continue
        if isinstance(per, dict) and "ids" in per:  # scorers that also return their units table
            per = per["ids"]
        r: dict = {"bom": {key[i]["chunk_id"]: v for i, v in per.items()
                           if key[i]["kind"] == "bom"}}  # fmt: skip
        views = {}
        for v, view in VIEWS.get(doc["method"], {}).items():
            norm = normalise(per, view, units)
            views[v] = {"decoys": decoy_accuracy(norm, key),
                        "leave_one_candidate_out": leave_one_out(norm, key)}  # fmt: skip
        if views:
            r["views"] = views
        steps = ladder_steps(doc["method"], doc.get("size"), thresholds or {})
        if steps and doc["method"] in LADDER:
            r["ladder"] = ladder_report(per, LADDER[doc["method"]], steps, key, units, split)
        methods[name] = r
    return methods


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
    split = json.loads(Path("data/bom/segments/split.json").read_text())["assignment"]
    plan = json.loads(PLAN.read_text())
    cal_path = Path("data/sweep/calibration.json")
    cal = json.loads(cal_path.read_text()) if cal_path.exists() else None
    th = json.loads(Path("data/blind/thresholds.json").read_text())["thresholds"]
    res = {"seal": seal_doc,
           "methods": unblind(list(manifest["sha256"]), key, plan, split, cal, th)}  # fmt: skip
    (OUT / "unblinded.json").write_text(json.dumps(res, indent=1) + "\n")
    print(f"unblinded {len(res['methods'])} methods -> {OUT / 'unblinded.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
