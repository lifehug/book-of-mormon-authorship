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
