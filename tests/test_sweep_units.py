"""The sweep's block sampler (BOM-39; Amendment 28)."""

import random

from sweep.units import chunks, sample


def test_sample_round_robin_distinct_slots() -> None:
    works = {"a": [("v1", 5000)], "b": [("v2", 2500), ("v3", 900)], "c": [("v4", 10_000)]}
    got = sample(works, 6, 1000, random.Random(1))
    assert len(got) == 6 and len(set(got)) == 6
    by = {v: k for k, vols in works.items() for v, _ in vols}
    assert {by[v] for v, _ in got[:3]} == {"a", "b", "c"}  # one per work before any repeats
    assert all(st % 1000 == 0 and st + 1000 <= dict(sum(works.values(), []))[v] for v, st in got)


def test_sample_stops_when_slots_run_out() -> None:
    got = sample({"a": [("v1", 2999)], "b": [("v2", 999)]}, 20, 1000, random.Random(2))
    assert sorted(got) == [("v1", 0), ("v1", 1000)]


def test_chunks_capped_and_seeded() -> None:
    vols = [("v1", 23_000), ("v2", 4_999), ("v3", 10_000)]
    assert chunks(vols, 5000, 22, random.Random(0)) == [
        ("v1", 0), ("v1", 5000), ("v1", 10000), ("v1", 15000), ("v3", 0), ("v3", 5000)
    ]  # fmt: skip
    few = chunks(vols, 5000, 3, random.Random(0))
    assert len(few) == 3 and few == sorted(few) == chunks(vols, 5000, 3, random.Random(0))
