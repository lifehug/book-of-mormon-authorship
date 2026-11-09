#!/usr/bin/env python3
"""Drive the BOM-30 style-embedding training on a rented H100 (Amendment 24; owner's cap ~$50).

One resumable state machine, run under tmux on the Mac: create a Secure Cloud pod -> set it up ->
upload the passages and the base model (each file's SHA-256 checked on the pod) -> smoke test ->
train in tmux on the pod, restarting a dead run from its checkpoint (at most 3 times) -> copy
``style.pt``, ``log.jsonl`` and ``run.json`` home (SHA-256 checked) -> delete the text and models
from the pod, check the deletion -> terminate the pod. Spend is estimated from the pod's hourly
price; at the cap the pod is stopped (not terminated) and the owner is asked. Events go to the
BOM-30 issue. State: ``logs/style_pod/state.json``.

Usage::

    python scripts/style_pod.py --issue 40 [--cap 50] [--size mid]

``--size mid`` trains the same encoder on the 590M backbone (owner, 2026-11-09; Amendment 37):
its own state (``logs/style_pod_mid/``), pod and output folder (``runs/style_mid``), so the
registered 297M encoder's files are never touched.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pod_watch", ROOT / "scripts/pod_watch.py")
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)

STATE = ROOT / "logs/style_pod/state.json"
SSH = "stylepod"
POD_NAME = "bom30-style"
PRICE = 3.99  # Secure H100 SXM, $/h (docs/runpod-setup.md)
IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
REPO = "https://github.com/lifehug/book-of-mormon-authorship.git"
R = "/workspace/repo"
UPLOADS = {  # local -> path under the repo on the pod
    "data/corpus/style_embed/passages.bin": "data/corpus/style_embed/passages.bin",
    "data/corpus/style_embed/passages.parquet": "data/corpus/style_embed/passages.parquet",
    "data/style_embed/authors.parquet": "data/style_embed/authors.parquet",
    "data/corpus/timelocked_lm/runs/base/model.pt": "data/corpus/timelocked_lm/runs/base/model.pt",
}
OUT = "data/corpus/style_embed/runs/style"
HOME = ROOT / OUT
FETCH = ["style.pt", "log.jsonl", "run.json"]
TRAIN_ARGS = ""


def configure(size: str) -> None:
    """Point the driver at another backbone's encoder (see the module docstring)."""
    global STATE, SSH, POD_NAME, UPLOADS, OUT, HOME, TRAIN_ARGS
    if size == "base":
        return
    STATE = ROOT / f"logs/style_pod_{size}/state.json"
    SSH, POD_NAME = f"stylepod{size}", f"bom30-style-{size}"
    model = f"data/corpus/timelocked_lm/runs/{size}/model.pt"
    UPLOADS = {k: v for k, v in UPLOADS.items() if "timelocked_lm" not in k} | {model: model}
    OUT = f"data/corpus/style_embed/runs/style_{size}"
    HOME = ROOT / OUT
    TRAIN_ARGS = f" --size {size}"


def log(msg: str) -> None:
    line = f"{time.strftime('%F %T')} {msg}"
    print(line, flush=True)
    with (STATE.parent / "watch.log").open("a") as f:
        f.write(line + "\n")


def save(s: dict) -> None:
    STATE.write_text(json.dumps(s, indent=1))


def event(s: dict, msg: str, issue: int) -> None:
    log(msg)
    s.setdefault("events", []).append(f"{time.strftime('%F %T')} {msg}")
    save(s)
    pw.sh(["gh", "issue", "comment", str(issue), "-b", f"Style-embedding pod: {msg}"], 120)


def remote(cmd: str, timeout: int = 900) -> tuple[int, str]:
    return pw.sh(["ssh", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes", SSH, cmd], timeout)


B2_PREFIX = "data/corpus/"  # the bucket mirrors data/corpus/ (scripts/b2_backup.sh)


def b2_prefetch(names: list[str]) -> None:
    """Pull the large model files among ``names`` onto the pod from the private B2 backup, so the
    Mac's slow upload carries each model once (owner, 2026-11-09). The key goes on the pod for the
    download only and is removed and checked, as for the training tokens. Best effort: a file not
    yet in the bucket, or any failure, is left to the rsync that follows, and every file's SHA-256
    is checked after it either way."""
    import subprocess

    big = [n for n in names if n.startswith(B2_PREFIX + "timelocked_lm/runs/") and
           n.endswith(".pt") and (ROOT / n).exists()]  # fmt: skip
    if not big:
        return
    have = remote(" ; ".join(f"stat -c %s {R}/{n} 2>/dev/null || echo 0" for n in big))[1].split()
    want = [n for n, h in zip(big, have, strict=False) if h != str((ROOT / n).stat().st_size)]
    if not want:
        return
    creds = (Path.home() / ".config/backblaze/credentials").read_text()
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", SSH, "umask 077 && cat > /root/.b2"],
                       input=creds, text=True, capture_output=True, timeout=60)  # fmt: skip
    if p.returncode == 0:
        pulls = " ; ".join(
            f"mkdir -p $(dirname {R}/{n}) && rclone copyto :b2:$B2_BUCKET/{n[len(B2_PREFIX):]} "
            f"{R}/{n}" for n in want)  # fmt: skip
        rc, out = remote(
            "(command -v rclone > /dev/null || (apt-get install -y -qq unzip > /dev/null && "
            "curl -s https://rclone.org/install.sh | bash > /dev/null)); set -a; . /root/.b2; "
            "set +a; export RCLONE_B2_ACCOUNT=$B2_KEY_ID RCLONE_B2_KEY=$B2_APP_KEY; "
            f"{pulls}; rm -f /root/.b2", 3600)  # fmt: skip
        log(f"B2 prefetch of {len(want)} model file(s): rc {rc} {out[-200:]}")
    for _ in range(3):
        remote("rm -f /root/.b2")
        if "GONE" in remote("test -e /root/.b2 && echo PRESENT || echo GONE")[1]:
            return
    raise RuntimeError("B2 key could not be confirmed removed from the pod")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def spend(s: dict) -> float:
    return PRICE * (time.time() - s["created"]) / 3600 if s.get("created") else 0.0


def ssh_config(ip: str, port: int) -> None:
    cfg = Path.home() / ".ssh/config"
    text = cfg.read_text() if cfg.exists() else ""
    blocks = [b for b in text.split("\nHost ") if not b.startswith(f"{SSH}\n")]
    text = "\nHost ".join(blocks).rstrip() + (
        f"\n\nHost {SSH}\n  HostName {ip}\n  Port {port}\n  User root\n"
        "  IdentityFile ~/.ssh/id_ed25519\n  StrictHostKeyChecking accept-new\n"
        "  ServerAliveInterval 30\n")  # fmt: skip
    cfg.write_text(text)


def create(s: dict) -> None:
    body = {"name": POD_NAME, "imageName": IMAGE, "cloudType": "SECURE", "gpuCount": 1,
            "gpuTypeIds": ["NVIDIA H100 80GB HBM3"], "containerDiskInGb": 60,
            "volumeInGb": 100, "volumeMountPath": "/workspace", "ports": ["22/tcp"]}  # fmt: skip
    import urllib.request

    req = urllib.request.Request("https://rest.runpod.io/v1/pods", method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {pw._token()}",
                                          "Content-Type": "application/json",
                                          "User-Agent": pw.UA})  # fmt: skip
    with urllib.request.urlopen(req, timeout=120) as r:
        pod = json.loads(r.read())
    s["pod"], s["created"] = pod["id"], time.time()
    save(s)


def wait_ssh(s: dict) -> bool:
    for _ in range(60):
        pod = pw.rest("GET", f"/pods/{s['pod']}")
        ip, ports = pod.get("publicIp"), pod.get("portMappings") or {}
        if ip and ports.get("22"):
            ssh_config(ip, int(ports["22"]))
            if remote("echo ok", 60)[0] == 0:
                return True
        time.sleep(20)
    return False


def step(s: dict, issue: int, cap: float) -> bool:
    """Advance one phase; False when finished or stopped."""
    ph = s["phase"]
    if s.get("pod") and ph not in ("done",) and spend(s) > cap:
        pw.rest("POST", f"/pods/{s['pod']}/stop")
        event(s, f"**stopped at the ${cap:.0f} cap** (est. ${spend(s):.2f}); waiting for the "
                 "owner. Checkpoint kept on the pod.", issue)  # fmt: skip
        s["phase"] = "capped"
        save(s)
        return False
    if ph == "create":
        create(s)
        event(s, f"pod `{s['pod']}` created (Secure H100, ${PRICE}/h).", issue)
        s["phase"] = "setup"
    elif ph == "setup":
        if not wait_ssh(s):
            event(s, "pod not reachable over SSH after 20 min; terminating.", issue)
            pw.rest("DELETE", f"/pods/{s['pod']}")
            s["phase"] = "failed"
            save(s)
            return False
        cmds = [
            "apt-get update -qq && apt-get install -y -qq rsync tmux > /dev/null",
            f"git clone -q {REPO} {R} || (cd {R} && git pull -q)",
            "pip install -q 'pyarrow<18' tokenizers pyyaml",
            f"mkdir -p {R}/data/corpus/style_embed {R}/data/corpus/timelocked_lm/runs/base "
            f"{R}/data/corpus/timelocked_lm/runs/mid",
        ]
        for c in cmds:
            rc, out = remote(c, 1800)
            if rc != 0:
                event(s, f"setup failed on `{c[:60]}`: {out[-300:]}", issue)
                return False
        s["phase"] = "upload"
    elif ph == "upload":
        b2_prefetch(list(UPLOADS.values()))
        for local, rel in UPLOADS.items():
            rc, out = pw.sh(["rsync", "-rt", "--no-o", "--no-g", "--partial", str(ROOT / local),
                             f"{SSH}:{R}/{rel}"], 7200)  # fmt: skip
            if rc != 0:
                log(f"upload {local} failed ({out[-200:]}); retrying")
                return True
            rc, out = remote(f"sha256sum {R}/{rel}")
            if rc != 0 or out.split()[0] != sha(ROOT / local):
                log(f"checksum mismatch on {rel}; re-uploading")
                return True
        event(s, f"upload verified ({len(UPLOADS)} files, SHA-256).", issue)
        s["phase"] = "smoke"
    elif ph == "smoke":
        rc, out = remote(f"cd {R} && python -m style_embed.train --out /workspace/runs/tiny "
                         "--tiny --max-steps 3", 1800)  # fmt: skip
        if rc != 0:
            event(s, f"smoke test failed: {out[-400:]}", issue)
            return False
        rc, out = remote(f"cd {R} && tmux new-session -d -s train 'python -m style_embed.train "
                         f"--out {R}/{OUT}{TRAIN_ARGS} 2>&1 | tee -a /workspace/train.out'",
                         )  # fmt: skip
        event(s, "smoke test passed; **training started** (20,000 steps).", issue)
        s["phase"], s["restarts"], s["train_started"] = "train", 0, time.time()
    elif ph == "train":
        rc, out = remote(f"grep heldout {R}/{OUT}/log.jsonl | tail -n 1; "
                         f"ls {R}/{OUT}/style.pt 2>/dev/null; "
                         "tmux has-session -t train 2>/dev/null && echo ALIVE")  # fmt: skip
        if rc not in (0, 1, 2):
            log(f"poll failed: {out[-200:]}")
            return True
        if "style.pt" in out:
            s["phase"] = "fetch"
        elif "ALIVE" not in out:
            if s["restarts"] >= 3:
                event(s, "training died 3 times; stopping the pod for the owner.", issue)
                pw.rest("POST", f"/pods/{s['pod']}/stop")
                return False
            s["restarts"] += 1
            remote(f"cd {R} && tmux new-session -d -s train 'python -m style_embed.train "
                   f"--out {R}/{OUT}{TRAIN_ARGS} 2>&1 | tee -a /workspace/train.out'")  # fmt: skip
            event(s, f"training process gone; restarted from checkpoint ({s['restarts']}/3). "
                     f"Last: {out[:200]}", issue)  # fmt: skip
        else:
            last = out.splitlines()[0] if out else ""
            s["last"] = last
            try:
                r = json.loads(last)
                if r["step"] >= s.get("next_report", 5000):
                    s["next_report"] = r["step"] - r["step"] % 5000 + 5000
                    top1, cost = r["heldout_top1"], spend(s)
                    event(s, f"step {r['step']:,}: loss {r['loss']:.3f}, held-out top-1 "
                             f"{top1:.3f}; est. spend ${cost:.2f}", issue)  # fmt: skip
            except (json.JSONDecodeError, KeyError):
                pass
            save(s)
            time.sleep(300)
            return True
    elif ph == "fetch":
        HOME.mkdir(parents=True, exist_ok=True)
        for f in FETCH:
            rc, out = pw.sh(["rsync", "-rt", f"{SSH}:{R}/{OUT}/{f}", str(HOME / f)], 3600)
            rc2, out2 = remote(f"sha256sum {R}/{OUT}/{f}")
            if rc or rc2 or out2.split()[0] != sha(HOME / f):
                log(f"fetch of {f} not verified; retrying")
                return True
        event(s, f"model home and verified in `{OUT}` ({', '.join(FETCH)}).", issue)
        s["phase"] = "cleanup"
    elif ph == "cleanup":
        remote(f"rm -rf {R}/data/corpus /workspace/runs /workspace/train.out {R}/{OUT}")
        rc, out = remote(f"ls {R}/data/corpus 2>/dev/null | wc -l; "
                         f"find /workspace -name 'passages.*' | wc -l")  # fmt: skip
        if rc != 0 or out.split() != ["0", "0"]:
            log(f"deletion not confirmed ({out}); retrying")
            return True
        pw.rest("DELETE", f"/pods/{s['pod']}")
        event(s, f"passages and models deleted from the pod (checked); pod **terminated**. "
                 f"Est. spend ${spend(s):.2f}.", issue)  # fmt: skip
        s["phase"] = "done"
        save(s)
        return False
    save(s)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--cap", type=float, default=50.0)
    ap.add_argument("--size", choices=["base", "mid"], default="base", help="the backbone")
    a = ap.parse_args(argv)
    configure(a.size)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(STATE.read_text()) if STATE.exists() else {"phase": "create"}
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a.issue, a.cap):
                break
        except Exception as e:  # noqa: BLE001 -- a transient API or network failure; retry
            log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
