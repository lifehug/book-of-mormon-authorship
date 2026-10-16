"""The analytic configuration: one versioned file every stage reads its choices from (BOM-40).

No module may hard-code an analytic value. Load the config, take the value, and stamp the
config's SHA-256 onto whatever the stage writes, so any output can be traced to the choices
that produced it::

    from metadata.config import load, sha256_of_config

    cfg = load()
    cutoff = cfg["corpus"]["ocr_max_cer"]
    stamp = sha256_of_config()

``load`` refuses a config whose registered values do not match the pre-registration, so a
silent edit to a pinned number fails loudly instead of quietly changing the study.

Usage::

    python -m metadata.config show
    python -m metadata.config hash
    python -m metadata.config pending
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "preregistered.yaml"

# Values fixed in paper/preregistration.md, by section. A config that disagrees with any of
# these is rejected: changing a registered choice takes a dated OSF amendment, not an edit.
PINNED: dict[tuple[str, ...], Any] = {
    ("corpus", "date_range"): [1780, 1830],
    ("corpus", "ocr_max_cer"): 0.10,  # 4.3
    ("corpus", "dedup", "threshold"): 0.8,  # 4.3
    ("corpus", "dedup", "shingle"): 5,  # 4.3
    ("corpus", "dedup", "keep"): "earliest",  # 4.3
    ("sealing", "contamination_min_tokens"): 12,  # 4.2
    ("kjv_mask", "verbatim", "min_identity"): 0.90,  # 4.4
    ("kjv_mask", "verbatim", "min_tokens"): 8,  # 4.4
    ("kjv_mask", "paraphrase", "min_identity"): 0.60,  # 4.4
    ("kjv_mask", "paraphrase", "max_identity"): 0.90,  # 4.4
    ("kjv_mask", "paraphrase", "min_tokens"): 8,  # 4.4
    ("segmentation", "chunk_words"): [2000, 5000],  # 4.5
    ("segmentation", "split", "stratify_by"): "narrator",  # 4.5
}


class ConfigError(RuntimeError):
    """The config is missing, malformed, or disagrees with the pre-registration."""


def _dig(cfg: dict, path: tuple[str, ...]) -> Any:
    node: Any = cfg
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise ConfigError(f"missing required key: {'.'.join(path)}")
        node = node[key]
    return node


def validate(cfg: dict) -> None:
    """Raise ``ConfigError`` unless every pre-registered value is present and unchanged."""
    for path, expected in PINNED.items():
        found = _dig(cfg, path)
        if found != expected:
            raise ConfigError(
                f"{'.'.join(path)} is {found!r}, but the pre-registration fixes it at "
                f"{expected!r}. Changing a registered choice takes a dated OSF amendment."
            )


def load(path: Path | None = None) -> dict:
    """Load and validate the config. Defaults to ``config/preregistered.yaml``."""
    path = path or DEFAULT_CONFIG
    if not path.exists():
        raise ConfigError(f"no config at {path}")
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path} does not contain a mapping")
    validate(cfg)
    return cfg


def sha256_of_config(path: Path | None = None) -> str:
    """The config's SHA-256, for stamping onto every output a stage writes."""
    path = path or DEFAULT_CONFIG
    if not path.exists():
        raise ConfigError(f"no config at {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pending(cfg: dict | None = None) -> list[dict]:
    """Choices this file does not fix yet; each needs a dated amendment before BOM-21."""
    cfg = cfg if cfg is not None else load()
    return list(cfg.get("pending_amendment") or [])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "command", choices=("show", "hash", "pending", "validate"), help="what to print"
    )
    parser.add_argument("-c", "--config", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        if args.command == "hash":
            print(sha256_of_config(args.config))
            return 0
        cfg = load(args.config)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.command == "show":
        print(json.dumps(cfg, indent=2, sort_keys=True))
    elif args.command == "pending":
        rows = pending(cfg)
        for row in rows:
            print(f"{row['key']:<40} {row['issue']:<10} {row['note']}")
        print(f"\n{len(rows)} choice(s) awaiting a dated amendment before BOM-21.")
    else:
        print(f"ok: {len(PINNED)} pre-registered values match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
