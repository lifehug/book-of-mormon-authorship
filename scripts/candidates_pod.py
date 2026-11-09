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

``--blind`` (BOM-32, 2026-11-08): after training and validating, and before the weights come home
(about 36 GB for the 590M), the same pod also scores the sealed set: it uploads
``data/corpus/blind/sealed.jsonl`` and ``data/blind/withheld.json`` (SHA-256 checked), adds this
size's thresholds (``blind.thresholds <size>``, merged by size), runs ``blind.run --only alm
--sizes <size>``, and the thresholds entry, the output file and its manifest entry come home and
are merged into the Mac's files (other sizes and methods untouched), every hash checked. The pod
never has the key. The weights follow afterwards and are kept.

Usage::

    python scripts/candidates_pod.py --issue 38 --size pilot|base|mid|large [--cap 25 --blind]
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
sys.path.insert(0, str(ROOT))
import style_pod as sp  # noqa: E402

R = sp.R
INPUTS = "data/corpus/alm/candidates/inputs"
PLAN = "data/benchmark/alm_candidates_plan.json"
SEALED = "data/corpus/blind/sealed.jsonl"
WITHHELD = "data/blind/withheld.json"
BLIND_TH = "data/blind/thresholds.json"
BLIND_MANIFEST = "data/blind/outputs.json"


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


def blind_merge(size: str, pod_th: dict, pod_manifest: dict, out_rel: str,
                root: Path = ROOT) -> None:  # fmt: skip
    """Merge the pod's results into the Mac's thresholds and output manifest, by size and file:
    nothing else in either file changes."""
    from blind.run import merge
    from blind.thresholds import add_size

    local = json.loads((root / BLIND_TH).read_text())
    (root / BLIND_TH).write_text(json.dumps(add_size(local, pod_th, size), indent=1) + "\n")
    merge(root / BLIND_MANIFEST, {out_rel: pod_manifest["sha256"][out_rel]}, ["alm"], [size])


def step(s: dict, issue: int, cap: float, size: str, blind: bool = False) -> bool:
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
        sp.b2_prefetch(names)  # models from B2 first; rsync then skips or fixes them
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
            s["phase"] = "blind_upload" if blind and not s.get("blind_home") else "fetch"
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
    elif ph == "blind_upload":
        if not (ROOT / SEALED).exists():
            event(s, f"`{SEALED}` missing on the Mac; blind stage skipped.", issue)
            s["phase"] = "fetch"
            return True
        rc, out = sp.pw.sh(["rsync", "-rtR", "--no-o", "--no-g", SEALED, WITHHELD,
                            f"{sp.SSH}:{R}/"], 3600)  # fmt: skip
        sums = sp.STATE.parent / "blind_sha256.txt"
        sums.write_text("".join(f"{sp.sha(ROOT / n)}  {n}\n" for n in (SEALED, WITHHELD)))
        sp.pw.sh(["rsync", str(sums), f"{sp.SSH}:{R}/blind_sha256.txt"])
        rc2, out2 = sp.remote(f"cd {R} && sha256sum -c --quiet blind_sha256.txt && echo BLINDOK")
        if rc or "BLINDOK" not in out2:
            sp.log(f"blind upload not verified ({(out + out2)[-200:]}); retrying")
            return True
        event(s, "sealed set and withheld spans on the pod (SHA-256 checked; no key).", issue)
        s["phase"], s["blind_restarts"] = "blind_run", s.get("blind_restarts", 0)
    elif ph == "blind_run":
        script = (f"python -m blind.thresholds {size} && python -m blind.run --only alm "
                  f"--sizes {size} && touch /workspace/BLIND_DONE")  # fmt: skip
        sp.remote(f"cd {R} && tmux new-session -d -s blind '({script}) 2>&1 | tee -a "
                  "/workspace/blind.out'")  # fmt: skip
        event(s, f"**{size} blind ALM scoring started** on the pod.", issue)
        s["phase"] = "blind_watch"
    elif ph == "blind_watch":
        probe = ("ls /workspace/BLIND_DONE 2>/dev/null; tmux has-session -t blind 2>/dev/null "
                 "&& echo ALIVE; tail -n 40 /workspace/blind.out")  # fmt: skip
        rc, out = sp.remote(probe)
        if "BLIND_DONE" in out:
            s["phase"] = "blind_fetch"
        elif rc == 0 and "ALIVE" not in out:
            (sp.STATE.parent / "blind_tail.log").open("a").write(f"--- {time.ctime()}\n{out}\n")
            if s["blind_restarts"] >= 3:
                event(s, f"blind scoring died 3 times; fetching the weights anyway. "
                         f"`{out.strip()[-300:]}`", issue)  # fmt: skip
                s["phase"] = "fetch"
                return True
            s["blind_restarts"] += 1
            s["phase"] = "blind_run"
        else:
            sp.save(s)
            time.sleep(60)
            return True
    elif ph == "blind_fetch":
        here = sp.STATE.parent
        out_rel = f"data/blind/outputs/alm_{size}.json"
        (ROOT / "data/blind/outputs").mkdir(parents=True, exist_ok=True)
        pairs = [(BLIND_TH, here / "thresholds.pod.json"),
                 (BLIND_MANIFEST, here / "outputs.pod.json"),
                 (out_rel, ROOT / out_rel), (result, ROOT / result)]  # fmt: skip
        got = [sp.pw.sh(["rsync", "-t", f"{sp.SSH}:{R}/{a}", str(b)])[0] for a, b in pairs]
        rc, sums = sp.remote(f"cd {R} && sha256sum {out_rel} {result}")
        if any(got) or rc:
            sp.log("blind fetch failed; retrying")
            return True
        for ln in sums.splitlines():
            digest, name = ln.split(maxsplit=1)
            if sp.sha(ROOT / name) != digest:
                sp.log(f"blind fetch of {name} not verified; retrying")
                return True
        pod_manifest = json.loads((here / "outputs.pod.json").read_text())
        if pod_manifest["sha256"].get(out_rel) != sp.sha(ROOT / out_rel):
            sp.log("the pod's manifest does not match the fetched output; retrying")
            return True
        pod_th = json.loads((here / "thresholds.pod.json").read_text())
        blind_merge(size, pod_th, pod_manifest, out_rel)
        s["blind_home"] = True
        event(s, f"**{size} blind ALM scores home**, SHA-256 verified, merged into `{BLIND_TH}` "
                 f"and `{BLIND_MANIFEST}`: commit them, then unblind. Weights follow.",
              issue)  # fmt: skip
        s["phase"] = "fetch"
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
        sp.remote(f"rm -rf {R}/data/corpus {R}/{PLAN} {R}/sha256.txt /workspace/cand.out "
                  "/workspace/blind.out")  # fmt: skip
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
    ap.add_argument("--size", choices=["pilot", "base", "mid", "large"], required=True)
    ap.add_argument("--cap", type=float, default=25.0)
    ap.add_argument("--blind", action="store_true", help="also score the sealed set (BOM-32)")
    a = ap.parse_args(argv)
    configure(a.size)
    if not (ROOT / PLAN).exists():
        raise SystemExit(f"{PLAN} missing: run python -m alm.candidates plan first")
    sp.STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(sp.STATE.read_text()) if sp.STATE.exists() else {"phase": "create"}
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a.issue, a.cap, a.size, a.blind):
                break
        except Exception as e:  # noqa: BLE001 -- transient API or network failure; retry
            sp.log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
