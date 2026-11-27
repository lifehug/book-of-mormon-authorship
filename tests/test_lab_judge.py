"""The paced judging queue: the hours window, and resuming without re-asking."""

import json
import time

from lab import judge


def _at(hour: int) -> time.struct_time:
    return time.struct_time((2026, 11, 20, hour, 0, 0, 4, 324, 0))


def test_hours_window_wraps_past_midnight():
    assert judge.in_hours([22, 7], _at(23))
    assert judge.in_hours([22, 7], _at(3))
    assert not judge.in_hours([22, 7], _at(12))
    assert judge.in_hours([9, 17], _at(9))
    assert not judge.in_hours([9, 17], _at(17))


def test_done_reads_answered_ids(tmp_path):
    answers = tmp_path / "a.jsonl"
    assert judge._done(answers) == set()
    answers.write_text(json.dumps({"id": "x", "reply": "Y"}) + "\n")
    assert judge._done(answers) == {"x"}


def test_failed_call_keeps_its_reason(tmp_path, monkeypatch):
    """An outage that speaks only on stderr is still logged, with a time, and kept for the judge."""
    import subprocess

    from metadata import genre
    from semantic import skeleton

    monkeypatch.setattr(genre, "PARSE_LOG", tmp_path / "pf.jsonl")
    monkeypatch.setattr(skeleton, "_wait_turn", lambda: None)
    done = subprocess.CompletedProcess([], 1, stdout="", stderr="usage limit reached")
    monkeypatch.setattr(skeleton.subprocess, "run", lambda *a, **k: done)
    assert skeleton._claude("q", "sonnet", retries=1) is None
    assert skeleton.LAST_FAILURE[0] == "usage limit reached"
    row = json.loads((tmp_path / "pf.jsonl").read_text())
    assert row["raw"] == "usage limit reached" and row["ts"]
