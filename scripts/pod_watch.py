"""Watch the rented GPU run (BOM-27) and the Mac's long jobs; act on what it sees; report on GitHub.

Runs on the Mac mini under tmux, independent of any Claude session. Every ``--every`` seconds:

* **upload** -- the token files are going up (tmux ``podupload``). When that session ends, every
  file's size and SHA-256 on the pod is checked against
  ``data/manifests/timelocked_lm_tokens.jsonl``; a short or missing file restarts the upload.
  Training never starts on a partial set.
* **pilot**, then **base** -- ``timelocked_lm.train`` in tmux ``train`` on the pod. A dead or
  stalled run (log silent for ``--stall-minutes``) is restarted and resumes from its checkpoint;
  more than three restarts in three hours stops the automation and reports. The checkpoint is
  copied home every ``--backup-hours``. When a run prints ``done:``, its model, log and run record
  come home (checksum-verified) and the next size starts.
* **cleanup** -- the licensed token files are deleted from the pod, the deletion is verified, and
  the pod is terminated. Only the models, logs and run records were ever copied back.

Spend guard: if this account's balance has fallen by more than ``--cap`` dollars since the watcher
first started, the pod is stopped (its disk kept) and the watcher reports and waits.

Reporting: the body of the GitHub status issue is rewritten every ``--report-minutes`` (pod,
training progress and ETA, spend, the Mac's index); a comment is added on every event and every
``--summary-hours``. State is in ``logs/pod_watch/state.json``, so a restarted watcher carries on.

Usage::

    python scripts/pod_watch.py --pod <id> --issue <number>     # under tmux, on the Mac
    python scripts/pod_watch.py --pod <id> --issue <number> --once
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "logs/pod_watch"
STATE = STATE_DIR / "state.json"
LOG = STATE_DIR / "watch.log"
MANIFEST = ROOT / "data/manifests/timelocked_lm_tokens.jsonl"
HOME_RUNS = ROOT / "data/corpus/timelocked_lm/runs"
TOKEN = Path.home() / ".config/runpod/token"
SSH = "bompod"
REMOTE_TOKENS = "/workspace/corpus/timelocked_lm/tokens"
REMOTE_REPO = "/workspace/repo"
REMOTE_RUNS = "/workspace/runs"
REMOTE_SEM = "/workspace/semantic"
HOME_INDEX = ROOT / "data/corpus/semantic/index"
STAGING = ROOT / "data/corpus/semantic/index_gpu_staging"
INDEX_SHARDS = 255  # pack files (BOM-25 GPU share: 241, then 14 of the Mac's Harvard tail)
UPLOAD_SESSION = "podupload"
UPLOAD_SCRIPT = ROOT / "scripts/pod_upload.sh"
BATCH_TOKENS = 524_288
MICRO = 64
UA = "bom-authorship-pod-watch/1.0 (github.com/lifehug/book-of-mormon-authorship)"
ORDER = ["upload", "pilot", "base", "cleanup", "finished"]


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def log(msg: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a") as f:
        f.write(line + "\n")


def load_state(pod: str) -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"pod": pod, "phase": "upload", "events": [], "restarts": [], "started": time.time()}


def save_state(s: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1) + "\n")
    tmp.replace(STATE)


# ---- RunPod -------------------------------------------------------------------------------------


def _token() -> str:
    return TOKEN.read_text().strip()


def rest(method: str, path: str) -> dict:
    req = urllib.request.Request(f"https://rest.runpod.io/v1{path}", method=method,
                                 headers={"Authorization": f"Bearer {_token()}",
                                          "User-Agent": UA})  # fmt: skip
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read()
    return json.loads(body) if body else {}


def balance() -> float | None:
    q = json.dumps({"query": "query { myself { clientBalance currentSpendPerHr } }"}).encode()
    req = urllib.request.Request("https://api.runpod.io/graphql", data=q, method="POST",
                                 headers={"Authorization": f"Bearer {_token()}",
                                          "Content-Type": "application/json",
                                          "User-Agent": UA})  # fmt: skip
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return float(json.loads(r.read())["data"]["myself"]["clientBalance"])
    except Exception as e:  # noqa: BLE001 -- a reporting read; never fatal
        log(f"balance read failed: {e}")
        return None


# ---- shell helpers -------------------------------------------------------------------------------


def sh(cmd: list[str], timeout: int = 600) -> tuple[int, str]:
    if cmd and cmd[0] == "rsync" and not any(c.startswith("--timeout") for c in cmd):
        # a dropped connection otherwise hangs rsync until the outer timeout (2026-11-06: an hour)
        cmd = [cmd[0], "--timeout=120", *cmd[1:]]
    if cmd and cmd[0] == "rsync" and "--keep-dirlinks" not in cmd:
        # without it a fetch with -R replaces the data/corpus symlink (to the external drive) with
        # a real folder: every job then looked in an empty directory (2026-11-07)
        cmd = [cmd[0], "--keep-dirlinks", *cmd[1:]]
    if cmd and cmd[0] == "ssh" and "ServerAliveInterval" not in " ".join(cmd):
        cmd = [cmd[0], "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=4", *cmd[1:]]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def remote(cmd: str, timeout: int = 600) -> tuple[int, str]:
    return sh(["ssh", "-o", "ConnectTimeout=30", "-o", "BatchMode=yes", SSH, cmd], timeout)


def local_tmux_alive(name: str) -> bool:
    return sh(["tmux", "has-session", "-t", f"={name}"])[0] == 0


# ---- phases --------------------------------------------------------------------------------------


def manifest() -> dict[str, dict]:
    return {r["path"]: r for r in map(json.loads, MANIFEST.read_text().splitlines())}


def verify_upload() -> tuple[bool, str]:
    want = manifest()
    rc, out = remote(f"cd {REMOTE_TOKENS} && sha256sum * 2>/dev/null", timeout=3600)
    if rc not in (0, 1):
        return False, f"sha256sum failed ({rc}): {out[-200:]}"
    have = {}
    for ln in out.splitlines():
        parts = ln.split(None, 1)
        if len(parts) == 2:
            have[parts[1].strip()] = parts[0]
    bad = [p for p, r in want.items() if have.get(p) != r["sha256"]]
    return not bad, f"{len(want) - len(bad)}/{len(want)} files verified" + (
        f"; first mismatch {bad[0]}" if bad else ""
    )


def train_cmd(size: str) -> str:
    out = f"{REMOTE_RUNS}/{size}"
    return (f"mkdir -p {out} && tmux new-session -d -s train 'cd {REMOTE_REPO} && "
            f"python -m timelocked_lm.train {size} --out {out} --micro-batch {MICRO} "
            f">> {out}/train.out 2>&1'")  # fmt: skip


def progress(size: str) -> dict:
    """Last log record, steps planned, tokens/s over the recent records."""
    out = f"{REMOTE_RUNS}/{size}"
    rc, txt = remote(f"tail -n 400 {out}/log.jsonl 2>/dev/null; echo ===; "
                     f"cat {out}/run.json 2>/dev/null; echo ===; tail -c 2000 {out}/train.out "
                     f"2>/dev/null; echo ===; stat -c %Y {out}/log.jsonl 2>/dev/null; date +%s; "
                     f"tmux has-session -t =train 2>/dev/null && echo ALIVE")  # fmt: skip
    if rc != 0 and "===" not in txt:
        return {"reachable": False, "error": txt[-300:]}
    parts = txt.split("===")
    recs = [json.loads(x) for x in parts[0].splitlines() if x.startswith("{")]
    try:
        run = json.loads(parts[1]) if parts[1].strip() else {}
    except json.JSONDecodeError:
        run = {}
    tail = parts[2] if len(parts) > 2 else ""
    rest_lines = (parts[3] if len(parts) > 3 else "").split()
    mtime = int(rest_lines[0]) if len(rest_lines) >= 2 and rest_lines[0].isdigit() else None
    clock = int(rest_lines[1]) if len(rest_lines) >= 2 and rest_lines[1].isdigit() else None
    p = {"reachable": True, "alive": "ALIVE" in txt, "done": "done:" in tail,
         "steps": run.get("steps"), "tail": tail[-400:]}  # fmt: skip
    if mtime and clock:
        p["silent_minutes"] = (clock - mtime) / 60
    if recs:
        last = recs[-1]
        p["step"] = last["step"]
        p["loss"] = last["loss"]
        vals = [r for r in recs if "val_loss" in r]
        if vals:
            p["val_loss"], p["val_step"] = vals[-1]["val_loss"], vals[-1]["step"]
        # records since the last resume (``sec`` restarts from zero when the trainer resumes)
        k = len(recs) - 1
        while k > 0 and recs[k - 1]["sec"] <= recs[k]["sec"]:
            k -= 1
        span = recs[k:]
        if len(span) > 20 and last["sec"] > span[0]["sec"]:
            first = span[0]
            p["tokens_per_s"] = (
                (last["step"] - first["step"]) * BATCH_TOKENS / (last["sec"] - first["sec"])
            )
            if p.get("steps"):
                p["eta_hours"] = (
                    (p["steps"] - last["step"]) * BATCH_TOKENS / p["tokens_per_s"] / 3600
                )
    return p


def fetch(size: str, names: list[str]) -> tuple[bool, str]:
    """Copy run files home and check each file's SHA-256 against the pod's."""
    dest = HOME_RUNS / size
    dest.mkdir(parents=True, exist_ok=True)
    rc, out = sh(["rsync", "-rt", "--partial", *[f"{SSH}:{REMOTE_RUNS}/{size}/{n}" for n in names],
                  str(dest) + "/"], timeout=7200)  # fmt: skip
    if rc != 0:
        return False, f"rsync {rc}: {out[-300:]}"
    # log.jsonl is still being appended to, so compare only the bytes that were copied
    n = (dest / "log.jsonl").stat().st_size if "log.jsonl" in names else 0
    cmd = " ; ".join(
        f"head -c {n} {REMOTE_RUNS}/{size}/{x} | sha256sum | sed 's|-$|{x}|'"
        if x == "log.jsonl"
        else f"sha256sum {REMOTE_RUNS}/{size}/{x}"
        for x in names
    )
    rc, out = remote(cmd)
    if rc != 0:
        return False, f"remote sha256sum {rc}: {out[-300:]}"
    for ln in out.splitlines():
        digest, path = ln.split(None, 1)
        local = dest / Path(path.strip()).name
        h = hashlib.sha256()
        with local.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            return False, f"checksum mismatch on {local.name}"
    return True, f"{len(names)} files home in {dest.relative_to(ROOT)}"


def index_sync(s: dict, issue: int | None) -> str:
    """Bring finished GPU index shards home (BOM-25): vectors and ids, checksum-verified, the
    ``.done`` marker moved in last; once all are home, delete the passage text from the pod."""
    if s.get("index_home_complete"):
        return f"all {INDEX_SHARDS} GPU shards home; passage text deleted from the pod"
    gpu = f"{REMOTE_SEM}/index_gpu"
    rc, out = remote(f"ls {gpu}/ 2>/dev/null | grep -c 'shard_p.*done'; "
                     f"grep -c INDEX_GPU_COMPLETE {gpu}.log 2>/dev/null")  # fmt: skip
    if rc not in (0, 1):
        return "pod not reachable"
    nums = out.split()
    pod_done = int(nums[0]) if nums and nums[0].isdigit() else 0
    complete = len(nums) > 1 and nums[1].isdigit() and int(nums[1]) > 0
    home = {d.stem for d in HOME_INDEX.glob("shard_p*.done")}
    rc, listing = remote(f"cd {REMOTE_SEM}/index_gpu && ls shard_p*.done 2>/dev/null")
    todo = [x[:-5] for x in listing.split() if x.endswith(".done") and x[:-5] not in home]
    brought = 0
    t0 = time.time()
    for stem in todo:
        if time.time() - t0 > 1200:  # leave room for the rest of the tick
            break
        STAGING.mkdir(parents=True, exist_ok=True)
        files = [f"{stem}.npy", f"{stem}.parquet", f"{stem}.done"]
        rc, msg = sh(["rsync", "-rt", "--partial",
                      *[f"{SSH}:{REMOTE_SEM}/index_gpu/{f}" for f in files], str(STAGING) + "/"],
                     timeout=3600)  # fmt: skip
        if rc != 0:
            log(f"index shard {stem}: rsync {rc}")
            break
        rc, sums = remote(f"cd {REMOTE_SEM}/index_gpu && sha256sum {stem}.npy {stem}.parquet")
        ok = rc == 0
        for ln in sums.splitlines() if ok else []:
            digest, name = ln.split(None, 1)
            h = hashlib.sha256()
            with (STAGING / name.strip()).open("rb") as f:
                for chunk in iter(lambda f=f: f.read(1 << 22), b""):
                    h.update(chunk)
            ok = ok and h.hexdigest() == digest
        if not ok:
            log(f"index shard {stem}: checksum mismatch; will retry")
            break
        for ext in (".npy", ".parquet", ".done"):  # the marker last, as the Mac's build does
            (STAGING / f"{stem}{ext}").replace(HOME_INDEX / f"{stem}{ext}")
        brought += 1
    home_n = len(list(HOME_INDEX.glob("shard_p*.done")))
    if brought:
        log(f"index: {brought} GPU shards home ({home_n}/{INDEX_SHARDS})")
    if complete and home_n >= INDEX_SHARDS:
        rc, out = remote(f"tmux kill-session -t =index 2>/dev/null; "
                         f"rm -rf {REMOTE_SEM}/pack {REMOTE_SEM}/checkonly && "
                         f"test ! -e {REMOTE_SEM}/pack && echo GONE")  # fmt: skip
        if "GONE" in out:
            s["index_home_complete"] = True
            event(s, f"**GPU index share finished**: all {INDEX_SHARDS} shards home and verified "
                     "in `data/corpus/semantic/index/`; passage text deleted from the pod "
                     "(verified).", issue)  # fmt: skip
    return f"pod {pod_done}/{INDEX_SHARDS} shards embedded, {home_n} home"


def mac_index() -> str:
    lg = ROOT / "logs/semantic_index.log"
    shards = len(list((ROOT / "data/corpus/semantic/index").glob("shard_*.done")))
    last = ""
    if lg.exists():
        lines = [x for x in lg.read_text().splitlines() if x.startswith("shard")]
        last = lines[-1] if lines else ""
    alive = local_tmux_alive("semantic_index")
    return f"{'running' if alive else 'NOT running'}; {shards} shards done; last: {last}"


# ---- the loop ------------------------------------------------------------------------------------


def event(s: dict, msg: str, issue: int | None) -> None:
    log(msg)
    s["events"].append([now(), msg])
    s["events"] = s["events"][-50:]
    if issue:
        sh(["gh", "issue", "comment", str(issue), "--body", f"**{now()}** {msg}"])


def restart_allowed(s: dict) -> bool:
    cut = time.time() - 3 * 3600
    s["restarts"] = [t for t in s["restarts"] if t > cut]
    return len(s["restarts"]) < 3


def tick(s: dict, a: argparse.Namespace) -> dict:
    info: dict = {"checked": now()}
    try:
        pod = rest("GET", f"/pods/{s['pod']}")
        info["pod_status"] = pod.get("desiredStatus")
        info["cost_per_hr"] = pod.get("costPerHr")
    except Exception as e:  # noqa: BLE001
        info["pod_status"] = f"API error: {e}"
        pod = {}
    bal = balance()
    if bal is not None:
        s.setdefault("balance_start", bal)
        info["balance"] = bal
        info["spent"] = s["balance_start"] - bal
        if info["spent"] > a.cap and s["phase"] in ("upload", "pilot", "base"):
            if not s.get("capped"):
                try:
                    rest("POST", f"/pods/{s['pod']}/stop")
                finally:
                    s["capped"] = True
                    event(s, f"Spend ${info['spent']:.0f} passed the ${a.cap:.0f} cap: pod "
                             "STOPPED (disk kept). Waiting for the owner.", a.issue)  # fmt: skip
            return info
    if s.get("capped") or s.get("halted"):
        return info
    phase = s["phase"]

    if phase == "upload":
        if local_tmux_alive(UPLOAD_SESSION):
            rc, out = remote(f"du -sm {REMOTE_TOKENS} | cut -f1")
            info["uploaded_mb"] = out if rc == 0 else "?"
        else:
            ok, msg = verify_upload()
            info["verify"] = msg
            if ok:
                event(s, f"Upload verified ({msg}). Starting the pilot.", a.issue)
                rc, out = remote(train_cmd("pilot"))
                s["phase"] = "pilot"
                s["phase_started"] = time.time()
                if rc != 0:
                    event(s, f"Pilot start failed: {out[-300:]}", a.issue)
            else:
                log(f"upload incomplete ({msg}); restarting upload")
                sh(["tmux", "new-session", "-d", "-s", UPLOAD_SESSION,
                    f"{UPLOAD_SCRIPT} >> {ROOT}/logs/pod_upload.log 2>&1"])  # fmt: skip

    elif phase in ("pilot", "base"):
        p = progress(phase)
        info["train"] = p
        if not p.get("reachable"):
            s["unreachable"] = s.get("unreachable", 0) + 1
            if s["unreachable"] == 3:
                event(s, f"Pod unreachable for 3 checks (status {info.get('pod_status')}): "
                         f"{p.get('error', '')[:200]}", a.issue)  # fmt: skip
                if info.get("pod_status") == "EXITED":
                    try:
                        rest("POST", f"/pods/{s['pod']}/start")
                        event(s, "Pod had exited; asked RunPod to start it again.", a.issue)
                    except Exception as e:  # noqa: BLE001
                        event(s, f"Pod start request failed: {e}", a.issue)
            return info
        s["unreachable"] = 0
        info["gpu_index"] = index_sync(s, a.issue)
        if p["done"]:
            names = ["model.pt", "log.jsonl", "run.json", "train.out"]
            ok, msg = fetch(phase, names)
            if not ok:
                event(s, f"{phase} finished but copying home failed ({msg}); will retry.", a.issue)
                return info
            nxt = "base" if phase == "pilot" else "cleanup"
            event(s, f"**{phase} finished** at step {p.get('step')}, val loss "
                     f"{p.get('val_loss', float('nan')):.4f}; {msg}."
                     + (" Starting the base model." if nxt == "base" else ""), a.issue)  # fmt: skip
            s["phase"], s["phase_started"] = nxt, time.time()
            s.pop("last_backup", None)
            if nxt == "base":
                rc, out = remote(train_cmd("base"))
                if rc != 0:
                    event(s, f"Base start failed: {out[-300:]}", a.issue)
            return info
        stalled = p.get("alive") and (p.get("silent_minutes") or 0) > a.stall_minutes
        if not p.get("alive") or stalled:
            why = f"log silent {p['silent_minutes']:.0f} min" if stalled else "process not running"
            if not restart_allowed(s):
                s["halted"] = True
                tail = p.get("tail", "")[-600:]
                event(s, f"{phase}: {why}, and 3 restarts in 3 h already. Automation halted; "
                         f"last output:\n```\n{tail}\n```", a.issue)  # fmt: skip
                return info
            s["restarts"].append(time.time())
            remote("tmux kill-session -t =train 2>/dev/null; true")
            rc, out = remote(train_cmd(phase))
            event(s, f"{phase}: {why}; restarted (resumes from checkpoint). "
                     f"Last output: `{p.get('tail', '')[-200:].strip()}`", a.issue)  # fmt: skip
            return info
        if time.time() - s.get("last_backup", s.get("phase_started", 0)) > a.backup_hours * 3600:
            ok, msg = fetch(phase, ["checkpoint.pt", "log.jsonl", "run.json"])
            s["last_backup"] = time.time()
            log(f"checkpoint backup: {msg}" if ok else f"checkpoint backup failed: {msg}")

    elif phase == "cleanup":
        info["gpu_index"] = index_sync(s, a.issue)
        if not s.get("index_home_complete"):
            log("cleanup waits for the GPU index shards to come home")
            return info
        rc, out = remote(f"rm -rf {REMOTE_TOKENS} /workspace/corpus {REMOTE_SEM} && "
                         f"test ! -e {REMOTE_TOKENS} && test ! -e {REMOTE_SEM} && "
                         f"echo GONE")  # fmt: skip
        if "GONE" not in out:
            event(s, f"Cleanup: could not verify the token files were deleted ({out[-200:]}); "
                     "pod left running for a look.", a.issue)  # fmt: skip
            s["halted"] = True
            return info
        try:
            rest("DELETE", f"/pods/{s['pod']}")
            event(s, "Token files and passage text deleted from the pod (verified) and the "
                     "pod **terminated**. "
                     f"Models are in `{HOME_RUNS.relative_to(ROOT)}/`.", a.issue)  # fmt: skip
            s["phase"] = "finished"
        except Exception as e:  # noqa: BLE001
            event(s, f"Pod terminate failed: {e}", a.issue)
    return info


def report(s: dict, info: dict, a: argparse.Namespace) -> str:
    t = info.get("train") or {}
    lines = [f"_Auto-updated by `scripts/pod_watch.py` on the Mac mini. Last check: "
             f"{info.get('checked')}._", "", "## GPU run (BOM-27 time-locked model)", "",
             "| | |", "| --- | --- |",
             f"| Phase | **{s['phase']}** ({' → '.join(ORDER)}) |",
             f"| Pod | `{s['pod']}`: {info.get('pod_status')}, "
             f"${info.get('cost_per_hr')}/h |"]  # fmt: skip
    if "uploaded_mb" in info:
        lines.append(f"| Uploaded | {info['uploaded_mb']} MB of ~49,300 MB |")
    if "verify" in info:
        lines.append(f"| Upload check | {info['verify']} |")
    if t.get("step"):
        pct = 100 * t["step"] / t["steps"] if t.get("steps") else 0
        lines.append(f"| Progress | step {t['step']:,} of {t.get('steps') or 0:,} ({pct:.1f}%) |")
        lines.append(
            f"| Loss | train {t.get('loss', 0):.3f}; validation "
            f"{t.get('val_loss', float('nan')):.3f} at step {t.get('val_step', '-')} |"
        )
        if t.get("tokens_per_s"):
            lines.append(f"| Speed | {t['tokens_per_s']:,.0f} tokens/s; about "
                         f"{t.get('eta_hours', 0):.1f} h left in this phase |")  # fmt: skip
    if t and not t.get("reachable", True):
        lines.append(f"| Pod reachable | **no** ({t.get('error', '')[:120]}) |")
    if "spent" in info:
        lines.append(f"| Spend since watch began | ${info['spent']:.2f} (cap ${a.cap:.0f}); "
                     f"balance ${info['balance']:.2f} |")  # fmt: skip
    if s.get("capped") or s.get("halted"):
        lines.append("| Automation | **paused, needs the owner** |")
    lines += ["", "## Passage index (BOM-25)", "",
              f"- GPU share (Internet Archive, TCP; 108M passages): {info.get('gpu_index', '-')}",
              f"- Mac share (Harvard): {mac_index()}", "",
              "## Recent events", ""]  # fmt: skip
    lines += [f"- {w}: {m}" for w, m in reversed(s["events"][-12:])] or ["- none yet"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--pod", required=True)
    ap.add_argument("--issue", type=int, default=None)
    ap.add_argument("--every", type=int, default=600, help="seconds between checks")
    ap.add_argument("--report-minutes", type=int, default=30)
    ap.add_argument("--summary-hours", type=float, default=12)
    ap.add_argument("--stall-minutes", type=float, default=30)
    ap.add_argument("--backup-hours", type=float, default=4)
    ap.add_argument("--cap", type=float, default=300.0, help="dollars of spend before stopping")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args(argv)
    s = load_state(a.pod)
    while True:
        try:
            info = tick(s, a)
        except Exception as e:  # noqa: BLE001 -- the watcher must outlive any one failure
            info = {"checked": now(), "error": str(e)}
            log(f"tick failed: {e}")
        save_state(s)
        if a.issue and time.time() - s.get("last_report", 0) > a.report_minutes * 60:
            body = report(s, info, a)
            rc, _ = sh(["gh", "issue", "edit", str(a.issue), "--body", body])
            if rc == 0:
                s["last_report"] = time.time()
            if time.time() - s.get("last_summary", 0) > a.summary_hours * 3600:
                sh(["gh", "issue", "comment", str(a.issue), "--body", "Summary\n\n" + body])
                s["last_summary"] = time.time()
            save_state(s)
        if a.once or s["phase"] == "finished":
            return 0
        time.sleep(a.every)


if __name__ == "__main__":
    sys.exit(main())
