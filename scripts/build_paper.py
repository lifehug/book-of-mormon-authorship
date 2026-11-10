#!/usr/bin/env python3
"""Assemble the paper (BOM-36) into one file, in the order of ``paper/outline.md`` (sections 1-13),
then the detailed methods and tables as appendices; superseded drafts are kept in
``paper/draft/v1/``. The simulated review (BOM-38) reads exactly this
file. Usage: ``python scripts/build_paper.py`` -> ``paper/paper.md``."""

from pathlib import Path

D = Path("paper/draft")
PARTS = [
    ("", "00_front.md"),
    ("", "02_scale.md"),
    ("", "03_prior.md"),
    ("", "04_measuring.md"),
    ("", "05_tests.md"),
    ("", "06_ces.md"),
    ("", "07_corrections.md"),
    ("", "08_claims.md"),
    ("", "09_held.md"),
    ("", "10_people.md"),
    ("", "11_limitations.md"),
    ("", "12_public.md"),
    ("", "13_next.md"),
    ("## Appendix A. Methods in detail", "methods.md"),
    ("## Appendix B. Detailed tables", "results_so_far.md"),
    ("## Appendix C. References", "references.md"),
]


def main() -> int:
    out = []
    for head, name in PARTS:
        text = (D / name).read_text()
        if head:  # each draft's own title becomes a section under the part heading
            lines = text.splitlines()
            if lines and lines[0].startswith("# "):
                lines = lines[1:]
            body = "\n".join("#" + ln if ln.startswith("#") else ln for ln in lines)
            text = head + "\n" + body  # the draft's sections nest under the part heading
        out.append(text.strip() + "\n")
    dest = Path("paper/paper.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n\n".join(out))
    print(f"-> {dest}: {len(dest.read_text().split()):,} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
