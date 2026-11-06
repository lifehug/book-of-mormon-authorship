"""Simulated peer review of the paper (BOM-38; ``docs/simulated-review-plan.md``).

Three independent reviews, each by a fresh hosted-model call with no tools and no access to the
repository or the working sessions: the reviewer sees only the paper draft (every ``*.md`` under
``--draft``) and the pre-registration with its amendments, passed in the prompt. Each takes one
reviewer role (``ROLES``), is told it is simulating a referee, and must answer in the fixed shape
``parse`` checks (summary, major points, minor points, recommendation). Replies are saved verbatim
under ``paper/review/``, each headed SIMULATED, with the model, the date and the SHA-256 of
exactly what it was shown; a response-plan template then lists every point for a dated answer
(a revision or a recorded disagreement). Calls are paced (``semantic.skeleton._claude``); a
transient failure is retried on the next run, never saved as a review.

Usage::

    python -m review.simulate run --draft paper/draft [--model claude-opus-5-5]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

OUT = Path("paper/review")
PREREG = Path("paper/preregistration.md")

ROLES = {
    "statistician": "a statistician who referees authorship-attribution and classification "
    "papers; focus on the decision rules, calibration, multiple comparisons, the open-set "
    "false-match rate, independence assumptions in the synthesis, and whether the conclusions "
    "follow from the numbers",
    "historian": "a historian of early Mormonism and of the early American religious book "
    "trade; focus on the candidate and source lists, access evidence, the manuscripts and "
    "dictation, and whether the historical claims are fairly stated for every side",
    "stylometrist": "a computational stylometrist; focus on corpus construction, OCR and "
    "spelling normalization, King James masking, feature choice, the time-locked language "
    "models and their fine-tuning, imitation robustness, and replication of prior studies",
}

PROMPT = """You are simulating a peer reviewer for a research paper. You are {role}.
This is a simulated review: the paper's author is one person working with AI assistance, and
your review will be published labelled as SIMULATED. Be the strongest fair critic you can be.
You see only the materials below: the paper draft and its pre-registration with amendments.
The study takes no position on inspiration or the truth of the book's contents; judge only its
methods and claims.

Reply in exactly this shape (Markdown):
## Summary
(3-5 sentences: what the paper claims and how)
## Major points
1. ... (each: the problem, why it matters, what would fix it)
## Minor points
1. ...
## Recommendation
One of: accept, minor revision, major revision, reject; then one sentence why.

=== PAPER DRAFT ===
{draft}

=== PRE-REGISTRATION AND AMENDMENTS ===
{prereg}
"""


def materials(draft: Path) -> tuple[str, str]:
    files = sorted(draft.glob("*.md"))
    if not files:
        raise SystemExit(f"no *.md under {draft}")
    text = "\n\n".join(f"--- {p.name} ---\n{p.read_text()}" for p in files)
    return text, PREREG.read_text()


def parse(reply: str) -> dict | None:
    """The review's sections and points, or None when the reply lacks the fixed shape."""
    heads = {
        "summary": r"##\s*Summary",
        "major": r"##\s*Major points",
        "minor": r"##\s*Minor points",
        "recommendation": r"##\s*Recommendation",
    }
    pos = {}
    for k, pat in heads.items():
        m = re.search(pat, reply, re.I)
        if not m:
            return None
        pos[k] = m
    order = sorted(pos, key=lambda k: pos[k].start())
    if order != list(heads):
        return None
    sec = {}
    for i, k in enumerate(order):
        end = pos[order[i + 1]].start() if i + 1 < len(order) else len(reply)
        sec[k] = reply[pos[k].end() : end].strip()
    rec = re.search(
        r"\b(accept|minor revision|major revision|reject)\b", sec["recommendation"], re.I
    )
    if not rec:
        return None
    points = {k: re.findall(r"^\s*\d+\.\s+(.+)$", sec[k], re.M) for k in ("major", "minor")}
    return {"summary": sec["summary"], **points, "recommendation": rec.group(1).lower()}


def header(role: str, model: str, digest: str) -> str:
    return (
        f"# SIMULATED review: {role}\n\n> **SIMULATED.** Written by an AI model ({model}) "
        f"acting as a {role} referee, {dt.date.today().isoformat()}. No human reviewed this "
        f"work. Shown: the draft and the pre-registration, SHA-256 `{digest}`.\n\n"
    )


def response_plan(reviews: dict[str, dict]) -> str:
    lines = [
        "# Response plan (BOM-38)",
        "",
        "Every point from the SIMULATED reviews, each to be answered with a dated revision "
        "(commit) or a recorded disagreement with its reason.",
        "",
        "| Review | Kind | # | Point | Response | Commit or reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for role, r in reviews.items():
        for kind in ("major", "minor"):
            for i, p in enumerate(r[kind], 1):
                cell = " ".join(p.split()).replace("|", "/")
                lines.append(f"| {role} | {kind} | {i} | {cell} | [pending] | |")
    return "\n".join(lines) + "\n"


def run(draft: Path, model: str) -> int:
    from semantic import skeleton as sk

    sk._PACE["per_hour"] = 60  # three long calls; paced like every other model job
    text, prereg = materials(draft)
    digest = hashlib.sha256((text + prereg).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    reviews, missing = {}, []
    for role, desc in ROLES.items():
        path = OUT / f"review_{role}.md"
        if path.exists():  # done on an earlier run
            got = parse(path.read_text().split("\n\n", 2)[-1])
            if got:
                reviews[role] = got
                continue
        reply = sk._claude(PROMPT.format(role=desc, draft=text, prereg=prereg), model)
        got = parse(reply) if reply else None
        if got is None:
            if reply:
                sk._log_parse_failure(model, reply)
            missing.append(role)
            continue
        path.write_text(header(role, model, digest) + reply.strip() + "\n")
        reviews[role] = got
        print(
            f"  {role}: {len(got['major'])} major, {len(got['minor'])} minor, "
            f"{got['recommendation']}",
            flush=True,
        )
    if reviews:
        (OUT / "response_plan.md").write_text(response_plan(reviews))
    print(
        f"{len(reviews)} of {len(ROLES)} simulated reviews -> {OUT}"
        + (f"; retry: {', '.join(missing)}" if missing else "")
    )
    return 1 if missing else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--draft", type=Path, default=Path("paper/draft"))
    ap.add_argument("--model", default=None, help="default: config review.model")
    a = ap.parse_args(argv)
    if a.model is None:
        from metadata.config import load

        a.model = load()["review"]["model"]
    return run(a.draft, a.model)


if __name__ == "__main__":
    sys.exit(main())
