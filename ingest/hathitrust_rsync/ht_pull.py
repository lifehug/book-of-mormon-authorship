#!/usr/bin/env python3
"""Pull the project's HathiTrust volumes from the ht_text_pd_open_access dataset by rsync.

Standalone: no third-party packages. Run from the repo root on the Mac mini, inside tmux:

    python3 ht_pull.py --check                 # 1. can this machine reach the dataset?
    python3 ht_pull.py --limit 20              # 2. smoke test: 20 ids
    python3 ht_pull.py                         # 3. full pull (resumable; rerun after any stop)
    python3 ht_pull.py --report                # 4. count what arrived, write missing.txt

Steps:
  * Reads one HathiTrust volume id per line (default: hathitrust_ids_not_in_harvard.txt next to
    this script) and turns each into its pairtree path, exactly as HathiTrust's wiki script does
    (verified against the `pairtree` library on all 107,178 ids, 0 mismatches).
  * rsyncs those paths from datasets.hathitrust.org::ht_text_pd_open_access into DEST.
    Each volume arrives as DEST/<ns>/pairtree_root/<pairs>/<encoded id>/<encoded id>.mets.xml
    and <encoded id>.zip (one text file per page inside the zip).
  * About 76,000 of the ids are Google-digitized and are NOT in this dataset. rsync reports
    each as "link_stat ... failed: No such file or directory" and exits 23. That is expected.
    Roughly 31,000 volumes should arrive.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOST_MODULE = "datasets.hathitrust.org::ht_text_pd_open_access"
HERE = Path(__file__).resolve().parent
DEFAULT_IDS = HERE / "hathitrust_ids_not_in_harvard.txt"
DEFAULT_DEST = Path("data/corpus/hathitrust")
RSYNC = "/opt/homebrew/bin/rsync" if Path("/opt/homebrew/bin/rsync").exists() else "rsync"
SPECIAL = set('"*+,<=>?\\^|')


def id_encode(ident: str) -> str:
    """Pairtree id cleaning (spec section 3): hex-escape unsafe chars,
    then / -> =, : -> +, . -> ,
    """
    out = []
    for ch in ident:
        o = ord(ch)
        if o < 0x21 or o > 0x7E or ch in SPECIAL:
            out.append("".join(f"^{b:02x}" for b in ch.encode("utf-8")))
        else:
            out.append(ch)
    s = "".join(out)
    return s.replace("/", "=").replace(":", "+").replace(".", ",")


def pairtree_path(htid: str) -> str:
    ns, ident = htid.split(".", 1)
    enc = id_encode(ident)
    shorties = "/".join(enc[i : i + 2] for i in range(0, len(enc), 2))
    return f"{ns}/pairtree_root/{shorties}/{enc}"


def read_ids(p: Path, limit: int | None) -> list[str]:
    ids = [ln.strip() for ln in p.open(encoding="utf-8") if ln.strip()]
    return ids[:limit] if limit else ids


def check() -> int:
    print("public IPv4 (must be the address HathiTrust allow-listed, <your allow-listed IP>):")
    subprocess.run(["curl", "-4", "-s", "--max-time", "10", "ifconfig.me"], check=False)
    print()
    print(f"rsync: {RSYNC}")
    subprocess.run([RSYNC, "--version"], check=False, stdout=subprocess.PIPE)
    print(f"listing {HOST_MODULE}/ (top level) ...")
    rc = subprocess.run(
        [RSYNC, "--contimeout=30", "--timeout=60", HOST_MODULE + "/"], check=False
    ).returncode
    if rc == 0:
        print("OK: dataset reachable.")
    else:
        print(
            f"FAILED (rsync exit {rc}). A timeout waiting for the daemon connection means this\n"
            "machine's public IP is not allow-listed. Confirm the IP above, or reply on ticket\n"
            "GS-17502 (support@hathitrust.org) with the new address."
        )
    return rc


def pull(ids_file: Path, dest: Path, limit: int | None, dry_run: bool) -> int:
    ids = read_ids(ids_file, limit)
    dest.mkdir(parents=True, exist_ok=True)
    listing = dest / "path_list.txt"
    listing.write_text("\n".join(pairtree_path(h) for h in ids) + "\n", encoding="utf-8")
    log = dest / f"rsync_{time.strftime('%Y%m%d_%H%M%S')}.log"
    cmd = [
        RSYNC, "--copy-links", "--recursive", "--times", "--partial", "--ignore-errors",
        "--contimeout=60", "--timeout=300", "--info=progress2,stats",
        f"--log-file={log}", f"--files-from={listing}", HOST_MODULE, str(dest),
    ]  # fmt: skip
    if dry_run:
        cmd.insert(1, "--dry-run")
    print(f"{len(ids):,} ids -> {listing}\nlog: {log}\n" + " ".join(cmd), flush=True)
    rc = subprocess.run(cmd, check=False).returncode
    print(f"\nrsync exit {rc} (0 = all listed paths present; 23 = some missing, expected here)")
    report(ids_file, dest, limit)
    return 0 if rc in (0, 23) else rc


def report(ids_file: Path, dest: Path, limit: int | None) -> None:
    ids = read_ids(ids_file, limit)
    dest.mkdir(parents=True, exist_ok=True)
    have_zip, have_mets, missing, size = [], [], [], 0
    for h in ids:
        d = dest / pairtree_path(h)
        enc = d.name
        z, m = d / f"{enc}.zip", d / f"{enc}.mets.xml"
        if z.exists():
            have_zip.append(h)
            size += z.stat().st_size
        else:
            missing.append(h)
        if m.exists():
            have_mets.append(h)
    (dest / "missing.txt").write_text("\n".join(missing) + "\n", encoding="utf-8")
    (dest / "present.txt").write_text("\n".join(have_zip) + "\n", encoding="utf-8")
    summary = {
        "ids_requested": len(ids),
        "volumes_with_zip": len(have_zip),
        "volumes_with_mets": len(have_mets),
        "missing": len(missing),
        "zip_bytes": size,
        "zip_gb": round(size / 1e9, 2),
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (dest / "pull_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"present ids -> {dest / 'present.txt'}; missing ids -> {dest / 'missing.txt'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--ids", type=Path, default=DEFAULT_IDS)
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--check", action="store_true", help="only test access to the dataset")
    ap.add_argument("--report", action="store_true", help="only count what is on disk")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        return check()
    if a.report:
        report(a.ids, a.dest, a.limit)
        return 0
    if not Path("pyproject.toml").exists():
        print(
            "run from the repo root (book-of-mormon-authorship) so data/corpus/ resolves",
            file=sys.stderr,
        )
        return 2
    return pull(a.ids, a.dest, a.limit, a.dry_run)


if __name__ == "__main__":
    os.environ.setdefault("LC_ALL", "C")
    sys.exit(main())
