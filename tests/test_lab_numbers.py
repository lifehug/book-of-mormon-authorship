"""BOM-114: numbers are read as written, the base-twenty measure and the Alma 11 fit behave."""

from fractions import Fraction

from lab.numbers import ALMA, CATALOGUE, base20_counts, between, english, fit, numbers, values

CFG = {
    "lab": {
        "numbers": {"year_lo": 1000, "year_hi": 1899, "base20_lo": 20, "base20_hi": 400,
                    "part_numbers": 100, "min_part": 50}
    }
}  # fmt: skip


def read(text: str) -> list[int]:
    return [v for v, _, _ in numbers(text, CFG)]


def test_king_james_forms_are_read_as_one_number():
    assert read("threescore and ten years") == [70]
    assert read("six hundred threescore and six") == [666]
    assert read("forty and two thousand three hundred and threescore") == [42360]
    assert read("six hundred thousand and three thousand and five hundred and fifty") == [603550]
    assert read("two and twenty years, and twenty and four, and an hundred and twenty") == [
        22, 24, 120]  # fmt: skip
    assert read("ten thousand times ten thousand") == [10000, 10000]


def test_kinds_units_and_what_is_left_out():
    got = numbers("in the three hundred and twentieth year he had 60 men in 1511. 3 Now one", CFG)
    assert got == [
        (320, "ordinal", "year"),
        (60, "cardinal", "people"),
        (1511, "calendar", "other"),
    ]
    assert numbers("four score years", CFG) == [(80, "cardinal+score", "year")]
    assert read("see chap 12 and page 40, seven and five") == [7, 5]


def test_base_twenty_counts_leave_out_hundreds_and_calendar_years():
    nums = [(v, "cardinal", "other") for v in (20, 40, 60, 30, 50, 100, 200, 400, 25, 420, 10)]
    assert base20_counts(nums + [(1820, "calendar", "other")], CFG) == (3, 2)


def test_bilingual_editions_keep_the_english():
    text = "TRANSLATION.\n\nIt was in the year when they came to the land.\n\nNOTES.\n\nthe of and"
    kept = between(text, r"TRANSLATION\.", r"NOTES\.")
    assert "came to the land" in kept and "the of and" not in kept
    mixed = "Lai año cu ximbal ca hichiucal kaxob\n\nThis is the year in which they came to it."
    assert english(mixed, 0.2).startswith("This is")


def test_fit_is_free_of_scale_and_counts_values_in_common():
    a = {Fraction(1), Fraction(2), Fraction(4)}
    assert fit(a, {Fraction(10), Fraction(20), Fraction(40)}) == (Fraction(1), 3)
    assert fit(a, {Fraction(1), Fraction(3), Fraction(9)}) == (Fraction(1, 5), 1)


def test_alma_has_eight_values_and_every_catalogue_entry_is_marked():
    assert len(values(ALMA)) == 8
    assert values(ALMA) >= {Fraction(1, 8), Fraction(3, 2), Fraction(7)}
    assert all(len(v) == 3 and v[0] and values(v[1]) for v in CATALOGUE.values())
