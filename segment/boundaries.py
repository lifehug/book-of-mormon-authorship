"""The narrator, dictation-order and scribe boundary file (BOM-17).

Amendment 2: "The narrator, dictation-order and scribe boundary file is published with its
SHA-256 before any segmented analysis." This builds it from the 1830 edition's paragraphs
(``data/bom/1830/edition_1830.jsonl``) and the original-manuscript alignment of BOM-05
(``data/bom/align_original_paragraphs.jsonl``). Every boundary carries its evidence: the 1830
paragraph that marks it, quoted, or the manuscript pages it rests on. No boundary is set by
reading the text for style; the Book of Mormon stays sealed from analysis (4.2), and building
the file reads only its structure.

``narrator``
    The record-keeper's voice, changed only where the text itself hands it over ("Behold I,
    Moroni, do finish the record of my father Mormon"). Mosiah to Mormon 7 is Mormon's
    abridgement; Ether is Moroni's.
``embedded``
    A secondary layer: documents the text explicitly presents as another writer's record or
    epistle inside a narrator's account. 1830 paragraphs are long and several documents begin
    or end mid-paragraph, so this layer is paragraph-granular and every entry says whether its
    edges are exact.
``dictation_order``
    Mosiah to Moroni first, then 1 Nephi to Words of Mormon. Evidence in the data itself: the
    1830 preface says the first 116 pages were lost and the work resumed, and in the surviving
    original manuscript John Whitmer's and Scribe 3's hands appear only in 1 Nephi, every other
    surviving page being Cowdery's -- the small plates were written last, at the Whitmer home in
    Fayette. Where Words of Mormon fell is not settled by the manuscript; it is placed last and
    flagged.
``scribe``
    From the surviving original manuscript only (about 28% of it). A paragraph on a page that
    does not survive is ``not_extant``, never guessed.

Usage::

    python -m segment.boundaries      # -> data/bom/segments/boundaries.json and its SHA-256
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

EDITION = Path("data/bom/1830/edition_1830.jsonl")
OM = Path("data/bom/align_original_paragraphs.jsonl")
OUT_DIR = Path("data/bom/segments")
OUT = OUT_DIR / "boundaries.json"
LABELS = OUT_DIR / "paragraph_labels.jsonl"

# (first 1830 paragraph seq, narrator); each holds until the next. Book starts are resolved
# from the edition; numbered seqs are hand-overs inside a book, quoted in EVIDENCE.
NARRATOR_BOOKS = {
    "1 Nephi": "Nephi", "Jacob": "Jacob", "Enos": "Enos", "Jarom": "Jarom", "Omni": "Omni",
    "Words of Mormon": "Mormon", "Mormon": "Mormon", "Ether": "Moroni", "Moroni": "Moroni",
}  # fmt: skip
NARRATOR_HANDOVERS = {
    585: "Amaron",
    586: "Chemish",
    587: "Abinadom",
    588: "Amaleki",
    1316: "Moroni",
}
EMBEDDED = [
    # (first seq, last seq, document, edges exact?)
    (638, 651, "record of Zeniff", True),
    (773, 785, "words of Alma, from his own record", True),
    (786, 829, "words of Alma and Amulek, from Alma's record", True),
    (1040, 1042, "epistles of Ammoron and Moroni", False),
    (1048, 1077, "epistle of Helaman to Moroni", False),
    (1082, 1082, "epistle of Moroni to Pahoran", False),
    (1083, 1085, "epistle of Pahoran to Moroni", False),
    (1195, 1196, "epistle of Giddianhi to Lachoneus", False),
    (1360, 1362, "words of Mormon on faith, hope and charity", False),
    (1363, 1367, "epistles of Mormon to Moroni", True),
]
DICTATION = [
    "Mosiah", "Alma", "Helaman", "3 Nephi", "4 Nephi", "Mormon", "Ether", "Moroni",
    "1 Nephi", "2 Nephi", "Jacob", "Enos", "Jarom", "Omni", "Words of Mormon",
]  # fmt: skip
FIRST_PHASE = set(DICTATION[:8])


def _rows() -> list[dict]:
    return [json.loads(ln) for ln in EDITION.read_text(encoding="utf-8").splitlines()]


def _quote(text: str, n: int = 90) -> str:
    return " ".join(text.split())[:n]


def build() -> tuple[dict, list[dict]]:
    rows = [r for r in _rows() if r["book"]]
    by_seq = {r["seq"]: r for r in rows}
    om = {r["seq"]: r for r in (json.loads(ln) for ln in OM.read_text().splitlines())}
    starts = {}
    for r in rows:
        starts.setdefault(r["book"], r["seq"])
    anchors = sorted(
        [(starts[b], n, f"book start: {b}") for b, n in NARRATOR_BOOKS.items()]
        + [(s, n, _quote(by_seq[s]["text"])) for s, n in NARRATOR_HANDOVERS.items()]
    )
    words = {r["seq"]: len(r["text"].split()) for r in rows}
    labels = []
    for r in rows:
        # the last hand-over at or before this paragraph; Mosiah to 4 Nephi fall after Words
        # of Mormon and before Mormon's own book, so they are Mormon's abridgement
        narrator = [n for s, n, _ in anchors if s <= r["seq"]][-1]
        emb = next((d for a, b, d, _ in EMBEDDED if a <= r["seq"] <= b), None)
        o = om.get(r["seq"])
        scribe = (
            "|".join(sorted(" ".join(s.split()) for s in o["scribes"]))
            if o and o["covered"] and o["scribes"]
            else "not_extant"
        )
        labels.append(
            {
                "seq": r["seq"],
                "book": r["book"],
                "chapter_1830": r["chapter"],
                "kind": r["kind"],
                "words": words[r["seq"]],
                "narrator": narrator,
                "embedded": emb,
                "dictation_index": DICTATION.index(r["book"]),
                "dictation_phase": "first" if r["book"] in FIRST_PHASE else "last",
                "scribe": scribe,
            }
        )
    order = sorted(labels, key=lambda x: (x["dictation_index"], x["seq"]))
    for i, x in enumerate(order):
        x["dictation_position"] = i

    def runs(key: str, seq_order: list[dict]) -> list[dict]:
        out: list[dict] = []
        for x in seq_order:
            if out and out[-1]["label"] == x[key]:
                out[-1]["seq_last"] = x["seq"]
                out[-1]["paragraphs"] += 1
                out[-1]["words"] += x["words"]
            else:
                out.append({"label": x[key], "seq_first": x["seq"], "seq_last": x["seq"],
                            "paragraphs": 1, "words": x["words"]})  # fmt: skip
        return out

    return {
        "source": {"edition": str(EDITION), "original_manuscript_alignment": str(OM)},
        "narrator": {
            "segments": runs("narrator", labels),
            "evidence": [{"seq": s, "narrator": n, "marker": q} for s, n, q in anchors]
            + [
                {"seq": 599, "narrator": "Mormon", "marker": _quote(by_seq[599]["text"])},
                {"seq": 1301, "narrator": "Mormon", "marker": _quote(by_seq[1301]["text"])},
            ],
        },  # fmt: skip
        "embedded": [
            {
                "document": d,
                "seq_first": a,
                "seq_last": b,
                "edges_exact": ex,
                "marker": _quote(by_seq[a]["text"]),
            }
            for a, b, d, ex in EMBEDDED
        ],  # fmt: skip
        "dictation_order": {
            "books": DICTATION,
            "segments": runs("dictation_phase", order),
            "evidence": (
                "1830 preface: the first 116 pages were lost and the work resumed from the "
                "plates of Nephi; surviving original manuscript: John Whitmer and Scribe 3 "
                "appear only in 1 Nephi (data/bom/align_original_paragraphs.jsonl)"
            ),
            "uncertain": ["Words of Mormon: placed last; the manuscript does not survive"],
        },
        "scribe": {"segments": runs("scribe", labels)},
    }, labels


def main() -> int:
    data, labels = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    OUT.write_text(body, encoding="utf-8")
    LABELS.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in labels))
    sha = hashlib.sha256(body.encode()).hexdigest()
    print(f"{OUT}  sha256 {sha}")
    for k in ("narrator", "scribe"):
        print(f"  {k}: {len(data[k]['segments'])} segments")
    print(f"  dictation_order: {len(data['dictation_order']['segments'])} phases")
    print(f"  embedded: {len(data['embedded'])} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
