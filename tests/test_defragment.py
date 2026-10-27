"""Re-segmenting fragmented newspaper OCR (BOM-14)."""

from ocr_fix.defragment import Segmenter, fragmented, repair_line

FREQ = {
    "has": 5000, "been": 6000, "the": 90000, "re": 50, "elected": 400, "opposition": 300,
    "no": 8000, "which": 9000, "can": 7000, "be": 9000, "handsome": 200, "called": 900,
}  # fmt: skip
SEG = Segmenter(FREQ)


def test_detects_fragmented_lines() -> None:
    assert fragmented("h a s b een re -e le cted")
    assert not fragmented("which can be called handsome")


def test_resegments_into_words() -> None:
    assert repair_line("h a s b een o p p o s i t i o n w hich ca n be", SEG) == (
        "has been opposition which can be"
    )


def test_leaves_garbage_runs_alone() -> None:
    line = "q x z k w v j"
    assert repair_line(line, SEG) == line
