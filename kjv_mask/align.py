"""KJV quotation and paraphrase masking (BOM-16).

Pre-registration 4.4: texts are aligned to the KJV with passim; a span is a *verbatim quote*
if it aligns with at least ``kjv_mask.verbatim.min_identity`` token identity over at least
``min_tokens`` tokens, a *close paraphrase* between the paraphrase identities, and *original*
otherwise. Attribution and dating read original spans only.

passim proposes candidate alignments between a text and KJV chapters. Its own alignment is
character-level and runs on past the quotation into the surrounding prose, so it is not the
span: inside each candidate the tokens are re-aligned (``difflib``, lowercased words) and the
4.4 classes are assigned to maximal token windows by their identity. Identity is the share of
the text's tokens in the window that align to an equal KJV token.

Amendment 2 registers passim's settings: word 5-grams, minimum alignment 8 tokens, maximum gap
100 characters, relative overlap 0.5, validated on a hand-checked sample of 200 alignments and
frozen before any Book of Mormon text is masked (``kjv_mask.passim`` in the config). It leaves
passim's minimum number of shared n-grams open, and that one cannot stay at passim's default of
5: an 8-token quotation holds only four 5-grams. It is chosen under Amendment 2's selection-rule
provision by ``kjv_mask.evaluate`` on planted quotations, never on the Book of Mormon (4.2).
The 8-token minimum is enforced on tokens here; passim's own ``--min-align`` counts characters
and is set low enough not to pre-empt it.

Tokens follow Amendment 2's registered tokenisation: Unicode NFKC, lowercased, long s folded,
split on non-alphanumerics except apostrophes and hyphens inside a word.

Usage::

    python -m kjv_mask.align run <targets.jsonl> -o <out dir> [--params '{"n": 4, ...}']

``targets.jsonl`` holds one ``{"id", "text"}`` per document.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from metadata.config import load as load_config

KJV = Path("data/kjv/kjv.jsonl")
JAVA_HOME = "/opt/homebrew/opt/openjdk@17"
SPARK_MEMORY = "6g"  # the default 1g runs out on whole books (exit 52)
_WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")


@dataclass
class Span:
    start: int  # character offsets into the target text
    end: int
    kind: str  # verbatim | paraphrase
    identity: float
    tokens: int
    ref: str  # KJV chapter id, e.g. kjv:ISA.53


def kjv_chapters() -> list[dict]:
    chapters: dict[str, list[str]] = {}
    for line in KJV.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        chapters.setdefault(f"kjv:{r['book']}.{r['chapter']}", []).append(r["text"])
    return [{"id": k, "series": "kjv", "text": " ".join(v)} for k, v in chapters.items()]


def run_passim(docs: list[dict], work: Path, params: dict) -> list[dict]:
    """passim over KJV chapters plus ``docs``; candidate alignments between the two series.

    Each input and settings combination gets its own directory, named by their hash; a
    directory that already holds passim's output is read rather than recomputed, so a grid
    resumes and nothing is ever deleted."""
    key = hashlib.sha256(
        json.dumps([params, [d["id"] for d in docs], [len(d["text"]) for d in docs]]).encode()
    ).hexdigest()[:16]
    work = work / key
    work.mkdir(parents=True, exist_ok=True)
    done = _finished(work)
    if done is not None:
        return _read_alignments(done)
    # a failed attempt leaves a partial directory Spark will not overwrite; each attempt gets
    # a fresh one rather than deleting the last
    attempt = 0
    while (work / f"out.{attempt}").exists() or (attempt == 0 and (work / "out").exists()):
        attempt += 1
    out_dir = work / ("out" if attempt == 0 else f"out.{attempt}")
    inp = work / "in.jsonl"
    with inp.open("w") as fh:
        for d in kjv_chapters() + [{**d, "series": "target"} for d in docs]:
            fh.write(json.dumps({"id": d["id"], "series": d["series"], "text": d["text"]}) + "\n")
    cmd = [
        "passim", "--fields", "series", "--filterpairs", "series <> series2", "--pairwise",
        "-n", str(params["n"]), "-m", str(params["min_match"]), "-a", str(params["min_align"]),
        "-g", str(params["gap"]), "--maxDF", str(params["max_df"]), "--log-level", "ERROR",
        "--src-overlap", str(params["overlap"]), "--dst-overlap", str(params["overlap"]),
        str(inp), str(out_dir),
    ]  # fmt: skip
    env = {**os.environ, "JAVA_HOME": JAVA_HOME,
           "SPARK_SUBMIT_ARGS": f"--driver-memory {SPARK_MEMORY}"}  # fmt: skip
    subprocess.run(cmd, check=True, env=env, capture_output=True)
    return _read_alignments(out_dir)


def _finished(work: Path) -> Path | None:
    """The output directory of a completed passim run under ``work``, if there is one."""
    for d in sorted(work.glob("out*")):
        if (d / "align.json" / "_SUCCESS").exists():
            return d
    return None


def _read_alignments(out_dir: Path) -> list[dict]:
    out = []
    for f in sorted((out_dir / "align.json").glob("*.json")):
        for line in f.read_text().splitlines():
            r = json.loads(line)
            if r["series"] == "kjv":  # passim orders the pair arbitrarily; normalise
                out.append({"ref": r["id"], "kb": r["begin"], "ke": r["end"],
                            "doc": r["id2"], "tb": r["begin2"], "te": r["end2"]})  # fmt: skip
            else:
                out.append({"ref": r["id2"], "kb": r["begin2"], "ke": r["end2"],
                            "doc": r["id"], "tb": r["begin"], "te": r["end"]})  # fmt: skip
    return out


def norm_token(tok: str) -> str:
    return unicodedata.normalize("NFKC", tok).lower().replace("ſ", "s")


def _tokens(text: str, offset: int) -> list[tuple[str, int, int]]:
    return [
        (norm_token(m.group(0)), offset + m.start(), offset + m.end()) for m in _WORD.finditer(text)
    ]


def classify(
    target: str, tb: int, te: int, kjv: str, kb: int, ke: int, ref: str, cfg: dict, seed: int
) -> list[Span]:
    """4.4 spans inside one candidate alignment.

    A span must contain an unbroken run of at least ``seed`` matching tokens -- passim's own
    n-gram order. Without that anchor a window of mostly function words reaches 0.60 by chance
    (``there can be no taxation without representation`` against Job 12 scored 0.62)."""
    v, p = cfg["kjv_mask"]["verbatim"], cfg["kjv_mask"]["paraphrase"]
    tt = _tokens(target[tb:te], tb)
    kt = _tokens(kjv[kb:ke], kb)
    if len(tt) < min(v["min_tokens"], p["min_tokens"]):
        return []
    hit = [0] * len(tt)
    sm = SequenceMatcher(a=[t[0] for t in tt], b=[t[0] for t in kt], autojunk=False)
    for blk in sm.get_matching_blocks():
        for i in range(blk.a, blk.a + blk.size):
            hit[i] = 1
    pre = [0]
    for h in hit:
        pre.append(pre[-1] + h)

    def best_windows(min_id: float, min_tok: int, taken: list[bool]) -> list[tuple[int, int]]:
        """Maximal windows (i, j) of >= min_tok tokens with identity >= min_id, greedy."""
        found = []
        i = 0
        n = len(tt)
        while i <= n - min_tok:
            if taken[i] or not hit[i]:
                i += 1
                continue
            j_best = None
            for j in range(n, i + min_tok - 1, -1):  # longest first
                if any(taken[i:j]):
                    continue
                if (pre[j] - pre[i]) / (j - i) >= min_id:
                    j_best = j
                    break
            if j_best is None:
                i += 1
                continue
            while j_best > i and not hit[j_best - 1]:  # do not end on a miss
                j_best -= 1
            if j_best - i >= min_tok:
                found.append((i, j_best))
                for k in range(i, j_best):
                    taken[k] = True
                i = j_best
            else:
                i += 1
        return found

    taken = [False] * len(tt)
    spans = []
    for kind, min_id, min_tok in (
        ("verbatim", v["min_identity"], v["min_tokens"]),
        ("paraphrase", p["min_identity"], p["min_tokens"]),
    ):
        for i, j in best_windows(min_id, min_tok, taken):
            if _longest_run(hit[i:j]) < seed:
                continue
            ident = (pre[j] - pre[i]) / (j - i)
            if kind == "paraphrase" and ident >= p["max_identity"]:
                kind_ = "verbatim"
            else:
                kind_ = kind
            spans.append(Span(tt[i][1], tt[j - 1][2], kind_, ident, j - i, ref))
    return spans


def _longest_run(flags: list[int]) -> int:
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return best


def registered_params(min_match: int | None = None) -> dict:
    """passim settings from the config (Amendment 2), with the selected ``min_match``."""
    p = load_config()["kjv_mask"]["passim"]
    return {
        "n": p["ngram"],
        "gap": p["max_gap_chars"],
        "overlap": p["relative_overlap"],
        "min_align": p["passim_min_align_chars"],
        "max_df": p["max_df"],
        "min_match": p.get("min_match") if min_match is None else min_match,
    }


def mask(docs: list[dict], work: Path, params: dict) -> dict[str, list[Span]]:
    cfg = load_config()
    chapters = {c["id"]: c["text"] for c in kjv_chapters()}
    texts = {d["id"]: d["text"] for d in docs}
    out: dict[str, list[Span]] = {d["id"]: [] for d in docs}
    for a in run_passim(docs, work, params):
        out[a["doc"]].extend(
            classify(
                texts[a["doc"]],
                a["tb"],
                a["te"],
                chapters[a["ref"]],
                a["kb"],
                a["ke"],
                a["ref"],
                cfg,
                params["n"],
            )  # fmt: skip
        )
    return {k: resolve(spans) for k, spans in out.items()}


def resolve(spans: list[Span]) -> list[Span]:
    """Overlapping candidates: keep the stronger class per region (verbatim over paraphrase)."""
    spans = sorted(spans, key=lambda s: (s.start, s.kind != "verbatim", -s.identity))
    kept: list[Span] = []
    for s in spans:
        if kept and s.start < kept[-1].end:
            if s.kind == "verbatim" and kept[-1].kind == "paraphrase":
                kept[-1] = s
            continue
        kept.append(s)
    return kept


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("targets", type=Path)
    r.add_argument("-o", "--out", type=Path, required=True)
    r.add_argument("--params", required=True, help="passim settings as JSON")
    a = ap.parse_args(argv)
    docs = [json.loads(ln) for ln in a.targets.read_text().splitlines()]
    spans = mask(docs, a.out / "passim", json.loads(a.params))
    with (a.out / "spans.jsonl").open("w") as fh:
        for doc, ss in spans.items():
            fh.write(json.dumps({"id": doc, "spans": [s.__dict__ for s in ss]}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
