"""A paced queue of questions for a hosted model, run on the owner's Claude subscription.

Several lab tests need a model to read a passage and answer a fixed question (does this passage
use the word in this sense; what does this phrase refer to). Every such answer is **simulated**
judging by an AI model and is labelled so wherever it is reported. A test writes its questions to
a jobs file, one JSON object a line (``{"id": ..., "prompt": ...}``); this runs them through the
lean ``claude -p`` call the study used for its story-skeleton test, at most ``lab.judge.per_hour``
calls an hour and only inside ``lab.judge.hours`` (all day since the owner's word of 2026-11-20),
and appends each reply to the answers file. It resumes from the answers file. A
reply lost to a usage limit or an outage is never written: the job stays open and is tried again
on the next pass, and after ``lab.judge.outage_wait`` seconds when every call in a row fails.

Usage::

    python -m lab.judge run JOBS.jsonl ANSWERS.jsonl [--model M] [--per-hour N] [--any-hour]
    python -m lab.judge status JOBS.jsonl ANSWERS.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from lab.paths import out
from metadata import config
from semantic import skeleton


def _done(answers: Path) -> set[str]:
    if not answers.exists():
        return set()
    return {json.loads(line)["id"] for line in answers.read_text().splitlines() if line.strip()}


def _jobs(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def in_hours(hours: list[int], now: time.struct_time | None = None) -> bool:
    """Whether the local hour is inside ``[start, end)``; the window may wrap past midnight."""
    start, end = hours
    h = (now or time.localtime()).tm_hour
    return start <= h < end if start <= end else (h >= start or h < end)


def run(jobs: Path, answers: Path, model: str, per_hour: float, any_hour: bool) -> int:
    j = config.load()["lab"]["judge"]
    skeleton._PACE["per_hour"] = per_hour
    todo = [job for job in _jobs(jobs) if job["id"] not in _done(answers)]
    print(f"{len(todo):,} questions to ask ({model}, {per_hour:g} an hour)", flush=True)
    failed_in_a_row = 0
    with out(answers).open("a", encoding="utf-8") as fh:
        for n, job in enumerate(todo, 1):
            while not any_hour and not in_hours(j["hours"]):
                time.sleep(j["hours_poll"])
            reply = skeleton._claude(job["prompt"], model, retries=1)
            if reply is None:  # transient: left open for the next pass
                failed_in_a_row += 1
                if failed_in_a_row >= j["outage_after"]:
                    why = skeleton.LAST_FAILURE[0][:200]
                    print(f"  {failed_in_a_row} failures in a row; waiting ({why})", flush=True)
                    time.sleep(j["outage_wait"])
                    failed_in_a_row = 0
                continue
            failed_in_a_row = 0
            row = {"id": job["id"], "reply": reply, "model": model, "invocation": "lean"}
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 50 == 0:
                print(f"  {n:,}/{len(todo):,}", flush=True)
    left = len([job for job in _jobs(jobs) if job["id"] not in _done(answers)])
    print(f"{left:,} still open", flush=True)
    return 1 if left else 0


def main(argv: list[str] | None = None) -> int:
    j = config.load()["lab"]["judge"]
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("cmd", choices=["run", "status"])
    ap.add_argument("jobs", type=Path)
    ap.add_argument("answers", type=Path)
    ap.add_argument("--model", default=j["model"])
    ap.add_argument("--per-hour", type=float, default=j["per_hour"])
    ap.add_argument("--any-hour", action="store_true", help="ignore the night-hours window")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        total, done = len(_jobs(a.jobs)), len(_done(a.answers))
        print(f"{done:,} of {total:,} answered; {total - done:,} open")
        return 0
    return run(a.jobs, a.answers, a.model, a.per_hour, a.any_hour)


if __name__ == "__main__":
    raise SystemExit(main())
