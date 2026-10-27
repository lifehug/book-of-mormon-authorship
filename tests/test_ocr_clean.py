"""Rule-based OCR cleaning (BOM-14)."""

from ocr_fix.clean import clean, fix_long_s, rejoin_hyphens, strip_headers

LEX = {
    "first": 6446, "firft": 2, "said": 6001, "faid": 41, "fame": 2617, "same": 6245,
    "houses": 2969, "example": 900, "well": 5000, "known": 4000, "of": 6800, "the": 6800,
    "sufficient": 3000, "history": 2000,
}  # fmt: skip


def test_long_s_by_frequency() -> None:
    text, n = fix_long_s("The firft houfes faid. Fame and fame. If of", LEX)
    assert text == "The first houses said. Fame and fame. If of"
    assert n == 3


def test_long_s_mixed_positions() -> None:
    assert fix_long_s("fufficient", LEX)[0] == "sufficient"


def test_hyphen_rejoin() -> None:
    text, n = rejoin_hyphens("an exam-\nple and well-\n\nknown things", LEX)
    assert text == "an example and well-known things"
    assert n == 2


def test_hyphen_not_across_page_break() -> None:
    assert rejoin_hyphens("exam-\n\f\nHISTORY\nple", LEX)[1] == 0


def test_paged_headers_and_numbers() -> None:
    words = "alpha beta gamma delta epsilon zeta eta theta iota kappa".split()
    pages = [f"THE HISTORY OF\n{i}\nbody text line {i}\n{w} ends\n{i}" for i, w in enumerate(words)]
    text, n = strip_headers("\f".join(pages))
    assert "HISTORY" not in text and "body text line 3" in text
    assert n == 20 + 10  # header and top number on 10 pages, plus bottom numbers


def test_unpaged_headers() -> None:
    body = "x" * 1990
    text, _ = strip_headers("\n".join(f"THE HISTORY OF\n{body}\n{i + 1}" for i in range(10)))
    assert "HISTORY" not in text and body in text


def test_clean_order() -> None:
    text, counts = clean("faid the exam-\nple", LEX)
    assert text == "said the example"
    assert counts == {"header_lines": 0, "hyphens": 1, "long_s": 1}
