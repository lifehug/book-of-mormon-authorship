#!/usr/bin/env python3
"""Run the 297M benchmark jobs (BOM-28: Amendment 22's primary run and Amendment 23's V1-V3) on a
rented H100: the Mac mini's 16 GB swaps on a 297M fine-tune (owner approved, about $5-10).

Resumable state machine under tmux on the Mac: create a Secure Cloud pod -> set it up -> upload the
files the jobs read (the benchmark works and imposter-pool texts, listed by a dry run), the base
model and the scores already made, checking every file's SHA-256 on the pod -> run the four jobs in
order in tmux on the pod (each resumes from its saved scores; restarted up to 3 times) -> copy the
result files and per-author scores home (SHA-256 checked) -> delete the corpus files from the pod,
check -> terminate. Stops the pod at the cap. Events go to the BOM-28 issue.

Usage::

    python scripts/alm_pod.py --issue 38 --files <list of repo-relative paths> [--cap 15]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import style_pod as sp  # noqa: E402

sp.STATE = ROOT / "logs/alm_pod/state.json"
sp.SSH = "almpod"
sp.POD_NAME = "bom28-alm-300m"
R = sp.R
JOBS = [
    "python -m alm.benchmark base --micro-batch 8",
    "python -m alm.benchmark base --variant v1 --micro-batch 8",
    "python -m alm.variants v2 base --micro-batch 8",
    "python -m alm.variants v3 base",
]
RESULTS = ["alm_base.json", "alm_base_v1.json", "alm_base_v2.json", "alm_base_v3.json"]
EXTRA = ["data/corpus/timelocked_lm/runs/base/model.pt", "data/corpus/alm/benchmark/base"]


def step(s: dict, issue: int, cap: float, files: Path) -> bool:
    ph = s["phase"]
    if s.get("pod") and sp.spend(s) > cap:
        sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
        sp.event(s, f"**stopped at the ${cap:.0f} cap** (est. ${sp.spend(s):.2f}).", issue)
        s["phase"] = "capped"
        sp.save(s)
        return False
    if ph == "create":
        sp.create(s)
        sp.event(s, f"297M benchmark pod `{s['pod']}` created (Secure H100).", issue)
        s["phase"] = "setup"
    elif ph == "setup":
        if not sp.wait_ssh(s):
            sp.pw.rest("DELETE", f"/pods/{s['pod']}")
            sp.event(s, "pod not reachable; terminated.", issue)
            return False
        for c in ["apt-get update -qq && apt-get install -y -qq rsync tmux > /dev/null",
                  f"git clone -q {sp.REPO} {R} || (cd {R} && git pull -q)",
                  "pip install -q 'pyarrow<18' tokenizers pyyaml scipy scikit-learn"]:  # fmt: skip
            rc, out = sp.remote(c, 1800)
            if rc != 0:
                sp.event(s, f"setup failed on `{c[:50]}`: {out[-300:]}", issue)
                return False
        s["phase"] = "upload"
    elif ph == "upload":
        lst = ROOT / "logs/alm_pod/files.txt"
        names = [ln for ln in files.read_text().splitlines() if ln]
        lst.write_text("\n".join(names + EXTRA) + "\n")
        rc, out = sp.pw.sh(["rsync", "-rtLR", "--no-o", "--no-g", f"--files-from={lst}", ".",
                            f"{sp.SSH}:{R}/"], 7200)  # fmt: skip
        if rc != 0:
            sp.log(f"upload failed ({out[-200:]}); retrying")
            return True
        sums = ROOT / "logs/alm_pod/sha256.txt"
        rc, out = sp.pw.sh(["bash", "-c", f"cd {ROOT} && sha256sum $(cat {lst} | grep -v "
                            f"'alm/benchmark/base$') > {sums}"], 3600)  # fmt: skip
        sp.pw.sh(["rsync", str(sums), f"{sp.SSH}:{R}/sha256.txt"])
        rc, out = sp.remote(f"cd {R} && sha256sum -c --quiet sha256.txt && echo ALLOK", 3600)
        if "ALLOK" not in out:
            sp.log(f"checksums failed: {out[-300:]}; re-uploading")
            return True
        sp.event(s, f"upload verified ({len(names) + 1} files, SHA-256).", issue)
        s["phase"] = "run"
    elif ph == "run":
        script = " && ".join(JOBS) + " && touch /workspace/ALL_DONE"
        rc, out = sp.remote(f"cd {R} && tmux new-session -d -s alm '{script} 2>&1 | tee -a "
                            "/workspace/alm.out'")  # fmt: skip
        sp.event(s, "**297M benchmark jobs started** (primary, V1, V2, V3).", issue)
        s["phase"], s["restarts"] = "watch", 0
    elif ph == "watch":
        rc, out = sp.remote("ls /workspace/ALL_DONE 2>/dev/null; tmux has-session -t alm "
                            "2>/dev/null && echo ALIVE; grep -h 'closed set' /workspace/alm.out "
                            "| tail -4")  # fmt: skip
        if "ALL_DONE" in out:
            s["phase"] = "fetch"
        elif "ALIVE" not in out:
            if s["restarts"] >= 3:
                sp.event(s, f"jobs died 3 times; stopping the pod. {out[-300:]}", issue)
                sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
                return False
            s["restarts"] += 1
            s["phase"] = "run"
            sp.log(f"jobs not running; restarting ({s['restarts']}/3)")
        else:
            sp.save(s)
            time.sleep(120)
            return True
    elif ph == "fetch":
        for f in RESULTS:
            rc, _ = sp.pw.sh(["rsync", "-rt", f"{sp.SSH}:{R}/data/benchmark/{f}",
                              str(ROOT / "data/benchmark" / f)])  # fmt: skip
            rc2, out2 = sp.remote(f"sha256sum {R}/data/benchmark/{f}")
            if rc or rc2 or out2.split()[0] != sp.sha(ROOT / "data/benchmark" / f):
                sp.log(f"fetch of {f} not verified; retrying")
                return True
        sp.pw.sh(["rsync", "-rt", f"{sp.SSH}:{R}/data/corpus/alm/benchmark/",
                  str(ROOT / "data/corpus/alm/benchmark/")])  # fmt: skip
        sp.event(s, f"results home and verified: {', '.join(RESULTS)}.", issue)
        s["phase"] = "cleanup"
    elif ph == "cleanup":
        sp.remote(f"rm -rf {R}/data/corpus {R}/data/kjv_mask /workspace/alm.out")
        rc, out = sp.remote(f"ls {R}/data/corpus 2>/dev/null | wc -l")
        if rc != 0 or out.strip() != "0":
            return True
        sp.pw.rest("DELETE", f"/pods/{s['pod']}")
        sp.event(s, f"corpus files deleted from the pod (checked); pod **terminated**. "
                    f"Est. spend ${sp.spend(s):.2f}.", issue)  # fmt: skip
        s["phase"] = "done"
        sp.save(s)
        return False
    sp.save(s)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--files", type=Path, required=True)
    ap.add_argument("--cap", type=float, default=15.0)
    a = ap.parse_args(argv)
    sp.STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(sp.STATE.read_text()) if sp.STATE.exists() else {"phase": "create"}
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a.issue, a.cap, a.files):
                break
        except Exception as e:  # noqa: BLE001 -- transient API or network failure; retry
            sp.log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
