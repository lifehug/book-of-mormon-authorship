from ingest.edition_1830 import join_lines, parse, roman

SAMPLE = (
    "\fTitle stuff\n\n           PREFACE.\n\n  To the reader, a short preface.\n"
    "\f        THE FIRST BOOK OF NEPHI.\n                 HIS REIGN AND MINISTRY.\n\n"
    "                         CHAPTER I.\n"
    "An account of Lehi and his wife, and his four Sons,\n being called Laman and Nephi.\n"
    "  I, Nephi, having been born of goodly parents, there­\nfore I was taught.\n"
    "  For it came to pass in the first year\n"
    "\f6                   FIRST BOOK OF NEPHI.\n\nof the reign of Zedekiah.\n"
    "  And it came to pass that he prayed.\n"
    "                         CHAPTER II.\n"
    "  Behold a second chapter.\n"
    "\f                     FIRST BOOK OF NEPHI.                      7\n\n"
    "  Last paragraph.\n                         THE END.\n"
    "          THE TESTIMONY OF THREE WITNESSES.\n  Be it known.\n"
)


def test_roman() -> None:
    assert [roman(x) for x in ("I", "IV", "IX", "XIV", "XXX")] == [1, 4, 9, 14, 30]


def test_join_lines_soft_hyphen() -> None:
    assert join_lines(["born of goodly parents, there­", "fore I was", "", "taught."]) == (
        "born of goodly parents, therefore I was taught."
    )


def test_parse_structure() -> None:
    recs = parse(SAMPLE)
    kinds = [(r["book"], r["chapter"], r["kind"]) for r in recs]
    assert kinds[0] == (None, None, "preface")
    assert kinds[1] == ("1 Nephi", 0, "title")
    assert kinds[2] == ("1 Nephi", 1, "synopsis")
    assert [k for k in kinds[3:]] == [
        ("1 Nephi", 1, "body"),
        ("1 Nephi", 1, "body"),
        ("1 Nephi", 1, "body"),
        ("1 Nephi", 2, "body"),
        ("1 Nephi", 2, "body"),
    ]
    body = [r for r in recs if r["kind"] == "body"]
    expected = "I, Nephi, having been born of goodly parents, therefore I was taught."
    assert body[0]["text"] == expected
    # paragraph spanning a page break is joined and spans pages 5-6
    assert body[1]["text"] == "For it came to pass in the first year of the reign of Zedekiah."
    assert (body[1]["page_start"], body[1]["page_end"]) == (5, 6)
    assert body[-1]["page_start"] == 7
    # testimonies after THE END are excluded
    assert not any("Be it known" in r["text"] for r in recs)
