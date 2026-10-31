"""Known-answer controls for texts that claim to be ancient (BOM-61).

Two groups of period English texts whose answer is known: **genuine** translations of texts
composed in antiquity, and **presented as ancient**: compositions of their own century sold as
translations or transcriptions of old records. A later test bears on whether the Book of Mormon
is a translation of an ancient record only if it separates these groups first. The set and the
separation rule are fixed here, in ``docs/known-answer-plan.md``, before any test runs on them;
no Book of Mormon text is used.

One edition per text, every volume of it; public sources preferred where the corpus has one, so
anyone can check the choice. Each entry says why it is in and what the scholarly consensus is.

Usage::

    python -m eval.known_answer build   # -> data/known_answer/set.jsonl
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

from metadata.config import stamp

OUT = Path("data/known_answer/set.jsonl")

GENUINE, MODERN = "genuine_translation", "presented_as_ancient"

# (key, group, primary, label, work ids, why it is here, consensus and caveats)
SET = [
    (
        "twelve_patriarchs",
        GENUINE,
        True,
        "The Testaments of the Twelve Patriarchs (Grosseteste's Latin, in English), 1791",
        ["internet_archive:bim_eighteenth-century_the-testament-of-the-twe_1791"],
        "biblical register, not in the King James Bible, widely printed in America in the period",
        "Composed in antiquity (2nd century BC to 2nd century AD, with Christian additions); "
        "reached English through a 13th-century Latin translation.",
    ),
    (
        "enoch",
        GENUINE,
        True,
        "The Book of Enoch, tr. Richard Laurence from the Ethiopic, 1821",
        ["hathitrust:yale.39002005226072"],
        "biblical register; the first English translation, published nine years before 1830",
        "1 Enoch, composed 3rd to 1st century BC; Laurence translated the Ethiopic manuscript "
        "Bruce brought to Britain.",
    ),
    (
        "apocryphal_nt",
        GENUINE,
        True,
        "The Apocryphal New Testament (Hone, from Jones and Wake), 1820",
        ["internet_archive:apocryphalnewtes0000vari_l6a3"],
        "biblical register; early Christian texts outside the canon, in period translations",
        "Texts of the 1st to 5th centuries; some were pseudepigraphic in antiquity (letters of "
        "Paul and Seneca), but all were composed in antiquity, which is the question here.",
    ),
    (
        "josephus",
        GENUINE,
        True,
        "Josephus, tr. William Whiston (The Genuine Works), 1794",
        [
            "institutional_books:HN26TQ",
            "institutional_books:HN26TR",
            "institutional_books:HN26TT",
            "institutional_books:HN26TU",
            "institutional_books:HN26TV",
        ],
        "ancient Jewish history retelling biblical narrative; the standard period translation",
        "1st century AD Greek; Whiston's translation of 1737. Includes Whiston's dissertations.",
    ),
    (
        "koran",
        GENUINE,
        True,
        "The Koran, tr. George Sale, 1800",
        ["internet_archive:korancommonlycal1800sale"],
        "scripture claiming revelation, translated from a non-European language",
        "7th century Arabic; Sale's translation of 1734, with his long Preliminary Discourse.",
    ),
    (
        "herodotus",
        GENUINE,
        True,
        "Herodotus, tr. William Beloe, 1791",
        [
            "internet_archive:bim_eighteenth-century_histories-english-the_herodotus_1791_1",
            "internet_archive:bim_eighteenth-century_histories-english-the_herodotus_1791_2",
        ],
        "ancient history and ethnography of distant peoples",
        "5th century BC Greek; Beloe's translation with notes. The corpus holds two of its "
        "volumes.",
    ),
    (
        "homer",
        GENUINE,
        True,
        "Homer, The Iliad and Odyssey, tr. Alexander Pope, 1783",
        [
            f"internet_archive:bim_eighteenth-century_the-iliad-and-odyssey-of_homer_1783_{i}"
            for i in (1, 2, 3, 4)
        ],
        "ancient epic in verse; the natural counterpart of Ossian",
        "8th century BC Greek; Pope's verse translation (1715-26), freer than most.",
    ),
    (
        "hesiod",
        GENUINE,
        True,
        "Hesiod, tr. Charles Abraham Elton, 1815",
        ["internet_archive:remainsofhesioda00hesiuoft"],
        "ancient verse on the gods and origins",
        "c. 700 BC Greek; Elton's verse translation with notes.",
    ),
    (
        "sacontala",
        GENUINE,
        True,
        "Kalidasa, Sacontala, tr. William Jones, 1792",
        ["internet_archive:sacontalaorfatal00kali_0"],
        "ancient text from a non-European language, translated in the period",
        "Sanskrit drama, c. 4th-5th century AD; Jones's prose translation of 1789.",
    ),
    (
        "ossian",
        MODERN,
        True,
        "James Macpherson, Fingal and other poems of Ossian, 1800",
        ["internet_archive:fingalotherpoems00macp"],
        "sold as translations of 3rd-century Gaelic epic; the best-known case of the period",
        "Composed largely by Macpherson in the 1760s from fragments of Gaelic ballad; the Highland "
        "Society's report (1805) found no originals for the poems as published.",
    ),
    (
        "rowley",
        MODERN,
        True,
        "Thomas Chatterton, Poems supposed to have been written at Bristol by Thomas Rowley, 1794",
        ["internet_archive:poemssupposedtoh01chat"],
        "presented as transcriptions of 15th-century manuscripts, in invented old spelling",
        "Written by Chatterton in the 1760s; shown modern by Tyrwhitt (1782) and Warton (1782). "
        "Old, not ancient; its spelling will strain OCR normalisation and every word-based test.",
    ),
    (
        "jasher",
        MODERN,
        True,
        "The Book of Jasher (Jacob Ilive, 1751), as reprinted 1829",
        ["internet_archive:bookofjasherwith00iliv"],
        "presented as a translation of the lost book of Jasher named in Joshua; biblical register; "
        "reprinted in 1829",
        "Forged by Jacob Ilive in 1751, with an invented translator (Alcuin) and testimonies.",
    ),
    # secondary: presented as an old record, but not ancient, or acknowledged early
    (
        "ireland_papers",
        MODERN,
        False,
        "W. H. Ireland, Miscellaneous papers under the hand and seal of William Shakspeare, 1796",
        [
            "internet_archive:bim_eighteenth-century_miscellaneous-papers-and_ireland-w-h-william-_1796"
        ],
        "presented as transcriptions of Elizabethan documents; exposed the same year",
        "Forged by Ireland, who confessed in 1796; Malone's Inquiry (1796) exposed it. Old, not "
        "ancient.",
    ),
    (
        "otranto",
        MODERN,
        False,
        "Horace Walpole, The Castle of Otranto, 1782",
        ["internet_archive:bim_eighteenth-century_the-castle-of-otranto-a_walpole-horace_1782"],
        "first presented (1764) as a translation of an Italian manuscript of 1529; the title page "
        "still names the invented translator",
        "Walpole acknowledged it in the second edition (1765); a fiction device more than a fraud.",
    ),
]


def build() -> int:
    want = {w for row in SET for w in row[4]}
    cols = ["work_id", "source", "title", "author", "year", "has_text", "text_path"]
    cat = {
        r["work_id"]: r
        for r in pq.read_table("data/catalog/catalog.parquet", columns=cols).to_pylist()
        if r["work_id"] in want
    }
    missing = sorted(want - {w for w, r in cat.items() if r["has_text"]})
    if missing:
        print(f"no text for: {missing}")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    head = stamp()
    with OUT.open("w") as f:
        for key, group, primary, label, ids, why, consensus in SET:
            vols = [{k: cat[w][k] for k in ("work_id", "source", "title", "author", "year")}
                    for w in ids]  # fmt: skip
            f.write(json.dumps({"key": key, "group": group, "primary": primary, "label": label,
                                "volumes": vols, "why": why, "consensus": consensus,
                                "config_sha256": head["config_sha256"]}) + "\n")  # fmt: skip
    n = {g: sum(1 for r in SET if r[1] == g and r[2]) for g in (GENUINE, MODERN)}
    print(f"{OUT}: {len(SET)} texts ({n[GENUINE]} genuine and {n[MODERN]} presented as ancient "
          f"in the primary set; {sum(1 for r in SET if not r[2])} secondary)")  # fmt: skip
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["build"]:
        return build()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
