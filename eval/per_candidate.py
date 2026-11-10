"""Each candidate sample, one by one, on the 168 Book of Mormon chunks (BOM-36, paper section 10).

Reads an unblinded file (``data/blind/unblinded.json`` for the registered run,
``data/blind/a43/unblinded.json`` for the run without Book of Mormon quotations) and reports, per
candidate sample and per method: mean rank among the candidate samples (1 = closest), how many
chunks rank it first, and how many chunks call it a match or inconclusive under the registered
rule (methods that make calls). "First" is the method's own recorded pick (its tie-breaking), and
tied scores share the mean of their ranks. A sample whose score is identical on every chunk was
not scorable (for the candidate models, a sample too short for one training sequence leaves the
base model unchanged) and is listed as such, outside the ranks. Descriptive: nothing new is
scored. Lower is closer for the language models' loss and the Deltas and style cosine distances;
higher is closer for General Imposters.

Writes names and numbers only: ``<run dir>/per_candidate.json``.

Usage::

    python -m eval.per_candidate report [--run registered|a43]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from metadata.config import stamp

RUNS = {"registered": Path("data/blind"), "a43": Path("data/blind/a43")}

# label -> (method key, score field, higher is closer, first field, call field or None)
METHODS = {
    "burrows_delta": ("classic", "burrows_delta", False, "burrows_first", None),
    "cosine_delta": ("classic", "cosine_delta", False, "cosine_first", None),
    "general_imposters": ("classic", "general_imposters", True, "gi_first", "gi_call"),
    "style_297m": ("style", "cosine", False, "first", "call"),
    "style_590m": ("style_mid", "cosine", False, "first", "call"),
    "alm_125m": ("alm_pilot", "scores", False, "first_candidate", "call"),
    "alm_297m": ("alm_base", "scores", False, "first_candidate", "call"),
    "alm_590m": ("alm_mid", "scores", False, "first_candidate", "call"),
}


def summarise(methods: dict) -> dict:
    out = {}
    for label, (key, field, higher, first_field, call_field) in METHODS.items():
        bom = methods.get(key, {}).get("bom")
        if not bom:
            continue
        chunks = list(bom.values())
        seen: dict[str, set] = {}
        for c in chunks:
            for u, s in c[field].items():
                if u.startswith("cand__"):
                    seen.setdefault(u, set()).add(s)
        unscorable = sorted(u for u, v in seen.items() if len(v) == 1)
        ranks, first, calls = Counter(), Counter(), {}
        for chunk in chunks:
            scores = {u: s for u, s in chunk[field].items() if u in seen and u not in unscorable}
            for u in scores:  # tied scores share the mean of their ranks
                ahead = sum((v > scores[u]) if higher else (v < scores[u]) for v in scores.values())
                ties = sum(v == scores[u] for v in scores.values())
                ranks[u] += ahead + (ties + 1) / 2
            pick = chunk.get(first_field)
            if pick:
                first[pick] += 1
            for u, c in (chunk.get(call_field) or {}).items() if call_field else ():
                calls.setdefault(u, Counter())[c] += 1
        n = len(chunks)
        out[label] = {
            "chunks": n,
            "not_scorable": unscorable,
            "units": {
                u: {
                    "mean_rank": round(ranks[u] / n, 2),
                    "first": first[u],
                    **(
                        {"match": calls[u]["match"], "inconclusive": calls[u]["inconclusive"]}
                        if u in calls
                        else {}
                    ),
                }
                for u in sorted(ranks)
            },
        }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--run", choices=sorted(RUNS), default="a43")
    a = p.parse_args(argv)
    d = RUNS[a.run]
    methods = json.loads((d / "unblinded.json").read_text())["methods"]
    res = {"stamp": stamp(), "run": a.run, "methods": summarise(methods)}
    (d / "per_candidate.json").write_text(json.dumps(res, indent=1) + "\n")
    for label, m in res["methods"].items():
        print(label, "not scorable:", ", ".join(m["not_scorable"]) or "none")
        for u, v in sorted(m["units"].items(), key=lambda x: x[1]["mean_rank"]):
            calls = f" match {v['match']} inc {v['inconclusive']}" if "match" in v else ""
            print(f"  {u:55s} rank {v['mean_rank']:5.2f} first {v['first']:3d}{calls}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
