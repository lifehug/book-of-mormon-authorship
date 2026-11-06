#!/usr/bin/env python3
"""Fine-tune the candidate and control authorial models (BOM-28; Amendment 30) on a rented H100.

The Mac mini's 16 GB swaps on a 297M fine-tune, and these models' weights are kept for BOM-32.
Resumable state machine under tmux on the Mac: create a Secure Cloud pod -> set it up -> upload
the encoded inputs from ``python -m alm.candidates plan`` (licensed text in another form, Joseph
Smith Papers text among it), the plan and the base model, checking every file's SHA-256 on the
pod -> train and validate in tmux on the pod (resumes per unit; restarted up to 3 times) -> copy
the result, every unit's weights and scores home, each SHA-256 checked -> delete the inputs,
weights and model from the pod, check -> terminate. Stops the pod at the cap. Events go to the
issue.

Usage::

    python scripts/candidates_pod.py --issue 38 --size base|large [--cap 25]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import style_pod as sp  # noqa: E402

R = sp.R
INPUTS = "data/corpus/alm/candidates/inputs"
PLAN = "data/benchmark/alm_candidates_plan.json"


def configure(size: str) -> None:
    sp.STATE = ROOT / f"logs/candidates_pod_{size}/state.json"
    sp.SSH = f"candpod{size}"
    sp.POD_NAME = f"bom28-candidates-{size}"


def event(s: dict, msg: str, issue: int) -> None:
    sp.log(msg)
    s.setdefault("events", []).append(f"{time.strftime('%F %T')} {msg}")
    sp.save(s)
    sp.pw.sh(["gh", "issue", "comment", str(issue), "-b", f"Candidate-model pod: {msg}"], 120)


def create(s: dict) -> None:
    """One Secure H100 with room for every unit's weights (about 4 GB each at 1B)."""
    body = {"name": sp.POD_NAME, "imageName": sp.IMAGE, "cloudType": "SECURE", "gpuCount": 1,
            "gpuTypeIds": ["NVIDIA H100 80GB HBM3"], "containerDiskInGb": 60,
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


def uploads(size: str) -> list[str]:
    files = sorted(str(p.relative_to(ROOT)) for p in (ROOT / INPUTS).glob("*.npz"))
    return [*files, PLAN, f"data/corpus/timelocked_lm/runs/{size}/model.pt"]


def step(s: dict, issue: int, cap: float, size: str) -> bool:
    ph = s["phase"]
    work = f"data/corpus/alm/candidates/{size}"
    result = f"data/benchmark/alm_candidates_{size}.json"
    if s.get("pod") and sp.spend(s) > cap:
        sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
        event(s, f"**stopped at the ${cap:.0f} cap** (est. ${sp.spend(s):.2f}).", issue)
        s["phase"] = "capped"
        sp.save(s)
        return False
    if ph == "create":
        create(s)
        event(s, f"{size} candidate-model pod `{s['pod']}` created (Secure H100).", issue)
        s["phase"] = "setup"
    elif ph == "setup":
        if not sp.wait_ssh(s):
            sp.pw.rest("DELETE", f"/pods/{s['pod']}")
            event(s, "pod not reachable; terminated.", issue)
            return False
        for c in ["apt-get update -qq && apt-get install -y -qq rsync tmux > /dev/null",
                  f"git clone -q {sp.REPO} {R} || (cd {R} && git pull -q)",
                  "pip install -q 'pyarrow<18' tokenizers pyyaml scipy scikit-learn"]:  # fmt: skip
            rc, out = sp.remote(c, 1800)
            if rc != 0:
                event(s, f"setup failed on `{c[:50]}`: {out[-300:]}", issue)
                return False
        s["phase"] = "upload"
    elif ph == "upload":
        names = uploads(size)
        lst = sp.STATE.parent / "files.txt"
        lst.write_text("\n".join(names) + "\n")
        rc, out = sp.pw.sh(["rsync", "-rtR", "--no-o", "--no-g", f"--files-from={lst}", ".",
                            f"{sp.SSH}:{R}/"], 7200)  # fmt: skip
        if rc != 0:
            sp.log(f"upload failed ({out[-200:]}); retrying")
            return True
        sums = sp.STATE.parent / "sha256.txt"
        sums.write_text("".join(f"{sp.sha(ROOT / n)}  {n}\n" for n in names))
        sp.pw.sh(["rsync", str(sums), f"{sp.SSH}:{R}/sha256.txt"])
        rc, out = sp.remote(f"cd {R} && sha256sum -c --quiet sha256.txt && echo ALLOK", 3600)
        if "ALLOK" not in out:
            sp.log(f"checksums failed: {out[-300:]}; re-uploading")
            return True
        event(s, f"upload verified ({len(names)} files, SHA-256).", issue)
        s["phase"], s["restarts"] = "run", s.get("restarts", 0)
    elif ph == "run":
        script = (f"python -m alm.candidates train {size} --micro-batch 8 && python -m "
                  f"alm.candidates validate {size} && touch /workspace/CAND_DONE")  # fmt: skip
        sp.remote(f"cd {R} && tmux new-session -d -s cand '({script}) 2>&1 | tee -a "
                  "/workspace/cand.out'")  # fmt: skip
        event(s, f"**{size} candidate and control models training.**", issue)
        s["phase"] = "watch"
    elif ph == "watch":
        probe = (
            "ls /workspace/CAND_DONE 2>/dev/null; tmux has-session -t cand 2>/dev/null "
            "&& echo ALIVE; tail -n 40 /workspace/cand.out"
        )
        rc, out = sp.remote(probe)
        if "CAND_DONE" in out:
            s["phase"] = "fetch"
        elif rc == 0 and "ALIVE" not in out:
            (sp.STATE.parent / "cand_tail.log").open("a").write(f"--- {time.ctime()}\n{out}\n")
            if s["restarts"] >= 3:
                event(s, f"jobs died 3 times; stopping the pod. `{out.strip()[-300:]}`", issue)
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
        (ROOT / work).mkdir(parents=True, exist_ok=True)
        rc, _ = sp.pw.sh(["rsync", "-rt", "--partial", f"{sp.SSH}:{R}/{work}/", str(ROOT / work)],
                         7200)  # fmt: skip
        rc2, _ = sp.pw.sh(["rsync", "-rt", f"{sp.SSH}:{R}/{result}", str(ROOT / result)])
        rc3, out = sp.remote(f"cd {R} && sha256sum {result} {work}/*")
        if rc or rc2 or rc3:
            sp.log("fetch failed; retrying")
            return True
        for ln in out.splitlines():
            digest, name = ln.split(maxsplit=1)
            if sp.sha(ROOT / name) != digest:
                sp.log(f"fetch of {name} not verified; retrying")
                return True
        event(s, f"results and {len(out.splitlines()) - 1} unit files home, SHA-256 verified "
                 f"(`{result}`, `{work}/`).", issue)  # fmt: skip
        s["phase"] = "cleanup"
    elif ph == "cleanup":
        sp.remote(f"rm -rf {R}/data/corpus {R}/{PLAN} {R}/sha256.txt /workspace/cand.out")
        rc, out = sp.remote(f"ls {R}/data/corpus 2>/dev/null | wc -l")
        if rc != 0 or out.strip() != "0":
            return True
        sp.pw.rest("DELETE", f"/pods/{s['pod']}")
        event(s, f"inputs, weights and model deleted from the pod (checked); pod **terminated**. "
                 f"Est. spend ${sp.spend(s):.2f}.", issue)  # fmt: skip
        s["phase"] = "done"
        sp.save(s)
        return False
    sp.save(s)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--size", choices=["base", "large"], required=True)
    ap.add_argument("--cap", type=float, default=25.0)
    a = ap.parse_args(argv)
    configure(a.size)
    if not (ROOT / PLAN).exists():
        raise SystemExit(f"{PLAN} missing: run python -m alm.candidates plan first")
    sp.STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(sp.STATE.read_text()) if sp.STATE.exists() else {"phase": "create"}
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a.issue, a.cap, a.size):
                break
        except Exception as e:  # noqa: BLE001 -- transient API or network failure; retry
            sp.log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
