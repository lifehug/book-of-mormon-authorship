"""The generic pod job runner's pure logic (scripts/pod_jobs.py)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pod_jobs", ROOT / "scripts/pod_jobs.py")
pj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pj)


def test_expand_lists_files_and_directories(tmp_path: Path) -> None:
    (tmp_path / "d/e").mkdir(parents=True)
    (tmp_path / "d/a.txt").write_text("x")
    (tmp_path / "d/e/b.txt").write_text("y")
    (tmp_path / "c.txt").write_text("z")
    assert pj.expand(["d", "c.txt"], tmp_path) == ["c.txt", "d/a.txt", "d/e/b.txt"]


def test_expand_refuses_missing(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(SystemExit):
        pj.expand(["nope"], tmp_path)


def test_job_script_marker_only_after_all_jobs() -> None:
    assert pj.job_script(["a", "b"], "/m") == "a && b && touch /m"


def test_unreachable_is_never_a_dead_job() -> None:
    assert pj.classify(255, "") == "unreachable"
    assert pj.classify(1, "ssh: connect to host x port 22: Connection refused") == "unreachable"
    assert pj.classify(1, "Connection timed out during banner exchange") == "unreachable"
    assert pj.classify(1, "some other failure") == "unreachable"  # not proven dead
    assert pj.classify(0, "ALIVE\n  step 3") == "alive"
    assert pj.classify(0, "/workspace/JOBS_DONE\n") == "done"
    assert pj.classify(0, "Traceback ...") == "dead"


def test_parse_sums() -> None:
    d = "a" * 64
    out = f"{d}  data/x.json\n{d} *data/y.bin\nsha256sum: z: No such file\n"
    assert pj.parse_sums(out) == {"data/x.json": d, "data/y.bin": d}
