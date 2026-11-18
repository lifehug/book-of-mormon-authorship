"""Where lab code may write. Everything else in the repository is read-only to the lab.

The study's results (``data/blind``, ``data/sweep``, ``data/benchmark`` ...), its config and its
paper are never written by lab code: every write goes through ``out``, which refuses a path
outside these roots, and ``tests/test_lab.py`` fails the build if a lab module writes another way.
"""

from __future__ import annotations

from pathlib import Path

REGISTRY = Path("data/lab")  # public: the registry (flags and ids, no text)
FAST = Path("data/corpus/lab")  # local disk: the fast passage index (derived, rebuildable)
NOTES = Path("data/private/lab")  # private repository: notes and outputs that may quote text
LOGS = Path("logs/lab")  # local, untracked: the query log
DOCS = Path("docs/lab")  # public: the generated data map
ROOTS = (REGISTRY, FAST, NOTES, LOGS, DOCS)


def out(path: str | Path) -> Path:
    """``path`` if it lies under a lab root (its folder is made); otherwise ``PermissionError``."""
    p = Path(path)
    full = p.resolve()
    for root in ROOTS:
        if full.is_relative_to(root.resolve()):
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
    raise PermissionError(f"the lab may not write {p}: outside {[str(r) for r in ROOTS]}")
