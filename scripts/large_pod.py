#!/usr/bin/env python3
"""Train the 1B time-locked model on 8 H100s (BOM-27, Amendment 26; owner's decision 2026-11-06).

Resumable state machine under tmux on the Mac: create a Secure Cloud 8-GPU pod -> set it up -> pull
the training tokens from the private B2 backup (the bucket key is put on the pod for the download
only, then deleted and the deletion checked) and check every token file against
``data/manifests/timelocked_lm_tokens.jsonl`` -> smoke test on all 8 GPUs -> train under torchrun,
restarting a dead run from its checkpoint (at most 3 times) -> copy ``model.pt``, ``log.jsonl``,
``run.json`` home (SHA-256 checked) -> delete the tokens from the pod, check -> terminate.

Money: the pod is stopped if the RunPod balance falls below ``--floor`` (the run resumes from its
last checkpoint once the balance is back above ``--resume-at``), and at ``--cap`` estimated spend.
Events go to the Run status issue.

Usage::

    python scripts/large_pod.py --issue 75 [--gpus 8 --cap 650 --floor 25 --resume-at 100]
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

sp.STATE = ROOT / "logs/large_pod/state.json"
sp.SSH = "largepod"
sp.POD_NAME = "bom27-1b"
GPUS = 8
sp.PRICE = 3.99 * GPUS
R = sp.R
TOK = "data/corpus/timelocked_lm/tokens"
OUT = "data/corpus/timelocked_lm/runs/large"
MANIFEST = ROOT / "data/manifests/timelocked_lm_tokens.jsonl"


def train_cmd() -> str:
    # micro-batch 8: the first launch (16) ran out of memory on step 2 once the optimizer state
    # existed (67.9 of 80 GB at step 1, logs/large_pod/diag_micro16.out; that run was also in
    # fp32 by a bug since fixed). At 8 in bf16 the peak is 33.8 GB. Same 512-sequence step.
    return (f"cd {R} && tmux new-session -d -s train 'PYTORCH_CUDA_ALLOC_CONF=expandable_segments:"
            f"True torchrun --nproc_per_node={GPUS} -m "
            f"timelocked_lm.train large --out {R}/{OUT} --micro-batch 8 2>&1 | tee -a "
            "/workspace/train.out'")  # fmt: skip


def create(s: dict) -> None:
    import urllib.request

    body = {"name": sp.POD_NAME, "imageName": sp.IMAGE, "cloudType": "SECURE", "gpuCount": GPUS,
            "gpuTypeIds": ["NVIDIA H100 80GB HBM3"], "containerDiskInGb": 100,
            "volumeInGb": 200, "volumeMountPath": "/workspace", "ports": ["22/tcp"]}  # fmt: skip
    req = urllib.request.Request("https://rest.runpod.io/v1/pods", method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {sp.pw._token()}",
                                          "Content-Type": "application/json",
                                          "User-Agent": sp.pw.UA})  # fmt: skip
    with urllib.request.urlopen(req, timeout=120) as r:
        pod = json.loads(r.read())
    s["pod"], s["created"] = pod["id"], time.time()
    sp.save(s)


def pull_tokens(s: dict, issue: int) -> bool:
    creds = (Path.home() / ".config/backblaze/credentials").read_text()
    import subprocess

    p = subprocess.run(["ssh", "-o", "BatchMode=yes", sp.SSH, "umask 077 && cat > /root/.b2"],
                       input=creds, text=True, capture_output=True, timeout=60)  # fmt: skip
    if p.returncode != 0:
        sp.log(f"could not place the B2 key: {p.stderr[-200:]}")
        return False
    rc, out = sp.remote(
        f"set -a; . /root/.b2; set +a; mkdir -p {R}/{TOK} && "
        "RCLONE_B2_ACCOUNT=$B2_KEY_ID RCLONE_B2_KEY=$B2_APP_KEY rclone copy "
        f":b2:$B2_BUCKET/timelocked_lm/tokens {R}/{TOK} --transfers 16 --checkers 16; "
        "rc=$?; rm -f /root/.b2; exit $rc", 7200)  # fmt: skip
    gone = sp.remote("test -e /root/.b2 && echo PRESENT || echo GONE")[1]
    if "GONE" not in gone:
        sp.remote("rm -f /root/.b2")
        sp.event(s, "B2 key still on the pod after the download; removing it and retrying.", issue)
        return False
    if rc != 0:
        sp.log(f"token pull failed: {out[-300:]}")
        return False
    lines = [json.loads(ln) for ln in MANIFEST.read_text().splitlines() if ln.strip()]
    sums = "\n".join(f"{r['sha256']}  {r['path']}" for r in lines) + "\n"
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", sp.SSH,
                        f"cd {R}/{TOK} && cat > /workspace/tok.sha && sha256sum -c --quiet "
                        "/workspace/tok.sha && echo ALLOK"],
                       input=sums, text=True, capture_output=True, timeout=3600)  # fmt: skip
    if "ALLOK" not in p.stdout:
        sp.log(f"token checksums failed: {(p.stdout + p.stderr)[-300:]}")
        return False
    sp.event(s, f"training tokens pulled from B2 and checked ({len(lines)} files, SHA-256); "
                "B2 key removed from the pod (checked).", issue)  # fmt: skip
    return True


def money(s: dict, issue: int, cap: float, floor: float, resume_at: float) -> bool:
    """True to carry on; stops the pod on a low balance or at the cap."""
    if s["phase"] in ("create", "done", "paused", "capped"):
        return True
    if sp.spend(s) > cap:
        sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
        sp.event(s, f"**stopped at the ${cap:.0f} cap** (est. ${sp.spend(s):.0f}).", issue)
        s["phase"] = "capped"
        return False
    bal = sp.pw.balance()
    if bal is not None and bal < floor:
        sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
        s["resume_phase"], s["phase"] = s["phase"], "paused"
        sp.event(s, f"**paused**: RunPod balance ${bal:.0f} is under ${floor:.0f}. Pod stopped; "
                    f"training resumes from its last checkpoint once the balance is over "
                    f"${resume_at:.0f} (BOM-70).", issue)  # fmt: skip
        return False
    return True


def step(s: dict, issue: int, a) -> bool:
    if not money(s, issue, a.cap, a.floor, a.resume_at):
        sp.save(s)
        return s["phase"] == "paused"
    ph = s["phase"]
    if ph == "paused":
        bal = sp.pw.balance()
        if bal is not None and bal >= a.resume_at:
            sp.pw.rest("POST", f"/pods/{s['pod']}/start")
            if sp.wait_ssh(s):
                s["phase"] = "launch" if s.get("resume_phase") == "watch" else s["resume_phase"]
                sp.event(s, f"balance ${bal:.0f}: pod restarted, resuming.", issue)
        else:
            time.sleep(600)
        sp.save(s)
        return True
    if ph == "create":
        create(s)
        sp.event(s, f"1B pod `{s['pod']}` created (Secure, {GPUS} x H100, ${sp.PRICE:.2f}/h).",
                 issue)  # fmt: skip
        s["phase"] = "setup"
    elif ph == "setup":
        if not sp.wait_ssh(s):
            sp.pw.rest("DELETE", f"/pods/{s['pod']}")
            sp.event(s, "pod not reachable over SSH; terminated.", issue)
            s["phase"] = "failed"
            sp.save(s)
            return False
        for c in ["apt-get update -qq && apt-get install -y -qq rsync tmux curl unzip > /dev/null",
                  "command -v rclone || (curl -s https://rclone.org/install.sh | bash > /dev/null)",
                  f"git clone -q {sp.REPO} {R} || (cd {R} && git pull -q)",
                  "pip install -q 'pyarrow<18' tokenizers pyyaml"]:  # fmt: skip
            rc, out = sp.remote(c, 1800)
            if rc != 0:
                sp.event(s, f"setup failed on `{c[:50]}`: {out[-300:]}", issue)
                return False
        s["phase"] = "tokens"
    elif ph == "tokens":
        if not pull_tokens(s, issue):
            time.sleep(60)
            return True
        s["phase"] = "smoke"
    elif ph == "smoke":
        rc, out = sp.remote(f"cd {R} && torchrun --nproc_per_node={GPUS} -m timelocked_lm.train "
                            "tiny --out /workspace/runs/tiny --max-steps 10 --micro-batch 1",
                            1800)  # fmt: skip
        if rc != 0:
            sp.event(s, f"smoke test failed: {out[-400:]}", issue)
            return False
        s["phase"], s["restarts"] = "launch", 0
    elif ph == "launch":
        sp.remote(train_cmd())
        sp.event(s, "**1B training started** (48,931 steps).", issue)
        s["phase"] = "watch"
    elif ph == "watch":
        rc, out = sp.remote(f"tail -n 1 {R}/{OUT}/log.jsonl; grep val_loss {R}/{OUT}/log.jsonl | "
                            f"tail -n 1; ls {R}/{OUT}/model.pt 2>/dev/null; tmux has-session -t "
                            "train 2>/dev/null && echo ALIVE")  # fmt: skip
        if rc == 255 or "Connection" in out and "timed out" in out or "refused" in out:
            # the Mac cannot reach the pod: that says nothing about training, which runs on the
            # pod in tmux. Never restart or stop for this (2026-11-06: an SSH outage was read as
            # three crashes and the pod was stopped mid-run). Report once an hour.
            s["unreachable"] = s.get("unreachable", 0) + 1
            if s["unreachable"] % 12 == 1:
                sp.event(s, f"pod unreachable over SSH ({s['unreachable']} checks); training "
                            "left alone, retrying.", issue)  # fmt: skip
            sp.save(s)
            time.sleep(300)
            return True
        s["unreachable"] = 0
        if "model.pt" in out:
            s["phase"] = "fetch"
        elif "ALIVE" not in out:
            err = sp.remote("tail -n 40 /workspace/train.out")[1]  # the error, kept on the Mac
            (ROOT / "logs/large_pod").mkdir(parents=True, exist_ok=True)
            with (ROOT / "logs/large_pod/train_tail.log").open("a") as f:
                f.write(f"--- {sp.pw.now()}\n{err}\n")
            if s["restarts"] >= 3:
                sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
                sp.event(s, f"training died 3 times; pod stopped for the owner. {out[-300:]}",
                         issue)  # fmt: skip
                return False
            s["restarts"] += 1
            sp.remote(train_cmd())
            sp.event(s, f"training process gone; restarted from checkpoint "
                        f"({s['restarts']}/3). Last output: `{err.strip()[-200:]}`",
                     issue)  # fmt: skip
        else:
            try:
                last = json.loads(out.splitlines()[0])
                if last["step"] >= s.get("next_report", 5000):
                    s["next_report"] = last["step"] - last["step"] % 5000 + 5000
                    v = json.loads(out.splitlines()[1]) if len(out.splitlines()) > 1 else {}
                    sp.event(s, f"step {last['step']:,} of 48,931; val loss "
                                f"{v.get('val_loss', float('nan')):.4f}; est. spend "
                                f"${sp.spend(s):.0f}", issue)  # fmt: skip
            except (json.JSONDecodeError, IndexError, KeyError):
                pass
            sp.save(s)
            time.sleep(300)
            return True
    elif ph == "fetch":
        home = ROOT / OUT
        home.mkdir(parents=True, exist_ok=True)
        for f in ("model.pt", "log.jsonl", "run.json"):
            rc, _ = sp.pw.sh(["rsync", "-rt", "--partial", f"{sp.SSH}:{R}/{OUT}/{f}",
                              str(home / f)], 7200)  # fmt: skip
            rc2, out2 = sp.remote(f"sha256sum {R}/{OUT}/{f}")
            if rc or rc2 or out2.split()[0] != sp.sha(home / f):
                sp.log(f"fetch of {f} not verified; retrying")
                return True
        sp.event(s, f"**1B finished**; model home and verified in `{OUT}`.", issue)
        s["phase"] = "cleanup"
    elif ph == "cleanup":
        sp.remote(f"rm -rf {R}/data/corpus /workspace/runs /workspace/train.out /workspace/tok.sha")
        rc, out = sp.remote(f"ls {R}/data/corpus 2>/dev/null | wc -l")
        if rc != 0 or out.strip() != "0":
            return True
        sp.pw.rest("DELETE", f"/pods/{s['pod']}")
        sp.event(s, f"tokens deleted from the pod (checked); pod **terminated**. Est. spend "
                    f"${sp.spend(s):.0f}.", issue)  # fmt: skip
        s["phase"] = "done"
        sp.save(s)
        return False
    sp.save(s)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--cap", type=float, default=650.0)
    ap.add_argument("--floor", type=float, default=25.0)
    ap.add_argument("--resume-at", type=float, default=100.0)
    ap.add_argument("--gpus", type=int, default=8, help="8 preferred; 4 when no 8-GPU pod is free")
    a = ap.parse_args(argv)
    global GPUS
    GPUS = a.gpus
    sp.PRICE = 3.99 * GPUS
    sp.STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(sp.STATE.read_text()) if sp.STATE.exists() else {"phase": "create"}
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a.issue, a):
                break
        except Exception as e:  # noqa: BLE001 -- transient API or network failure; retry
            sp.log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
