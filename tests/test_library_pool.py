"""The shared pool's equal-dose slices (BOM-94)."""

from eval.library_pool import slices


def test_slices_spread_evenly_and_never_overrun() -> None:
    assert slices(26000, 3039, 3) == [0, 11480, 22961]
    assert slices(3039, 3039, 3) == [0] and slices(3000, 3039, 3) == []
    assert slices(10000, 3039, 1) == [3480]
    assert all(s + 3039 <= 4000 for s in slices(4000, 3039, 3))
