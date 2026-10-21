"""No pipeline stage may delete its own source data.

This exists because the rule was already written down and still got broken. `CLAUDE.md` says
"keep originals and intermediate artifacts, and flag rather than delete", and the owner had said
the same in plainer words. The Chronicling America bulk extractor nonetheless matched only
`ocr.txt`, treated every `ocr.xml` as skipped, and then deleted the tarball it had just read --
by default, with no flag needed. That discarded the ALTO for 158,960 pages: per-word confidence,
per-character confidence and word coordinates, which is a direct OCR-quality measurement for the
whole corpus and the only route to column-aware reading order. There were no backups and no
snapshots. Recovery means re-downloading 76 archives by hand through Cloudflare.

A comment is not a guard. These tests fail the build if a destructive call reappears anywhere in
the ingest or processing packages outside the two patterns that are genuinely safe:

  * ``tmp.replace(final)`` -- atomic write, where the temp file is this process's own output
  * a call guarded by an explicitly opt-in flag that defaults to off

If a new stage legitimately needs to delete something, add it to ``ALLOWED`` with a reason, so
the decision is visible in a diff rather than buried in a function.
"""

from __future__ import annotations

import ast
import pathlib

PACKAGES = ("ingest", "metadata", "ocr_fix", "kjv_mask", "segment", "classic")
DESTRUCTIVE = {"unlink", "rmtree", "remove", "rmdir", "removedirs"}

# path -> why this one is safe. Keep the reason; it is the point of the allowlist.
ALLOWED: dict[str, str] = {
    "ingest/chronicling_america.py": (
        "guarded by --discard-tarball, which defaults to False. It used to be the default and "
        "that is what cost the project the ALTO for 158,960 pages."
    ),
}

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _destructive_calls(path: pathlib.Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in DESTRUCTIVE:
                hits.append(node.lineno)
    return hits


def test_no_unreviewed_deletion_in_the_pipeline():
    offenders = {}
    for pkg in PACKAGES:
        for path in (ROOT / pkg).rglob("*.py") if (ROOT / pkg).is_dir() else []:
            rel = str(path.relative_to(ROOT))
            lines = _destructive_calls(path)
            if lines and rel not in ALLOWED:
                offenders[rel] = lines
    assert not offenders, (
        f"destructive calls outside the allowlist: {offenders}. A pipeline stage must not "
        f"delete its source data. If this is genuinely safe, add it to ALLOWED in "
        f"tests/test_no_source_deletion.py with a reason, so the decision shows up in a diff."
    )


def test_chronam_keeps_both_ocr_members():
    """The extractor must take ocr.xml as well as ocr.txt."""
    from ingest.chronicling_america import member_ext, member_key

    base = "sn87062070/1830/03/31/ed-1/seq-1"
    assert member_key(f"{base}/ocr.txt") is not None
    assert member_key(f"{base}/ocr.xml") is not None, "ALTO must not be skipped again"
    assert member_ext(f"{base}/ocr.txt") == "txt"
    assert member_ext(f"{base}/ocr.xml") == "xml"
    assert member_key(f"{base}/something_else.jp2") is None


def test_chronam_keeps_the_tarball_by_default():
    """Deleting the original is opt-in. It was the default once; it must never be again."""
    import inspect

    from ingest.chronicling_america import bulk

    discard = inspect.signature(bulk).parameters["discard"]
    assert discard.default is False, "the source archive must survive unless explicitly discarded"


def test_alto_and_text_go_to_separate_directories():
    from ingest.chronicling_america import page_path

    row = {"lccn": "sn87062070", "date": "1830-03-31", "edition": 1, "sequence": 1}
    assert page_path(row, "txt").parts[-3] == "text"
    assert page_path(row, "xml").parts[-3] == "alto"
