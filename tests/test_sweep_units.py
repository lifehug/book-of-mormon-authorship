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


def test_distances_and_leave_one_out() -> None:
    import numpy as np

    from sweep.calibrate import distances, loo_counts

    g = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    d = distances(g, np.array([[2.0, 0.0], [1.0, 0.1]]), "style")
    assert d.argmin() == 0 and np.isclose(d[1], 1.0, atol=0.06)
    z = distances(g, g[:1], "mfw", g.mean(axis=0), g.std(axis=0, ddof=1))
    assert z.argmin() == 0 and np.isclose(z[0], 0.0)
    # two books over three authors; book 0's author is 0, book 1's is 2
    dd = {"mfw": [np.array([0.1, 0.2, 0.9]), np.array([0.5, 0.6, 0.1])],
          "style": [np.array([0.1, 0.3, 0.9]), np.array([0.5, 0.2, 0.1])]}  # fmt: skip
    best = {"mfw": np.array([0.2, 0.5]), "style": np.array([0.3, 0.2])}
    # book 0 judged by book 1's thresholds (0.5, 0.2): author 1 has 0.2 < 0.5 but 0.3 !< 0.2
    assert loo_counts(dd, [0, 2], best, 5) == [0, 0]
    best = {"mfw": np.array([0.2, 0.7]), "style": np.array([0.3, 0.4])}
    assert loo_counts(dd, [0, 2], best, 5) == [1, 0]
