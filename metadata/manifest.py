"""Checksum manifests: the project's data-versioning approach.

A manifest is a JSON Lines file with one record per data file:
``{"path": "<relative path>", "bytes": <size>, "sha256": "<hex digest>"}``.

Usage::

    python -m metadata.manifest build data/bom -o data/manifests/bom.jsonl
    python -m metadata.manifest verify data/bom data/manifests/bom.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Iterable
from pathlib import Path

CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_hidden(rel: Path) -> bool:
    return any(part.startswith(".") for part in rel.parts)


def build(root: Path, exclude: Iterable[Path] = ()) -> list[dict]:
    """Return one record per regular file under ``root``, sorted by relative path."""
    root = root.resolve()
    excluded = {p.resolve() for p in exclude}
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() in excluded:
            continue
        rel = path.relative_to(root)
        if _is_hidden(rel):
            continue
        records.append(
            {"path": rel.as_posix(), "bytes": path.stat().st_size, "sha256": sha256_of(path)}
        )
    return records


def write(records: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def verify(root: Path, records: list[dict]) -> list[str]:
    """Return a list of problems; empty means every record matches the files on disk."""
    problems = []
    for rec in records:
        path = root / rec["path"]
        if not path.is_file():
            problems.append(f"missing: {rec['path']}")
            continue
        size = path.stat().st_size
        if size != rec["bytes"]:
            problems.append(f"size changed: {rec['path']} ({rec['bytes']} -> {size})")
            continue
        if sha256_of(path) != rec["sha256"]:
            problems.append(f"checksum changed: {rec['path']}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="write a manifest for every file under ROOT")
    p_build.add_argument("root", type=Path)
    p_build.add_argument("-o", "--out", type=Path, required=True)

    p_verify = sub.add_parser("verify", help="check files under ROOT against MANIFEST")
    p_verify.add_argument("root", type=Path)
    p_verify.add_argument("manifest", type=Path)

    args = parser.parse_args(argv)
    if args.command == "build":
        records = build(args.root, exclude=[args.out])
        write(records, args.out)
        print(f"wrote {len(records)} records to {args.out}")
        return 0

    problems = verify(args.root, read(args.manifest))
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{'FAIL' if problems else 'OK'}: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
