"""Remove from the B2 backup the model weights that Hugging Face already holds, byte for byte.

Owner, 2026-11-11: "if things are in hugging face we don't need them anymore in b2". The public
Hub copy plus the Mac's copy replace the private B2 copy, for weights only. A file qualifies only
if the Hub's SHA-256 for it equals the SHA-256 of the local file, freshly computed. Anything else
(corpus text, ``inputs/`` folders, a file missing or different on the Hub) stays in B2.

Writes the qualifying corpus paths to ``data/manifests/b2_published_on_hf.txt``. That list is the
public record of what was pruned, and ``scripts/b2_backup.sh upload`` excludes it so the weekly
job does not send the files back. Dry run by default; ``--delete`` removes them from the bucket.

Usage::

    uv run python scripts/b2_prune_published.py [--delete]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from timelocked_lm.publish import OWNER, SINGLE, WEIGHTS, weight_files  # noqa: E402

LIST = Path("data/manifests/b2_published_on_hf.txt")
CORPUS = Path("data/corpus")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while b := f.read(1 << 24):
            h.update(b)
    return h.hexdigest()


def _b2_env() -> tuple[dict, str]:
    env = dict(os.environ)
    for line in Path("~/.config/backblaze/credentials").expanduser().read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip().removeprefix("export ")] = v.strip().strip("'\"")
    env["RCLONE_B2_ACCOUNT"], env["RCLONE_B2_KEY"] = env["B2_KEY_ID"], env["B2_APP_KEY"]
    return env, f":b2:{env['B2_BUCKET']}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--delete", action="store_true", help="remove the files from B2 (default: list)"
    )
    ap.add_argument("--token-file", type=Path, default=Path("~/.config/huggingface/token"))
    a = ap.parse_args(argv)
    from huggingface_hub import HfApi

    api = HfApi(token=a.token_file.expanduser().read_text().strip())
    keep, prune, size = [], [], 0
    for name in sorted(set(WEIGHTS) | set(SINGLE)):
        hub = {f.path: f.lfs.sha256 for f in api.list_repo_tree(f"{OWNER}/{name}", recursive=True)
               if getattr(f, "lfs", None)}  # fmt: skip
        for p, dst in weight_files(name):
            rel = str(p.relative_to(CORPUS))
            if hub.get(dst) and hub[dst] == _sha256(p):
                prune.append(rel)
                size += p.stat().st_size
            else:
                keep.append(f"{name}/{dst}")
        print(f"{name}: {len(prune)} verified so far, {len(keep)} not on the Hub", flush=True)
    LIST.write_text("".join(f"{r}\n" for r in sorted(prune)))
    print(f"{len(prune)} files, {size / 2**30:.1f} GiB identical on the Hub -> {LIST}")
    if keep:
        print(f"{len(keep)} weight files not (yet) identical on the Hub, kept: {keep[:5]} ...")
    if not a.delete:
        print("dry run; --delete removes the listed files from B2")
        return 0
    env, root = _b2_env()
    cmd = ["rclone", "delete", root, "--files-from", str(LIST), "--b2-hard-delete",
           "--log-level", "INFO", "--log-file", "logs/b2_backup.log"]  # fmt: skip
    print(" ".join(cmd), flush=True)
    return subprocess.run(cmd, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
