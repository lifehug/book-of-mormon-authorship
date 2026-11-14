"""*View of the Hebrews* beside the Book of Mormon, for the reader (exploratory; adds no test).

Everything here re-reads results that exist (``data/semantic/named.json``, ``named_null.json``,
``skeleton/bom.json``, ``skeleton/controls.json``, ``data/reuse/bom/rare.json``) and pulls out,
by fixed rules, the examples a reader needs to see them:

- **ideas**: with the registered embedding model and 128-word passages, the ``closeup.show``
  closest passage pairs between the Book of Mormon and the 1823 *View of the Hebrews* (one per
  source passage), and the passages of each book whose best match in the other is weakest
  (passages that are mostly digits or page references, an errata list or an index, are skipped).
  Passages are shown by their first ``closeup.words`` words.
- **story**: the event lists of ``semantic.skeleton`` (written by a model, names replaced by
  roles) for the Book of Mormon and *View of the Hebrews*, and for Josephus and Genesis-Judges
  as the yardstick: for every event of the second text, its closest event in the first when the
  two pass the registered match threshold; which of those lie on the best in-order alignment;
  the closest pairs and the events with the weakest partner.

The 1823 text is the project's Internet Archive copy (public domain); no licensed text is read.

Usage::

    python -m semantic.closeup     # -> data/semantic/closeup_view_of_the_hebrews.json
"""

from __future__ import annotations

import json
import re
import sys

import numpy as np

from metadata.config import load as load_config
from metadata.config import stamp

OUT = "data/semantic/closeup_view_of_the_hebrews.json"
KEY = "view_of_the_hebrews_1823"


def head(text: str, n: int) -> str:
    w = text.split()
    return " ".join(w[:n]) + (" ..." if len(w) > n else "")


def prose(text: str) -> bool:
    """Not an errata list or an index: few digits among the words."""
    w = text.split()
    return sum(bool(re.search(r"\d", x)) for x in w) / max(1, len(w)) < 0.08


def traceback(match: np.ndarray, cfg: dict) -> list[tuple[int, int]]:
    """The matched (row, column) pairs on ``semantic.skeleton.sw_align``'s best alignment."""
    s = cfg["skeleton"]
    n, m = match.shape
    h = np.zeros((n + 1, m + 1))
    for i in range(1, n + 1):
        sc = np.where(match[i - 1], s["match_score"], s["mismatch_score"])
        for j in range(1, m + 1):
            h[i, j] = max(0.0, h[i - 1, j - 1] + sc[j - 1], h[i - 1, j] + s["gap_score"],
                          h[i, j - 1] + s["gap_score"])  # fmt: skip
    i, j = np.unravel_index(int(h.argmax()), h.shape)
    out = []
    while i > 0 and j > 0 and h[i, j] > 0:
        sc = s["match_score"] if match[i - 1, j - 1] else s["mismatch_score"]
        if np.isclose(h[i, j], h[i - 1, j - 1] + sc):
            if match[i - 1, j - 1]:
                out.append((int(i - 1), int(j - 1)))
            i, j = i - 1, j - 1
        elif np.isclose(h[i, j], h[i - 1, j] + s["gap_score"]):
            i -= 1
        else:
            j -= 1
    return out[::-1]


def story(a: str, b: str, thr: float, cfg: dict, texts: bool) -> dict:
    from semantic import skeleton as sk

    def events(name: str) -> list[str]:
        rows = sk._rows(name)
        return sk._flat([rows[k]["events"] for k in sorted(rows)])[0]

    A, B = events(a), events(b)
    S = sk.embed(A, cfg) @ sk.embed(B, cfg).T
    M = S >= thr
    run = set(traceback(M, cfg))
    lines = []
    for j in np.where(M.any(axis=0))[0]:
        i = int(S[:, j].argmax())
        on = any(jj == j for _, jj in run)
        if on:
            i = next(ii for ii, jj in run if jj == j)
        row = {"a": round(i / len(A), 4), "b": round(int(j) / len(B), 4), "in_order": on,
               "sim": round(float(S[i, j]), 3)}  # fmt: skip
        if texts:
            row.update(a_event=A[i], b_event=B[int(j)])
        lines.append(row)
    out = {"a": a, "b": b, "a_events": len(A), "b_events": len(B),
           "b_events_with_a_lookalike": int(M.any(axis=0).sum()), "in_order": len(run),
           "lines": lines}  # fmt: skip
    if texts:
        n = cfg["closeup"]["show"]
        out["weakest_a"] = [{"sim": round(float(S[i].max()), 3), "event": A[i]}
                            for i in np.argsort(S.max(axis=1))[:n]]  # fmt: skip
        out["weakest_b"] = [{"sim": round(float(S[:, j].max()), 3), "event": B[j]}
                            for j in np.argsort(S.max(axis=0))[:n]]  # fmt: skip
    return out


def ideas(cfg: dict) -> dict:
    from semantic.index import _model
    from semantic.search import CANDIDATES, NAMED, _embed, bom_queries, text_passages

    s, c = cfg["semantic"], cfg["closeup"]
    q = [x for x in bom_queries(s["passage_words"]) if x["kjv_share"] <= s["max_query_kjv_share"]]
    text = (CANDIDATES / NAMED[KEY][1]).read_text(encoding="utf-8", errors="replace")
    ps = text_passages(text, cfg)
    m = _model(cfg)
    S = _embed(m, [x["text"] for x in q], cfg) @ _embed(m, ps, cfg).T
    closest, used = [], set()
    for i in np.argsort(-S.max(axis=1)):
        j = int(S[i].argmax())
        if j in used or not prose(ps[j]):
            continue
        used.add(j)
        closest.append({"sim": round(float(S[i, j]), 3), "bom": head(q[i]["text"], c["words"]),
                        "source": head(ps[j], c["words"])})  # fmt: skip
        if len(closest) == c["show"]:
            break
    weak_s = [{"sim": round(float(S[:, j].max()), 3), "text": head(ps[j], c["words"])}
              for j in np.argsort(S.max(axis=0)) if prose(ps[j])][: c["show"]]  # fmt: skip
    weak_b = [{"sim": round(float(S[i].max()), 3), "text": head(q[i]["text"], c["words"])}
              for i in np.argsort(S.max(axis=1))][: c["show"]]  # fmt: skip
    return {"bom_passages": len(q), "source_passages": len(ps),
            "typical_best_match": round(float(np.median(S.max(axis=1))), 3),
            "closest": closest, "weakest_source": weak_s, "weakest_bom": weak_b}  # fmt: skip


def run() -> int:
    cfg = load_config()
    c = cfg["closeup"]
    named = json.loads(open("data/semantic/named.json").read())
    null = json.loads(open("data/semantic/named_null.json").read())["sources"][
        "view_of_the_hebrews_1825"]  # fmt: skip
    sk_bom = json.loads(open("data/semantic/skeleton/bom.json").read())
    ctl = json.loads(open("data/semantic/skeleton/controls.json").read())["controls"]
    rare = json.loads(open("data/reuse/bom/rare.json").read())
    thr = sk_bom["event_match"]
    vals = np.array(list(null["null"].values()))
    edges = c["null_bands"]
    bands = [{"from": a, "to": b, "books": int(((vals >= a) & (vals < b)).sum())}
             for a, b in zip(edges[:-1], edges[1:], strict=True)]  # fmt: skip
    reg = sk_bom["named"][KEY]
    doc = {
        **stamp(), "exploratory": True,
        "words": {"shared_rare_phrases": rare["named"]["view_of_the_hebrews"]["shared"],
                  "score": round(rare["named"]["view_of_the_hebrews"]["density"], 2),
                  "bar": round(rare["null_p99_density"], 2)},
        "ideas_subject": [{"title": r["title"], "score": round(r["score"], 1)}
                          for r in named["groups"]["origins"]["ranking"][: c["subject_top"]]],
        "ideas_subject_of": named["groups"]["origins"]["members"],
        "ideas_null": {"books": len(vals), "score": round(null["score"], 1),
                       "bar": round(null["null_p99"], 1), "median": round(null["null_median"], 1),
                       "percentile": null["percentile"],
                       "closer_books": int((vals > null["score"]).sum()), "bands": bands},
        "ideas": ideas(cfg),
        "story_registered": {k: reg[k] for k in ("matched", "order_p", "rank", "of")},
        "story_controls": {k: {x: v[x] for x in ("matched", "order_p")} for k, v in ctl.items()},
        "story": story("bom", KEY, thr, cfg, texts=True),
        "story_yardstick": story("josephus", "kjv:GEN-JDG", thr, cfg, texts=False),
    }  # fmt: skip
    with open(OUT, "w") as f:
        f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    s, y = doc["story"], doc["story_yardstick"]
    print(f"story: {s['b_events_with_a_lookalike']} of {s['b_events']} events have a look-alike, "
          f"{s['in_order']} in order; yardstick {y['b_events_with_a_lookalike']} of "
          f"{y['b_events']}, {y['in_order']} in order -> {OUT}")  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(run())
