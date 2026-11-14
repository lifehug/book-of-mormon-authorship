#!/usr/bin/env python3
"""Assemble ``paper/paper.md`` from the section files in ``paper/draft/v3/`` (title and abstract
``sec00.md``, sections ``sec01.md`` to ``sec14.md``, ``appendix.md``). Edit the section files,
not ``paper/paper.md``.

Usage::

    python scripts/assemble_paper.py
"""

from pathlib import Path

D = Path(__file__).resolve().parents[1] / "paper/draft/v3"
parts = [D / f"sec{n:02d}.md" for n in range(15)] + [D / "appendix.md"]
text = "\n\n".join(p.read_text().strip() for p in parts) + "\n"
(D.parents[1] / "paper.md").write_text(text)
print(f"{len(text.split()):,} words -> paper/paper.md")
