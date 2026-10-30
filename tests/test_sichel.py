from classic.sichel import equivalent, fit


def test_fit_reproduces_holmes_table_3_moroni_1() -> None:
    """Holmes (1992) Table 3, Moroni 1: alpha 1.141739, theta 0.961849 (cell pooling differs)."""
    f = fit([139, 66, 32, 26, 22, 20, 9, 10, 8, 3, 3, 2, 0, 2, 3], 22)
    assert abs(f["alpha"] - 1.141739) / 1.141739 < 0.02
    assert abs(f["theta"] - 0.961849) < 0.002


def test_equivalent_keeps_the_invariants() -> None:
    a, t, n = 1.14, 0.96, 1961
    a2, t2 = equivalent(a, t, n)
    assert abs(a * (1 - t) ** 0.5 - a2 * (1 - t2) ** 0.5) < 1e-9
    assert abs(t / ((1 - t) * n) - t2 / ((1 - t2) * 10000)) < 1e-12
