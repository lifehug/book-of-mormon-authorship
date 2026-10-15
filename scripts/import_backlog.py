"""Import docs/backlog.md into GitHub labels, milestones, and issues.

Dry run by default: prints what would be created and writes the full issue bodies to
``--out``. Pass ``--apply`` to create things with ``gh``. Safe to re-run: existing labels
are updated in place, and milestones or issues whose title already exists are skipped.

Issue titles are prefixed ``BOM-NN`` and ``#N`` references in bodies become ``BOM-NN``,
because the repository's old issues and PRs already occupy GitHub numbers 1-10.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "backlog.md"

PHASE_RE = re.compile(r"^## Phase (\d+) — (.+)$")
ISSUE_RE = re.compile(r"^### #(\d+) (.+)$")
REF_RE = re.compile(r"#(\d{1,2})\b")

PHASE_COLORS = ["5319e7", "0052cc", "006b75", "0e8a16", "fbca04", "d93f0b", "b60205", "000000"]


def bom_id(n: int | str) -> str:
    return f"BOM-{int(n):02d}"


@dataclass
class Phase:
    number: int
    title: str
    intro: str = ""

    @property
    def label(self) -> str:
        return f"phase-{self.number}"

    @property
    def milestone(self) -> str:
        return f"Phase {self.number} — {self.title}"


@dataclass
class Issue:
    number: int
    title: str
    phase: int
    lines: list[str] = field(default_factory=list)

    @property
    def gh_title(self) -> str:
        return f"{bom_id(self.number)} {self.title}"

    def body(self, phase: Phase) -> str:
        text = "\n".join(self.lines).strip("\n")
        text = REF_RE.sub(lambda m: bom_id(m.group(1)), text)
        footer = (
            f"\n\n---\n{phase.milestone}. Imported from `docs/backlog.md`; "
            "that file is the source of truth for the work plan."
        )
        return text + footer


def parse(text: str) -> tuple[dict[int, Phase], list[Issue]]:
    phases: dict[int, Phase] = {}
    issues: list[Issue] = []
    phase: Phase | None = None
    issue: Issue | None = None
    for line in text.splitlines():
        if m := PHASE_RE.match(line):
            phase = Phase(int(m.group(1)), m.group(2).strip())
            phases[phase.number] = phase
            issue = None
            continue
        if m := ISSUE_RE.match(line):
            if phase is None:
                raise ValueError(f"issue before any phase heading: {line}")
            issue = Issue(int(m.group(1)), m.group(2).strip(), phase.number)
            issues.append(issue)
            continue
        if issue is not None:
            issue.lines.append(line)
        elif phase is not None and line.strip() and not phase.intro:
            phase.intro = line.strip()
    return phases, issues


def gh(*args: str, capture: bool = True) -> str:
    result = subprocess.run(["gh", *args], check=True, capture_output=capture, text=True)
    return result.stdout if capture else ""


def existing_titles(kind: str) -> set[str]:
    if kind == "issue":
        out = gh("issue", "list", "--state", "all", "--limit", "500", "--json", "title")
        return {row["title"] for row in json.loads(out)}
    out = gh("api", "--paginate", "repos/{owner}/{repo}/milestones?state=all", "--jq", ".[].title")
    return set(out.split())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--apply", action="store_true", help="create labels, milestones, issues")
    parser.add_argument("--out", type=Path, help="dry run: write full issue bodies here")
    parser.add_argument("--backlog", type=Path, default=BACKLOG)
    args = parser.parse_args(argv)

    phases, issues = parse(args.backlog.read_text(encoding="utf-8"))
    numbers = [i.number for i in issues]
    if numbers != list(range(1, len(issues) + 1)):
        raise SystemExit(f"issue numbers are not 1..N in order: {numbers}")

    print(f"{len(phases)} phases, {len(issues)} issues\n")
    print("LABELS / MILESTONES")
    for p in phases.values():
        count = sum(1 for i in issues if i.phase == p.number)
        print(f"  {p.label:8s}  {p.milestone}  ({count} issues)")
    print("\nISSUES")
    for i in issues:
        print(f"  {i.gh_title}  [{phases[i.phase].label}]")

    if args.out:
        with args.out.open("w", encoding="utf-8") as fh:
            for i in issues:
                p = phases[i.phase]
                fh.write(f"==== {i.gh_title}\nlabel: {p.label}\nmilestone: {p.milestone}\n\n")
                fh.write(i.body(p) + "\n\n")
        print(f"\nfull bodies written to {args.out}")

    if not args.apply:
        print("\nDry run. Re-run with --apply to create these on GitHub.")
        return 0

    print("\nAPPLYING")
    for p in phases.values():
        gh(
            "label", "create", p.label, "--force",
            "--color", PHASE_COLORS[p.number % len(PHASE_COLORS)],
            "--description", p.milestone,
        )  # fmt: skip
        print(f"  label {p.label}")

    have_ms = existing_titles("milestone")
    for p in phases.values():
        if p.milestone in have_ms:
            print(f"  milestone exists: {p.milestone}")
            continue
        gh(
            "api", "repos/{owner}/{repo}/milestones",
            "-f", f"title={p.milestone}", "-f", f"description={p.intro}",
        )  # fmt: skip
        print(f"  milestone {p.milestone}")

    have_issues = existing_titles("issue")
    for i in issues:
        if i.gh_title in have_issues:
            print(f"  issue exists: {i.gh_title}")
            continue
        p = phases[i.phase]
        url = gh(
            "issue", "create",
            "--title", i.gh_title, "--body", i.body(p),
            "--label", p.label, "--milestone", p.milestone,
        ).strip()  # fmt: skip
        print(f"  {i.gh_title} -> {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
