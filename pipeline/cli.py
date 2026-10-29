"""One entry point for the pipeline, and the multiverse runner (BOM-40).

``bom run`` runs the analysis stages under one config and writes every output, stamped, to
``results/<config-hash>/``; the registered config gives the official result. ``bom multiverse``
forms alternate configs from the ranges in ``config/multiverse.yaml``, runs the same stages under
each (loaded non-strict, so their outputs say ``registered: false``), and draws a specification
curve: for every conclusion, the share of configurations that agree with it.

Stages are registered in ``STAGES`` with their recompute tier (``config/tiers.yaml``). Only
feature-tier stages exist so far; the benchmark (BOM-21) joins them, and the curve is redrawn on
it.

Usage::

    uv run bom run [--config config/preregistered.yaml] [--out results/<hash>/]
    uv run bom multiverse [--max-configs N]
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import random
import sys
from collections.abc import Callable
from pathlib import Path

import yaml

from metadata.config import DEFAULT_CONFIG, derive_seed, load, sha256_of_config, stamp

RESULTS = Path("results")
MULTIVERSE = Path("config/multiverse.yaml")


def _classic_corpus_run(out_dir: Path) -> Path:
    from classic.corpus_run import run

    out = out_dir / "classic_corpus_run.json"
    run(out)
    return out


# name -> (tier, function writing its output under the given directory, returning the path)
STAGES: dict[str, tuple[str, Callable[[Path], Path]]] = {
    "classic_corpus_run": ("feature", _classic_corpus_run),
}


def _with_config(path: Path, strict: bool):
    """Point every ``metadata.config`` reader at ``path`` for the duration."""

    class _Ctx:
        def __enter__(self):
            self.saved = {k: os.environ.get(k) for k in ("BOM_CONFIG", "BOM_CONFIG_STRICT")}
            os.environ["BOM_CONFIG"] = str(path.resolve())
            os.environ["BOM_CONFIG_STRICT"] = "1" if strict else "0"

        def __exit__(self, *exc):
            for k, v in self.saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    return _Ctx()


def run(config: Path, out: Path | None, stages: list[str], strict: bool = True) -> Path:
    with _with_config(config, strict):
        out = out or RESULTS / sha256_of_config()[:16]
        out.mkdir(parents=True, exist_ok=True)
        written = {name: str(STAGES[name][1](out)) for name in stages}
        (out / "stamp.json").write_text(json.dumps({**stamp(), "stages": written}, indent=1) + "\n")
    print(f"-> {out}")
    return out


def _set(cfg: dict, dotted: str, value) -> None:
    node = cfg
    *head, last = dotted.split(".")
    for k in head:
        node = node[k]
    if last not in node:
        raise KeyError(f"{dotted} is not in the config")
    node[last] = value


def configurations(spec: dict, base: dict, max_configs: int) -> list[dict]:
    """Every combination of the ranges (the registered values among them), or a seeded sample."""
    keys = sorted(spec["ranges"])
    combos = list(itertools.product(*(spec["ranges"][k] for k in keys)))
    if len(combos) > max_configs:
        rng = random.Random(derive_seed("multiverse", base))
        combos = rng.sample(combos, max_configs)
    out = []
    for combo in combos:
        cfg = copy.deepcopy(base)
        for k, v in zip(keys, combo, strict=True):
            _set(cfg, k, v)
        out.append({"choices": dict(zip(keys, combo, strict=True)), "config": cfg})
    return out


def conclusions(result: dict) -> dict[str, bool]:
    """The yes/no findings a stage reports, flattened to ``test:finding``."""
    return {
        f"{t}:{k}": bool(v) for t, d in result.get("per_test", {}).items() for k, v in d.items()
    }


def multiverse(max_configs: int | None, opt_in: bool) -> int:
    spec = yaml.safe_load(MULTIVERSE.read_text())
    if opt_in:
        spec["ranges"].update(spec.get("opt_in") or {})
    base = load(DEFAULT_CONFIG)
    configs = configurations(spec, base, max_configs or spec["max_configs"])
    root = RESULTS / "multiverse"
    root.mkdir(parents=True, exist_ok=True)
    official = run(DEFAULT_CONFIG, None, spec["stages"])
    runs = []
    for i, c in enumerate(configs, 1):
        path = root / f"config_{i:03d}.yaml"
        path.write_text(yaml.safe_dump(c["config"], sort_keys=False))
        out = run(path, root / f"run_{i:03d}", spec["stages"], strict=False)
        runs.append({"choices": c["choices"], "out": str(out)})
    curve = specification_curve(official, runs, spec["stages"])
    (root / "curve.json").write_text(json.dumps(curve, indent=1) + "\n")
    (root / "curve.svg").write_text(curve_svg(curve))
    print(
        f"{len(runs)} configurations; agreement with the registered result: "
        f"median {curve['median_agreement']:.0%}, lowest {curve['lowest_agreement']:.0%}"
    )
    return 0


def _load_results(out: Path, stages: list[str]) -> dict:
    return {s: json.loads((out / f"{s}.json").read_text()) for s in stages}


def specification_curve(official: Path, runs: list[dict], stages: list[str]) -> dict:
    """Per conclusion of the registered run, the share of configurations that reach the same."""
    reg = {}
    for res in _load_results(official, stages).values():
        reg.update(conclusions(res))
    per_run = []
    for r in runs:
        got = {}
        for res in _load_results(Path(r["out"]), stages).values():
            got.update(conclusions(res))
        per_run.append(
            {
                "choices": r["choices"],
                "conclusions": got,
                "share_true": sum(got.values()) / max(1, len(got)),
            }
        )
    agree = {
        k: sum(r["conclusions"].get(k) == v for r in per_run) / max(1, len(per_run))
        for k, v in reg.items()
    }
    vals = sorted(agree.values())
    per_run.sort(key=lambda r: r["share_true"])
    return {
        "registered": str(official),
        "configurations": len(per_run),
        "median_agreement": vals[len(vals) // 2] if vals else None,
        "lowest_agreement": vals[0] if vals else None,
        "agreement": agree,
        "runs": per_run,
    }


def curve_svg(curve: dict, width: int = 720, height: int = 360) -> str:
    """The specification curve: each configuration's share of positive findings, sorted, with a
    panel below marking the choices each configuration made. Plain SVG, no plotting library."""
    runs = curve["runs"]
    n = max(1, len(runs))
    keys = sorted({k for r in runs for k in r["choices"]})
    top_h, row_h, pad = 200, 18, 40
    h = top_h + pad + row_h * sum(len({str(r["choices"][k]) for r in runs}) for k in keys) + pad
    x = lambda i: pad + 160 + (width - pad - 180) * (i + 0.5) / n  # noqa: E731
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{max(height, h)}" '
        'font-family="sans-serif" font-size="11">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{pad}" y="20">Share of findings positive, per configuration (sorted)</text>',
    ]
    for i, r in enumerate(runs):
        y = 30 + (top_h - 40) * (1 - r["share_true"])
        parts.append(f'<circle cx="{x(i):.1f}" cy="{y:.1f}" r="3" fill="#33a"/>')
    for frac in (0, 0.5, 1):
        y = 30 + (top_h - 40) * (1 - frac)
        parts.append(f'<text x="{pad + 120}" y="{y + 4:.0f}">{frac:.0%}</text>')
    y = top_h + pad
    for k in keys:
        for v in sorted({str(r["choices"][k]) for r in runs}):
            parts.append(f'<text x="{pad}" y="{y + 4}">{k.split(".")[-1]} = {v}</text>')
            for i, r in enumerate(runs):
                if str(r["choices"][k]) == v:
                    parts.append(
                        f'<rect x="{x(i) - 2:.1f}" y="{y - 4}" width="4" height="8" fill="#555"/>'
                    )
            y += row_h
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="bom", description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    r.add_argument("--out", type=Path)
    r.add_argument("--stage", action="append", choices=sorted(STAGES))
    r.add_argument("--not-strict", action="store_true", help="allow a non-registered config")
    m = sub.add_parser("multiverse")
    m.add_argument("--max-configs", type=int)
    m.add_argument("--opt-in", action="store_true", help="include corpus/model-tier ranges")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(a.config, a.out, a.stage or sorted(STAGES), strict=not a.not_strict)
        return 0
    return multiverse(a.max_configs, a.opt_in)


if __name__ == "__main__":
    sys.exit(main())
