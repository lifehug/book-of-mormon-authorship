#!/usr/bin/env python3
"""Assemble the paper (BOM-36) into one file: front matter, methods, validation and borrowing
results, blind results, limitations, discussion. The simulated review (BOM-38) reads exactly this
file. Usage: ``python scripts/build_paper.py`` -> ``paper/paper.md``."""

from pathlib import Path

D = Path("paper/draft")
PARTS = [
    ("", "00_front.md"),
    ("# Part I. Data and methods", "methods.md"),
    ("# Part II. Validation, borrowing and dating checks", "results_so_far.md"),
    ("# Part III. The blind run", "20_blind_results.md"),
    ("# Part IV. Limitations", "limitations.md"),
    ("", "90_discussion.md"),
]


def main() -> int:
    out = []
    for head, name in PARTS:
        text = (D / name).read_text()
        if head:  # each draft's own title becomes a section under the part heading
            lines = text.splitlines()
            if lines and lines[0].startswith("# "):
                lines = lines[1:]
            text = head + "\n" + "\n".join(lines)
        out.append(text.strip() + "\n")
    dest = Path("paper/paper.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n\n".join(out))
    print(f"-> {dest}: {len(dest.read_text().split()):,} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
