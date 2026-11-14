"""Life dates and the alive rule for swept authors (BOM-91)."""

from sweep.people import cat_life, decide, loc_life, ours, same_name, status

P = {"year": 1829, "min_age": 15, "max_age": 90}


def test_names() -> None:
    assert ours("tatham, edward d d") == ("tatham", ["edward"])
    assert ours("lemaistre, j g john gustavus") == ("lemaistre", ["john", "gustavus"])
    assert ours("bell, john d") == ("bell", ["john", "d"])
    assert same_name(("bell", ["john", "d"]), "Bell, John D., 1790-1850")
    assert not same_name(("bell", ["john", "d"]), "Bell, John, 1763-1820")
    assert same_name(("lemaistre", ["john", "gustavus"]), "Lemaistre, J. G. (John Gustavus), -1840")


def test_dates() -> None:
    assert cat_life("Smith, Ethan, 1762-1849") == (1762, 1849)
    assert loc_life("Gibbs, Maria, 1770-") == (1770, None)
    assert loc_life("Colman, George Washington, -1862") == (None, 1862)
    assert loc_life("Colman, George") is None


def test_decide_takes_only_a_single_plausible_match() -> None:
    labels = ["Colman, George, 1732-1794", "Colman, George, 1762-1836", "Colman, George, 1802-1883"]
    assert decide("colman, george", labels, 1785, 12) == ("ambiguous", 2)
    assert decide("colman, george", labels, 1750, 12) == ("loc", 1732, 1794)
    assert decide("colman, george", ["Colman, Geo. W., 1834-"], 1785, 12) == ("none",)


def test_status() -> None:
    assert status(1762, 1849, P) == "alive" and status(1700, 1790, P) == "dead"
    assert status(1820, None, P) == "too_young" and status(1730, None, P) == "dead"
    assert status(None, 1840, P) == "alive" and status(None, None, P) == "unknown"
