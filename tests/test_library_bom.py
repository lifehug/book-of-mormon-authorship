"""Profile slices for the library ranking (BOM-95)."""

from eval.library_bom import windows


def test_windows_start_in_the_middle_and_never_overlap() -> None:
    assert windows(2, 2) == [(0, 2)] and windows(5, None) == [(0, 5)] and windows(1, 3) == [(0, 1)]
    w = windows(11, 3)
    assert w[0] == (4, 7) and sorted(w) == [(1, 4), (4, 7), (7, 10)]
    for n_eps in range(3, 40):
        got = sorted(windows(n_eps, 3))
        assert all(b - a == 3 and b <= n_eps for a, b in got)
        assert all(x[1] <= y[0] for x, y in zip(got, got[1:], strict=False))
