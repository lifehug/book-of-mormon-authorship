#!/usr/bin/env python3
"""Run any list of resumable jobs on a rented Secure H100 (owner, 2026-11-06: every model size
runs every test; the 297M and 1B runs need an H100, the Mac swaps).

Resumable state machine under tmux on the Mac, as ``alm_pod.py`` and ``candidates_pod.py``:
create a Secure Cloud pod -> set it up (clone this repo at the pushed commit) -> upload the listed
files (licensed text among them), every file's SHA-256 checked on the pod -> run the jobs in
order in tmux on the pod -> copy the ``--fetch`` paths home, every file's SHA-256 checked ->
delete ``data/corpus``, ``data/private`` and every uploaded file from the pod, check -> terminate.

A job is restarted (all jobs rerun in order, each resuming from what it saved; at most 3 times)
only when the pod answers over SSH and the job is confirmed gone; an unreachable pod says nothing
about the job and is left alone, reported hourly (2026-11-06: an SSH outage read as three crashes
stopped the 1B mid-run). The last 40 lines of output are kept on every restart. At the cap the pod
is stopped, not terminated, and the owner is asked. State: ``logs/pod_jobs_<name>/``.

Usage::

    python scripts/pod_jobs.py --name <name> --issue <n> --files <list> [--extra <path> ...] \\
        --jobs "<cmd>" ["<cmd>" ...] --fetch <path> [<path> ...] [--cap 25 --disk 100]
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import style_pod as sp  # noqa: E402

R = sp.R
DONE = "/workspace/JOBS_DONE"
OUTFILE = "/workspace/jobs.out"


def configure(name: str) -> None:
    safe = re.sub(r"[^a-z0-9]+", "", name.lower())
    sp.STATE = ROOT / f"logs/pod_jobs_{name}/state.json"
    sp.SSH = f"podjobs{safe}"
    sp.POD_NAME = f"bom-{name}".replace("_", "-")[:40]


def expand(paths: list[str], root: Path = ROOT) -> list[str]:
    """Repo-relative files: each listed file, and every file under each listed directory."""
    out: set[str] = set()
    for p in paths:
        q = root / p
        if q.is_dir():
            out |= {str(f.relative_to(root)) for f in q.rglob("*") if f.is_file()}
        elif q.is_file():
            out.add(p)
        else:
            raise SystemExit(f"listed path missing: {p}")
    return sorted(out)


def job_script(jobs: list[str], marker: str = DONE) -> str:
    """The jobs in order, stopping at the first failure; the marker only if all succeed."""
    return " && ".join([*jobs, f"touch {marker}"])


def unreachable(rc: int, out: str) -> bool:
    """The Mac could not reach the pod (ssh's own failure), which says nothing about the job."""
    if rc == 255:
        return True
    low = out.lower()
    return rc != 0 and any(s in low for s in ("timed out", "connection refused",
                                              "connection closed", "no route to host",
                                              "could not resolve"))  # fmt: skip


def classify(rc: int, out: str) -> str:
    """'unreachable', 'done', 'alive' or 'dead' from the watch probe's exit code and output."""
    if unreachable(rc, out):
        return "unreachable"
    if "JOBS_DONE" in out:
        return "done"
    if "ALIVE" in out:
        return "alive"
    return "dead" if rc == 0 else "unreachable"


def parse_sums(out: str) -> dict[str, str]:
    """``sha256sum`` lines -> {repo-relative path: digest}."""
    got = {}
    for ln in out.splitlines():
        parts = ln.split(maxsplit=1)
        if len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            got[parts[1].lstrip("*").strip()] = parts[0]
    return got


def event(s: dict, msg: str, issue: int) -> None:
    sp.log(msg)
    s.setdefault("events", []).append(f"{time.strftime('%F %T')} {msg}")
    sp.save(s)
    sp.pw.sh(["gh", "issue", "comment", str(issue), "-b", f"Pod `{s['name']}`: {msg}"], 120)


def create(s: dict, disk: int) -> None:
    body = {"name": sp.POD_NAME, "imageName": sp.IMAGE, "cloudType": "SECURE", "gpuCount": 1,
            "gpuTypeIds": ["NVIDIA H100 80GB HBM3"], "containerDiskInGb": 60,
            "volumeInGb": disk, "volumeMountPath": "/workspace", "ports": ["22/tcp"]}  # fmt: skip
    req = urllib.request.Request("https://rest.runpod.io/v1/pods", method="POST",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {sp.pw._token()}",
                                          "Content-Type": "application/json",
                                          "User-Agent": sp.pw.UA})  # fmt: skip
    with urllib.request.urlopen(req, timeout=120) as r:
        pod = json.loads(r.read())
    s["pod"], s["created"] = pod["id"], time.time()
    sp.save(s)


def step(s: dict, a: argparse.Namespace) -> bool:
    ph, issue = s["phase"], a.issue
    if s.get("pod") and sp.spend(s) > a.cap:
        sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
        event(s, f"**stopped at the ${a.cap:.0f} cap** (est. ${sp.spend(s):.2f}).", issue)
        s["phase"] = "capped"
        sp.save(s)
        return False
    if ph == "create":
        create(s, a.disk)
        event(s, f"pod `{s['pod']}` created (Secure H100) for {len(a.jobs)} job(s).", issue)
        s["phase"] = "setup"
    elif ph == "setup":
        if not sp.wait_ssh(s):
            sp.pw.rest("DELETE", f"/pods/{s['pod']}")
            event(s, "pod not reachable after creation; terminated.", issue)
            return False
        pip = "pip install -q 'pyarrow<18' tokenizers pyyaml scipy scikit-learn joblib"
        for c in ["apt-get update -qq && apt-get install -y -qq rsync tmux > /dev/null",
                  f"git clone -q {sp.REPO} {R} || (cd {R} && git pull -q)", pip]:  # fmt: skip
            rc, out = sp.remote(c, 1800)
            if rc != 0:
                event(s, f"setup failed on `{c[:50]}`: {out[-300:]}", issue)
                return False
        s["phase"] = "upload"
    elif ph == "upload":
        names = s["uploads"]
        lst = sp.STATE.parent / "files.txt"
        lst.write_text("\n".join(names) + "\n")
        sp.b2_prefetch(names)  # models from B2 first; rsync then skips or fixes them
        rc, out = sp.pw.sh(["rsync", "-rtLR", "--no-o", "--no-g", f"--files-from={lst}", ".",
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
        script = job_script(a.jobs)
        sp.remote(f"cd {R} && rm -f {DONE} && tmux new-session -d -s jobs "
                  f"{shlex.quote(f'({script}) 2>&1 | tee -a {OUTFILE}')}")  # fmt: skip
        event(s, "**jobs started**: " + "; ".join(f"`{j}`" for j in a.jobs), issue)
        s["phase"] = "watch"
    elif ph == "watch":
        rc, out = sp.remote(f"ls {DONE} 2>/dev/null; tmux has-session -t jobs 2>/dev/null && "
                            f"echo ALIVE; tail -n 40 {OUTFILE}")  # fmt: skip
        state = classify(rc, out)
        if state == "unreachable":
            s["unreachable"] = s.get("unreachable", 0) + 1
            if s["unreachable"] % 30 == 1:  # every hour at 2-minute checks
                event(s, f"pod unreachable over SSH ({s['unreachable']} checks); jobs left "
                         "alone, retrying.", issue)  # fmt: skip
        elif state == "done":
            s["unreachable"] = 0
            s["phase"] = "fetch"
            sp.save(s)
            return True
        elif state == "dead":
            with (sp.STATE.parent / "tail.log").open("a") as f:
                f.write(f"--- {time.ctime()}\n{out}\n")
            if s["restarts"] >= 3:
                # nothing worth keeping on the pod: delete the text and terminate, never leave
                # licensed text on a stopped pod's disk (2026-11-06)
                event(s, f"jobs died 3 times; cleaning up and terminating. "
                         f"`{out.strip()[-300:]}`", issue)  # fmt: skip
                s["failed"], s["phase"] = True, "cleanup"
                sp.save(s)
                return True
            s["restarts"] += 1
            s["phase"] = "run"
            sp.log(f"jobs gone; restarting ({s['restarts']}/3). Last: {out.strip()[-200:]}")
            sp.save(s)
            return True
        else:
            s["unreachable"] = 0
        sp.save(s)
        time.sleep(120)
    elif ph == "fetch":
        s["fetch_tries"] = s.get("fetch_tries", 0) + 1
        if s["fetch_tries"] > 20:  # a path that never appears must not keep the pod billing
            event(s, "fetch failed 20 times; stopping the pod for the owner.", issue)
            sp.pw.rest("POST", f"/pods/{s['pod']}/stop")
            return False
        for p in a.fetch:
            rc, out = sp.pw.sh(["rsync", "-rtR", "--partial", f"{sp.SSH}:{R}/./{p}", str(ROOT)],
                               7200)  # fmt: skip
            if rc != 0:
                sp.log(f"fetch of {p} failed ({out[-200:]}); retrying")
                return True
        quoted = " ".join(shlex.quote(p) for p in a.fetch)
        rc, out = sp.remote(f"cd {R} && find {quoted} -type f -print0 | xargs -0 sha256sum", 3600)
        got = parse_sums(out)
        if rc != 0 or not got:
            sp.log(f"remote checksums failed ({out[-200:]}); retrying")
            return True
        bad = [n for n, d in got.items() if not (ROOT / n).exists() or sp.sha(ROOT / n) != d]
        if bad:
            sp.log(f"fetch not verified for {len(bad)} file(s), e.g. {bad[0]}; retrying")
            return True
        event(s, f"{len(got)} result file(s) home, SHA-256 verified: "
                 + ", ".join(f"`{p}`" for p in a.fetch), issue)  # fmt: skip
        s["phase"] = "cleanup"
    elif ph == "cleanup":
        # uploads under data/corpus or data/private go with those folders; list only the rest
        # (26,508 token files once made the command too long for ssh, 2026-11-07)
        rest = [n for n in s["uploads"] if not n.startswith(("data/corpus/", "data/private/"))]
        listed = " ".join(shlex.quote(n) for n in rest)
        sp.remote(f"cd {R} && rm -rf data/corpus data/private {listed} sha256.txt {OUTFILE}")
        rc, out = sp.remote(f"cd {R} && ls -d data/corpus data/private {listed} 2>/dev/null "
                            "| wc -l")  # fmt: skip
        if rc != 0 or out.strip() != "0":
            return True
        sp.pw.rest("DELETE", f"/pods/{s['pod']}")
        event(s, f"text and models deleted from the pod (checked); pod **terminated**. "
                 f"Est. spend ${sp.spend(s):.2f}.", issue)  # fmt: skip
        s["phase"] = "failed" if s.get("failed") else "done"
        sp.save(s)
        return False
    sp.save(s)
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--name", required=True)
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--files", type=Path, help="a file listing repo-relative paths, one a line")
    ap.add_argument("--extra", nargs="*", default=[], help="more repo-relative paths")
    ap.add_argument("--jobs", nargs="+", required=True)
    ap.add_argument("--fetch", nargs="+", required=True)
    ap.add_argument("--cap", type=float, default=25.0)
    ap.add_argument("--disk", type=int, default=100, help="pod volume, GB")
    a = ap.parse_args(argv)
    configure(a.name)
    sp.STATE.parent.mkdir(parents=True, exist_ok=True)
    s = json.loads(sp.STATE.read_text()) if sp.STATE.exists() else {"phase": "create"}
    if "uploads" not in s:
        listed = [ln.strip() for ln in a.files.read_text().splitlines()] if a.files else []
        s["uploads"] = expand([p for p in [*listed, *a.extra] if p])
        s["name"] = a.name
        sp.save(s)
    while s["phase"] not in ("done", "failed", "capped"):
        try:
            if not step(s, a):
                break
        except Exception as e:  # noqa: BLE001 -- transient API or network failure; retry
            sp.log(f"error in {s['phase']}: {e}; retrying in 60 s")
            time.sleep(60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
