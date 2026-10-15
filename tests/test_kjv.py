from ingest.kjv import parse_vpl

SAMPLE = """GEN 1:1 In the beginning God created the heaven and the earth.
GEN 1:2 And the earth was without form, and void; and darkness [was] upon the face of the deep.
TOB 1:1 The book of the words of Tobit.
MAT 5:3 Blessed [are] the poor in spirit: for theirs is the kingdom of heaven.
"""


def test_parse_vpl() -> None:
    recs = parse_vpl(SAMPLE)
    assert [r["ref"] for r in recs] == ["Genesis 1:1", "Genesis 1:2", "Tobit 1:1", "Matthew 5:3"]
    assert [r["section"] for r in recs] == ["OT", "OT", "Apocrypha", "NT"]
    assert (
        recs[1]["text"]
        == "And the earth was without form, and void; and darkness was upon the face of the deep."
    )
    assert "[was]" in recs[1]["text_marked"]
    assert recs[3]["chapter"] == 5 and recs[3]["verse"] == 3
