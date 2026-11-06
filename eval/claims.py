"""The claims register filled from the results that exist (BOM-42; ``docs/public-claims.md``).

``data/claims/register.yaml`` lists every public claim the study answers, each with its decision
rule written before any result (``supported_if`` / ``contradicted_if``) and an ``evidence`` list
naming the results that feed it. ``table`` reads each piece of evidence that exists and records
its key numbers; evidence not yet produced (the blind run, the synthesis) is marked pending.
Verdicts come only from the register, set by hand from the rule after BOM-35; a claim without
one is pending, an untestable claim is reported as untestable with its reason, not dropped.

Evidence names: ``rare:<named key>`` (BOM-24), ``semantic:<key>`` and ``semantic_null:<key>``
(BOM-25), ``triage`` (BOM-26), ``dating:grammar|lexical|transformer`` (BOM-29), ``imitation``
(BOM-31), ``open_set`` (BOM-21/25), ``manuscript`` (BOM-34), ``synthesis`` (BOM-35),
``blind:unblinded|dating|scribes`` (BOM-32), ``file:<path>`` (exists or not).

Writes names and numbers only: ``data/claims/claims.json``.

Usage::

    python -m eval.claims table
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from metadata.config import stamp

REGISTER = Path("data/claims/register.yaml")
OUT = Path("data/claims/claims.json")
PENDING = "pending"

FILES = {
    "rare": Path("data/reuse/bom/rare.json"),
    "semantic": Path("data/semantic/named.json"),
    "semantic_null": Path("data/semantic/named_null.json"),
    "triage": Path("data/semantic/triage.json"),
    "dating": Path("data/dating/validation.json"),
    "dating_transformer": Path("data/dating/transformer_validation.json"),
    "imitation": Path("data/benchmark/imitation.json"),
    "open_set": Path("data/benchmark/open_set.json"),
    "manuscript": Path("data/manuscript/summary.json"),
    "synthesis": Path("data/synthesis/posterior_sizes.json"),
    "unblinded": Path("data/blind/unblinded.json"),
    "scribes": Path("data/benchmark/scribes.json"),
}


def _load(key: str) -> dict | None:
    p = FILES[key]
    return json.loads(p.read_text()) if p.exists() else None


def _pick(d: dict, keys: tuple[str, ...]) -> dict:
    return {k: d[k] for k in keys if k in d}


def evidence(name: str) -> dict:
    """One piece of evidence: its file, whether it exists, and its key numbers (or pending)."""
    kind, _, arg = name.partition(":")
    if kind == "file":
        return {"file": arg, "status": "present" if Path(arg).exists() else PENDING}
    if kind == "dating":
        key = "dating_transformer" if arg == "transformer" else "dating"
    elif kind == "blind":
        key = {"scribes": "scribes"}.get(arg, "unblinded")
    else:
        key = kind
    if key not in FILES:
        raise ValueError(f"unknown evidence {name!r}")
    out = {"file": str(FILES[key])}
    d = _load(key)
    if d is None:
        return {**out, "status": PENDING}
    out["status"] = "present"
    try:
        if kind == "rare":
            out["values"] = _pick(d["named"][arg], ("rank", "shared", "density", "p", "genre_p"))
            out["values"]["null_p99_density"] = d.get("null_p99_density")
        elif kind == "semantic":
            out["values"] = _pick(d["named"][arg], ("group", "rank", "of", "score", "parallels"))
        elif kind == "semantic_null":
            src = d["sources"].get(arg)
            out["values"] = (
                _pick(src, ("percentile", "rank", "of", "score", "null_p99"))
                if src
                else {"note": "no registered null for this source"}
            )
        elif kind == "triage":
            out["values"] = {
                **_pick(d, ("items", "agreement", "kappa")),
                "specific_both": len(d.get("specific_both", [])),
            }
        elif kind == "dating" and arg in ("grammar", "lexical"):
            k = d["kjv_imitation"][arg]
            out["values"] = {
                "kjv_imitation_shift_years": k["shift_years"],
                "kjv_imitation_p": k["permutation_p"],
                "held_out_mae": d["held_out"][arg]["all"].get("mae_years"),
            }
        elif kind == "dating":  # transformer cross-check
            out["values"] = {
                "held_out_mae": d["held_out"]["transformer"]["all"].get("mae_years"),
                "kjv_imitation_shift_years": d["kjv_imitation"]["shift_years"],
            }
        elif kind == "imitation":
            out["values"] = {
                m: {"forward": v["forward"].get("accuracy"), "weight": v["weight"]}
                for m, v in d["methods"].items()
            }
        elif kind == "open_set":
            out["values"] = {
                m: _pick(v, ("closed_set", "open_set_fpr", "passes"))
                for m, v in d["methods"].items()
            }
        elif kind == "manuscript":
            out["values"] = {"same_scribe_cowdery": d["same_scribe_cowdery"]}
    except (KeyError, TypeError) as e:  # a result file whose shape changed: say so, never guess
        out["status"], out["error"] = "unreadable", f"{type(e).__name__}: {e}"
    return out


def build(register: dict) -> dict:
    rows = []
    for c in register["claims"]:
        src = register["sources"].get(c["source"], {})
        row = {
            "id": c["id"],
            "source": c["source"],
            "stance": src.get("stance"),
            "testable": c["testable"],
            "tested_by": c.get("tested_by", []),
        }
        if c["testable"] == "none":
            row["status"], row["reason"] = "untestable", " ".join(c["reason"].split())
        else:
            row["evidence"] = [{"name": n, **evidence(n)} for n in c.get("evidence", [])]
            row["status"] = c["verdict"] or PENDING
        rows.append(row)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "register_version": register.get("version"),
        "frozen": register.get("frozen"),
        "claims": len(rows),
        "by_status": counts,
        "rows": rows,
        "note": "The register takes no side; untestable is not disproved.",
    }


def table() -> int:
    import yaml

    reg = yaml.safe_load(REGISTER.read_text())
    doc = {**stamp(), **build(reg)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    for r in doc["rows"]:
        ev = r.get("evidence", [])
        have = sum(e["status"] == "present" for e in ev)
        print(f"{r['id']:36s} {r['testable']:8s} {r['status']:11s} evidence {have}/{len(ev)}")
    print(f"{doc['claims']} claims {doc['by_status']} -> {OUT}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["table"])
    ap.parse_args(argv)
    return table()


if __name__ == "__main__":
    sys.exit(main())
