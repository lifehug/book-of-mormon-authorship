"""The Mac/GPU split of the passage index (BOM-25): boundaries never overlap or leave a gap."""

from semantic import index


def test_remaining_split_is_a_partition(monkeypatch):
    ids = ["hathitrust:a", "institutional_books:b", "internet_archive:c", "tcp:d",
           "internet_archive:e"]  # fmt: skip
    rows = [{"work_id": w} for w in ids]
    monkeypatch.setattr(index, "indexed", lambda: {"hathitrust:a"})
    monkeypatch.setattr("reuse.exact.eligible_any_year", lambda cfg: rows)
    mac = index.remaining({}, before="internet_archive:")
    gpu = index.remaining({}, start="internet_archive:")
    assert [r["work_id"] for r in mac] == ["institutional_books:b"]
    assert [r["work_id"] for r in gpu] == ["internet_archive:c", "internet_archive:e", "tcp:d"]


def test_second_batch_takes_the_macs_tail(monkeypatch):
    ids = ["institutional_books:a", "institutional_books:b", "institutional_books:c",
           "internet_archive:d"]  # fmt: skip
    rows = [{"work_id": w} for w in ids]
    monkeypatch.setattr(index, "indexed", lambda: set())
    monkeypatch.setattr("reuse.exact.eligible_any_year", lambda cfg: rows)
    mac = index.remaining({}, before="institutional_books:b")
    gpu = index.remaining({}, start="institutional_books:b", before="internet_archive:")
    assert [r["work_id"] for r in mac] == ["institutional_books:a"]
    assert [r["work_id"] for r in gpu] == ["institutional_books:b", "institutional_books:c"]
