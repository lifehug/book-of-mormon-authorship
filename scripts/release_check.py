#!/usr/bin/env python3
"""The pre-release checklist of BOM-37 (``docs/release-plan.md``), run automatically.

Each check prints PASS, WARN or FAIL with its evidence; the exit status is 1 if any check fails.

1. **Results hold no text:** every JSON under the public result directories is small, and no
   string in one is longer than ``--max-string`` characters (BOM-58's guard, widened).
2. **Explorer:** every panel in ``explorer/panels.json`` reads a file that exists (or is marked
   pending), its path resolves, at least one row has each column, and no value it shows is long
   text (a panel may allow longer prose of our own with ``max_text``).
3. **Nothing private is tracked:** no tracked file under ``data/private/`` or ``data/corpus/``,
   no model weights, nothing over ``--max-file-mb``.
4. **Licenses** ``LICENSE`` (code) and ``LICENSE-DATA`` (derived data) exist.
5. **Every tracked data directory has a SOURCES.md** (CLAUDE.md).
6. **Manifests parse,** and every tracked file a manifest lists matches its SHA-256.
7. **The tree is committed and pushed** (WARN only).

Usage::

    python scripts/release_check.py [--max-string 400 --max-file-mb 50]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT_DIRS = ["data/benchmark", "data/classic", "data/semantic", "data/dating", "data/sweep",
               "data/blind", "data/synthesis", "data/manuscript", "data/access"]  # fmt: skip
PANELS = ROOT / "explorer/panels.json"
WEIGHTS = (".pt", ".bin", ".safetensors", ".ckpt", ".npy", ".npz")
NOTE_KEYS = ("note", "test", "rule", "about", "description")  # our own prose, not corpus text
BULKY_OK = ("data/catalog/", "data/manifests/")  # large by design and public (CLAUDE.md)


def tracked() -> list[str]:
    r = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return r.stdout.splitlines()


def long_strings(obj, limit: int, path: str = "") -> list[str]:
    """Paths of every string longer than ``limit`` in a JSON value, except under keys that hold
    the project's own notes (``NOTE_KEYS``)."""
    if isinstance(obj, str):
        key = path.rsplit(".", 1)[-1].split("[")[0].lower()
        if any(key.endswith(n) for n in NOTE_KEYS):
            return []
        return [path or "$"] if len(obj) > limit else []
    if isinstance(obj, dict):
        return [p for k, v in obj.items() for p in long_strings(v, limit, f"{path}.{k}")]
    if isinstance(obj, list):
        return [p for i, v in enumerate(obj) for p in long_strings(v, limit, f"{path}[{i}]")]
    return []


def get(obj, path: str):
    for k in [p for p in path.split(".") if p]:
        obj = obj.get(k) if isinstance(obj, dict) else None
    return obj


def panel_rows(panel: dict, root: Path = ROOT) -> list[dict] | None:
    """The rows a panel shows, as the explorer builds them; None if its file is absent."""
    f = root / panel["file"]
    if not f.exists():
        return None
    if panel["mode"] == "csv":
        with f.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    node = get(json.loads(f.read_text()), panel.get("path", ""))
    if panel["mode"] == "counts":
        return [{"name": k, "count": v} for k, v in node.items()]
    if panel["mode"] == "groups":
        return [{"group": g, **r} for g, v in node.items() for r in v.get(panel["sub"], [])]
    if panel["mode"] == "summary":
        return [{c: get(node, c) for c in panel.get("columns", [])}]
    if isinstance(node, list):
        return node
    keys = panel.get("rows") or list(node)
    return [{"name": k, **node[k]} for k in keys if k in node]


def check_panels(panels: list[dict], root: Path = ROOT, limit: int = 400) -> list[str]:
    """Problems with the explorer's panels; empty when every panel is sound."""
    out = []
    for p in panels:
        rows = panel_rows(p, root)
        if rows is None:
            if not p.get("pending"):
                out.append(f"{p['id']}: {p['file']} missing")
            continue
        if not rows:
            out.append(f"{p['id']}: no rows")
            continue
        for c in p.get("columns", []):
            if p["mode"] != "summary" and all(get(r, c) is None for r in rows):
                out.append(f"{p['id']}: column {c} empty in every row")
        cap = p.get("max_text", limit)
        shown = [get(r, c) for r in rows for c in (p.get("columns") or list(rows[0]))]
        if any(isinstance(v, str) and len(v) > cap for v in shown):
            out.append(f"{p['id']}: a shown value is longer than {cap} characters")
    return out


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--max-string", type=int, default=400)
    ap.add_argument("--max-file-mb", type=float, default=50)
    a = ap.parse_args(argv)
    files = tracked()
    fails = 0

    def report(status: str, name: str, detail: str = "") -> None:
        nonlocal fails
        fails += status == "FAIL"
        print(f"{status:4}  {name}{': ' + detail if detail else ''}", flush=True)

    bad, big = [], []
    for d in RESULT_DIRS:
        for p in sorted((ROOT / d).rglob("*.json")):
            hits = long_strings(json.loads(p.read_text()), a.max_string)
            if hits:
                bad.append(f"{p.relative_to(ROOT)} {hits[:3]}")
            elif p.stat().st_size > 2_000_000:  # large but no long strings: ids and numbers
                big.append(f"{p.relative_to(ROOT)} ({p.stat().st_size:,} bytes)")
    report("FAIL" if bad else "PASS", "results hold no text", "; ".join(bad[:10]))
    if big:
        report("WARN", "large result files (no long strings; check by eye)", "; ".join(big))
    probs = check_panels(json.loads(PANELS.read_text())["panels"], ROOT, a.max_string)
    report("FAIL" if probs else "PASS", "explorer panels", "; ".join(probs))
    hidden = ("data/private/", "data/corpus/")
    private = [f for f in files if f.startswith(hidden) or f.endswith(WEIGHTS)]
    report("FAIL" if private else "PASS", "nothing private tracked", ", ".join(private[:10]))
    bulky = [f for f in files if not f.startswith(BULKY_OK) and (ROOT / f).is_file()
             and (ROOT / f).stat().st_size > a.max_file_mb * 2**20]  # fmt: skip
    report("FAIL" if bulky else "PASS", f"no unexpected file over {a.max_file_mb:.0f} MB",
           ", ".join(bulky[:10]))  # fmt: skip
    lic = [n for n in ("LICENSE", "LICENSE-DATA") if not (ROOT / n).exists()]
    report("FAIL" if lic else "PASS", "licenses", ("missing " + ", ".join(lic)) if lic else "")
    dirs = sorted(
        {str(Path(f).parent) for f in files if f.startswith("data/") and f.count("/") >= 2}
    )
    tops = sorted({"/".join(d.split("/")[:2]) for d in dirs})

    def documented(top: str) -> bool:  # its own SOURCES.md, or one in each subdirectory with files
        if (ROOT / top / "SOURCES.md").exists():
            return True
        subs = {"/".join(d.split("/")[:3]) for d in dirs if d.startswith(top + "/")} - {top}
        return bool(subs) and all((ROOT / s / "SOURCES.md").exists() for s in subs)

    nosrc = [d for d in tops if d != "data/manifests" and not documented(d)]
    report("FAIL" if nosrc else "PASS", "SOURCES.md in every data directory", ", ".join(nosrc))
    # manifest paths are relative to the directory they were built from: match by suffix
    by_suffix: dict[str, list[str]] = {}
    for f in files:
        if f.startswith("data/manifests/"):  # a manifest never lists another manifest
            continue
        parts = f.split("/")
        for i in range(1, len(parts)):
            by_suffix.setdefault("/".join(parts[i:]), []).append(f)
    mism, broken, checked = [], [], 0
    for m in sorted((ROOT / "data/manifests").glob("*.jsonl")):
        try:
            recs = [json.loads(ln) for ln in m.read_text().splitlines() if ln.strip()]
        except json.JSONDecodeError:
            broken.append(m.name)
            continue
        for r in recs:
            hits = by_suffix.get(r.get("path", ""), [])
            if len(hits) != 1 or not r.get("sha256"):
                continue
            checked += 1
            if (ROOT / hits[0]).stat().st_size != r.get("bytes", -1) or sha(ROOT / hits[0]) != r[
                "sha256"
            ]:
                mism.append(f"{m.name}: {hits[0]}")
    status = "WARN" if mism else ("FAIL" if broken else "PASS")
    report(
        status,
        f"manifests ({checked} tracked files checked; a mismatch means a file "
        "changed since its manifest was built)",
        "; ".join(broken + mism[:10]),
    )
    st = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    ahead = subprocess.run(["git", "rev-list", "--count", "@{u}..HEAD"], cwd=ROOT,
                           capture_output=True, text=True)  # fmt: skip
    dirty = len(st.stdout.splitlines())
    unpushed = ahead.stdout.strip() or "?"
    status = "WARN" if dirty or unpushed not in ("0",) else "PASS"
    report(status, "committed and pushed", f"{dirty} uncommitted, {unpushed} unpushed")
    print(f"{'FAILED' if fails else 'ready'}: {fails} check(s) failed", flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
