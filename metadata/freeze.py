"""Freeze corpus v1.0: one index naming every byte later stages run against (BOM-19).

The corpus is already described file by file in ``data/manifests/``; freezing adds a single
record that pins them together. ``data/manifests/corpus_<version>.json`` lists every manifest
and every derived table the analysis stages read -- catalog, genre labels, dedup, OCR flags,
spelling map, KJV masks, Book of Mormon segments and split, candidate units and control lists
-- each with its SHA-256 and size, plus the config hash and the git commit it was made at. A
later stage cites the version; a replicator checks the index, then each manifest against their
own copies of the sources.

It refuses to freeze with any listed file missing, with uncommitted changes to a listed file,
or before the control masks exist. Publishing the frozen set (Zenodo, BOM-19's DOI) is the
owner's step and is not done here.

Usage::

    python -m metadata.freeze v1.0          # -> data/manifests/corpus_v1.0.json
    python -m metadata.freeze v1.0 --check  # verify the files still match the index
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from metadata.config import sha256_of_config

MANIFESTS = Path("data/manifests")
# derived data the analysis stages read; globs relative to the repository root
FROZEN = [
    "data/catalog/catalog.parquet",
    "data/catalog/genre.parquet",
    "data/catalog/genre_pass2.parquet",
    "data/catalog/duplicates.parquet",
    "data/catalog/duplicates_normalized.parquet",
    "data/catalog/author_words.parquet",
    "data/catalog/author_words_normalized.parquet",
    "data/catalog/sealed.json",
    "data/catalog/validation_index.json",
    "data/ocr_quality/volumes.parquet",
    "data/ocr_quality/cleaning.parquet",
    "data/ocr_quality/groundtruth.parquet",
    "data/ocr_quality/calibration.json",
    "data/normalization/normalization.parquet",
    "data/normalization/applied_map.tsv",
    "data/kjv_mask/bom/spans.jsonl",
    "data/kjv_mask/candidates/spans.jsonl",
    "data/kjv_mask/controls/spans.jsonl.gz",
    "data/kjv_mask/*/report.json",
    "data/kjv_mask/validation_200.jsonl",
    "data/bom/segments/*.json",
    "data/bom/segments/*.jsonl",
    "data/candidates/units.csv",
    "data/candidates/signed_items.json",
    "data/candidates/word_counts.json",
    "data/controls/*.txt",
    "data/controls/*.jsonl",
    "data/controls/controls.json",
    "config/preregistered.yaml",
]
REQUIRED = ["data/kjv_mask/controls/report.json"]  # written only when a masking run completes


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files(root: Path = Path(".")) -> list[Path]:
    out: set[Path] = set()
    for pattern in FROZEN:
        hits = sorted(root.glob(pattern))
        if not hits:
            raise SystemExit(f"nothing matches {pattern}")
        out.update(hits)
    out.update(p for p in (root / MANIFESTS).glob("*.jsonl"))
    return sorted(out)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def index(version: str, root: Path = Path(".")) -> dict:
    return {
        "version": version,
        "config_sha256": sha256_of_config(),
        "files": {
            str(p.relative_to(root)): {"sha256": _sha(p), "bytes": p.stat().st_size}
            for p in files(root)
        },
    }


def freeze(version: str) -> int:
    missing = [p for p in REQUIRED if not Path(p).exists()]
    if missing:
        raise SystemExit(f"not ready to freeze: {missing} missing")
    listed = [str(p) for p in files()]
    dirty = _git("status", "--porcelain", "--", *listed).strip()
    if dirty:
        raise SystemExit(f"uncommitted changes to frozen files:\n{dirty}")
    rec = index(version)
    rec["git_commit"] = _git("rev-parse", "HEAD").strip()
    out = MANIFESTS / f"corpus_{version}.json"
    out.write_text(json.dumps(rec, indent=1) + "\n")
    total = sum(f["bytes"] for f in rec["files"].values())
    print(f"froze {len(rec['files'])} files ({total / 1e9:.2f} GB) at {rec['git_commit'][:10]}")
    print(f"-> {out}  sha256 {_sha(out)}")
    return 0


def check(version: str) -> int:
    rec = json.loads((MANIFESTS / f"corpus_{version}.json").read_text())
    bad = [
        p for p, f in rec["files"].items() if not Path(p).exists() or _sha(Path(p)) != f["sha256"]
    ]
    print(f"{len(rec['files']) - len(bad)} of {len(rec['files'])} files match corpus {version}")
    for p in bad:
        print(f"  changed or missing: {p}")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("version")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return check(a.version) if a.check else freeze(a.version)


if __name__ == "__main__":
    sys.exit(main())
