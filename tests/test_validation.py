"""The BOM-12 review page must show text for every record, verse included."""

from pathlib import Path

from metadata.validation import excerpt


def test_verse_gets_an_excerpt(tmp_path: Path) -> None:
    verse = tmp_path / "verse.txt"
    verse.write_text(
        "O Myghty fader in heuen on hye\nOne god and perses thre\n\nThat made bothe daye\n"
    )
    assert excerpt({"text_path": str(verse)}) == (
        "O Myghty fader in heuen on hye / One god and perses thre / That made bothe daye"
    )


def test_prose_keeps_the_usual_excerpt(tmp_path: Path) -> None:
    prose = tmp_path / "prose.txt"
    line = "A long line of ordinary prose that is well over forty characters."
    prose.write_text(f"Title\n{line}\n")
    assert excerpt({"text_path": str(prose)}) == line


def test_no_text_path() -> None:
    assert excerpt({"text_path": None}) == ""
