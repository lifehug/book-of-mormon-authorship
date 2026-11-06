#!/usr/bin/env python3
"""Print one line whenever a long job changes state, so a crash or a finish is seen at once
(owner, 2026-11-06: the 1B died at 07:38 and nobody noticed for an hour).

Watches tmux sessions starting and ending, new driver events in ``logs/large_pod/watch.log``,
and in the Mac job logs: EXIT lines, errors, and silence (no new output for ``--stall`` minutes).
Prints only on change; meant to run under a monitor that turns each line into a notification.

Usage::

    python scripts/jobwatch.py [--interval 60 --stall 20]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "logs/large_pod/watch.log"
LOGS = [
    "sweep_mask.log",
    "sweep_chain.log",
    "bom29.log",
    "alm_large.log",
    "candidates.log",
    "imitation.log",
    "mac_gpu.log",
    "imitation_base.log",
    "gpt2.log",
]
BAD = re.compile(r"^EXIT|Traceback|Error|error:|FAILED|Killed")


def sessions() -> set[str]:
    r = subprocess.run(["tmux", "ls", "-F", "#S"], capture_output=True, text=True)
    return set(r.stdout.split())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--interval", type=float, default=60)
    ap.add_argument("--stall", type=float, default=20)
    a = ap.parse_args(argv)
    prev = sessions()
    events = len(DRIVER.read_text().splitlines()) if DRIVER.exists() else 0
    size = {f: (ROOT / "logs" / f).stat().st_size if (ROOT / "logs" / f).exists() else 0
            for f in LOGS}  # fmt: skip
    seen = {f: time.time() for f in LOGS}
    stalled: set[str] = set()
    last_driver = ""
    while True:
        cur = sessions()
        for s in sorted(prev - cur):
            print(f"ENDED tmux '{s}'", flush=True)
        for s in sorted(cur - prev):
            print(f"STARTED tmux '{s}'", flush=True)
        prev = cur
        if DRIVER.exists():
            lines = DRIVER.read_text().splitlines()
            for ln in lines[events:]:
                body = ln[20:]  # without the timestamp: a retry loop repeats one line
                if body != last_driver:
                    print(f"1B: {ln[:300]}", flush=True)
                last_driver = body
            events = len(lines)
        for f in LOGS:
            p = ROOT / "logs" / f
            if not p.exists():
                continue
            sz = p.stat().st_size
            if sz < size[f]:  # rotated or rewritten
                size[f] = 0
            if sz > size[f]:
                with p.open("rb") as fh:
                    fh.seek(size[f])
                    new = fh.read().decode("utf-8", "replace")
                for ln in new.splitlines():
                    if BAD.search(ln):
                        print(f"{f}: {ln[:300]}", flush=True)
                size[f], seen[f] = sz, time.time()
                stalled.discard(f)
            elif sz and f not in stalled and time.time() - seen[f] > a.stall * 60:
                last = (p.read_text(errors="replace").splitlines() or [""])[-1]
                if not last.startswith("EXIT"):
                    print(f"STALL {f}: no output for {a.stall:.0f} min (last: {last[:120]})",
                          flush=True)  # fmt: skip
                stalled.add(f)
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
