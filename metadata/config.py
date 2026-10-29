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

**Which config.** ``config/preregistered.yaml`` unless ``BOM_CONFIG`` names another file, so any
stage can be rerun under an alternate config without code changes (``pipeline.run``). An
alternate that departs from a registered value loads only with ``BOM_CONFIG_STRICT=0``, which
the multiverse runner sets; ``stamp()`` then records ``registered: false`` on every output.

**Seeds.** One root seed (``seed``, Amendment 2). Every component derives its own from it by
name -- ``random.Random(f"{root}:{name}")``, or ``derive_seed(name)`` where an integer is needed
-- so no component seed is chosen separately. ``segmentation.split.seed`` equals the root and is
pinned on its own because 4.5 names it.

Usage::

    python -m metadata.config show
    python -m metadata.config hash
    python -m metadata.config pending
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "preregistered.yaml"

# Values fixed in paper/preregistration.md, by section, and by its dated amendments. A config
# that disagrees with any of these is rejected: changing a registered choice takes a dated OSF
# amendment, not an edit.
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
    # Registered by Amendment 2, 2026-10-17 (OSF revision 6ad3f82fc8f5176e336b2561).
    ("corpus", "language_filter", "min_probability"): 0.90,
    ("corpus", "spelling_normalization", "pre_1700"): "morphadorner_emod_lexicon",
    ("corpus", "spelling_normalization", "post_1780"): "artifacts_only",
    ("kjv_mask", "edition"): "kjv_1769_oxford_blayney",
    ("kjv_mask", "passim", "ngram"): 5,  # Amendment 2
    ("kjv_mask", "passim", "max_gap_chars"): 100,  # Amendment 2
    ("kjv_mask", "passim", "relative_overlap"): 0.5,  # Amendment 2
    ("segmentation", "split", "seed"): 20261017,
    ("seed",): 20261017,
    # Registered by Amendment 3, 2026-10-20 (OSF revision 6ad802954d710c8c6b00b651).
    ("corpus", "genre_tagging", "max_labels"): 2,
    ("corpus", "genre_tagging", "allow_uncertain"): True,
    ("corpus", "genre_tagging", "passes"): 2,
    ("corpus", "genre_tagging", "validation_sample"): 300,
    ("corpus", "genre_tagging", "validation_sampling"): "stratified",
    # Registered by Amendment 4, 2026-10-20 (OSF revision 6ad844dc2aba3079ce0da955).
    ("corpus", "genre_tagging", "reliability_sample"): 5000,
    ("corpus", "genre_tagging", "reliability_strata"): ["category", "source", "decade"],
    ("corpus", "genre_tagging", "pass2_model_family"): "distinct_from_pass1",
    ("corpus", "genre_tagging", "perturbation_runs"): 100,
    ("corpus", "genre_tagging", "perturbation_rate"): "from_validation",
    ("corpus", "genre_tagging", "perturbation_confusion"): "observed",
    # Registered by Amendment 5, 2026-10-21 (OSF revision 6ad8cc455301b781d55b34dc).
    ("candidates", "expanded_corpora", "role"): "secondary",
    ("candidates", "expanded_corpora", "exposed_rule"): (
        "non_match_is_evidence_match_is_uninformative"
    ),
    ("candidates", "expanded_corpora", "provenance_admitted"): [
        "holograph",
        "dictated_to_scribe",
    ],
    ("candidates", "expanded_corpora", "gate"): "time_split_validation_at_section_7_floor",
    ("candidates", "expanded_corpora", "sweep_lead_expansions_max"): 10,
    ("candidates", "expanded_corpora", "publish_test_counts"): True,
    # Registered by Amendment 6, 2026-10-27 (OSF revision 6ae16f4142a77759f3e18539).
    ("corpus", "dedup", "metadata_pass", "keys"): ["title_norm", "author_norm", "year"],
    ("corpus", "dedup", "metadata_pass", "across_sources"): True,
    ("corpus", "dedup", "metadata_pass", "keep"): "earliest",
    ("corpus", "ocr_cleaning", "lexicon_min_docs"): 2,
    ("corpus", "ocr_cleaning", "long_s_ratio"): 100,
    ("corpus", "ocr_cleaning", "edge_lines"): 2,
    ("corpus", "ocr_cleaning", "header_min_letters"): 6,
    ("corpus", "ocr_cleaning", "header_min_pages"): 3,
    ("corpus", "ocr_cleaning", "header_min_share"): 0.05,
    ("corpus", "ocr_cleaning", "short_line"): 60,
    ("corpus", "ocr_cleaning", "chars_per_page"): 2000,
    ("corpus", "ocr_cleaning", "defragment_fragment_share"): 0.3,
    ("corpus", "ocr_cleaning", "defragment_fragment_len"): 2,
    ("corpus", "ocr_cleaning", "defragment_max_word"): 20,
    ("corpus", "ocr_cleaning", "defragment_unknown_per_letter"): 12,
    ("corpus", "ocr_cleaning", "llm_correction"): False,
    ("corpus", "genre_tagging", "pass2_model"): "claude_sonnet",
    ("corpus", "genre_tagging", "perturbation_rate_bound"): {
        "model_decided": 0.28,
        "rule_decided": 0.03,
    },
    ("corpus", "spelling_normalization", "range_1700_1779"): "artifacts_only",
    ("corpus", "spelling_normalization", "morphadorner"): "adorner_as_distributed",
    ("corpus", "spelling_normalization", "morphadorner_keep_printed"): ["an", "whether", "fall"],
    ("sealing", "contamination_excludes_kjv"): True,
    ("sealing", "contamination_min_shared"): 20,
    ("kjv_mask", "passim", "passim_min_align_chars"): 20,
    ("kjv_mask", "passim", "max_df"): 100,
    ("kjv_mask", "passim", "batch_words"): 720000,
    ("kjv_mask", "passim", "piece_words"): 150000,
    ("kjv_mask", "passim", "piece_overlap"): 500,
    ("kjv_mask", "passim", "split_parts"): 3,
    ("kjv_mask", "passim", "split_depth"): 2,
    ("controls", "pool_sample"): {"history": 3000, "general_prose": 5000},
    ("controls", "pseudo_biblical"): "curated",
    # 5.1 and Amendment 2: classical stylometry
    ("classic", "mfw"): [100, 300, 1000],
    ("classic", "mfw_min_doc_fraction"): 0.20,
    ("classic", "char_ngrams"): [3, 4],
    ("classic", "pos_ngrams"): [2, 3],
    ("classic", "imposters", "trials"): 100,
    ("classic", "imposters", "feature_fraction"): 0.5,
    ("classic", "imposters", "imposter_fraction"): 0.5,
    ("classic", "imposters", "per_trial"): 100,
    ("classic", "imposters", "distance"): "cosine_delta",
    ("classic", "ensc", "shrinkage_grid"): [0, 0.5, 1, 2, 4, 8],
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


def active_path() -> Path:
    """The config in force: ``BOM_CONFIG`` if set, else the registered one."""
    env = os.environ.get("BOM_CONFIG")
    return Path(env) if env else DEFAULT_CONFIG


def _strict() -> bool:
    return os.environ.get("BOM_CONFIG_STRICT", "1") != "0"


def load(path: Path | None = None, strict: bool | None = None) -> dict:
    """Load the config and, unless ``strict`` is false, validate it against the registration."""
    path = path or active_path()
    if not path.exists():
        raise ConfigError(f"no config at {path}")
    with path.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path} does not contain a mapping")
    if _strict() if strict is None else strict:
        validate(cfg)
    return cfg


def is_registered(cfg: dict) -> bool:
    try:
        validate(cfg)
    except ConfigError:
        return False
    return True


def sha256_of_config(path: Path | None = None) -> str:
    """The config's SHA-256, for stamping onto every output a stage writes."""
    path = path or active_path()
    if not path.exists():
        raise ConfigError(f"no config at {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        return None


def stamp() -> dict:
    """What every output records about how it was made."""
    cfg = load(strict=False)
    return {"config_sha256": sha256_of_config(), "config_path": str(active_path()),
            "registered": is_registered(cfg), "git_commit": git_commit()}  # fmt: skip


def derive_seed(name: str, cfg: dict | None = None) -> int:
    """A component's integer seed, derived from the root seed by name."""
    root = (cfg or load(strict=False))["seed"]
    return int.from_bytes(hashlib.sha256(f"{root}:{name}".encode()).digest()[:4], "big")


def classic_kwargs(cfg: dict | None = None) -> dict:
    """The registered settings of the classical methods, ready to pass (5.1, Amendment 2)."""
    c = (cfg or load(strict=False))["classic"]
    gi, en = c["imposters"], c["ensc"]
    distance = {"cosine_delta": "cosine", "burrows_delta": "delta"}[gi["distance"]]
    return {
        "imposters": {"trials": gi["trials"], "feature_fraction": gi["feature_fraction"],
                      "distance": distance},
        # pending_amendment classic.ensc.alpha: the registered value once pinned
        "ensc": {"alpha": en.get("alpha", en["alpha_provisional"]),
                 "priors": en.get("priors", en["priors_provisional"])},
        "mfw_min_doc_fraction": c["mfw_min_doc_fraction"],
    }  # fmt: skip


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
