"""Long texts are aligned as overlapping pieces and mapped back (BOM-16)."""

from kjv_mask import run as R
from kjv_mask.align import Span


def test_short_text_is_one_piece():
    assert R.piece_ranges("a b c") == [(0, 5)]


def test_pieces_overlap_and_cover(monkeypatch):
    monkeypatch.setattr(R, "PIECE_WORDS", 10)
    monkeypatch.setattr(R, "PIECE_OVERLAP", 3)
    text = " ".join(f"w{i}" for i in range(25))
    rs = R.piece_ranges(text)
    assert rs[0][0] == 0 and rs[-1][1] == len(text)
    assert [text[a:b].split()[0] for a, b in rs] == ["w0", "w10", "w20"]
    assert text[rs[0][0] : rs[0][1]].split()[-1] == "w12"  # 3 words of overlap


def test_spans_map_back_onto_the_whole_text(monkeypatch, tmp_path):
    monkeypatch.setattr(R, "PIECE_WORDS", 10)
    monkeypatch.setattr(R, "PIECE_OVERLAP", 3)
    monkeypatch.setattr(R, "OUT", tmp_path)
    monkeypatch.setattr(R, "validation_passed", lambda: True)
    monkeypatch.setattr(R, "registered_params", lambda: {})
    text = " ".join(f"w{i}" for i in range(25))
    target = text.index("w11")

    def fake_mask(docs, work, params):  # "finds" w11 wherever a piece holds it
        out = {}
        for d in docs:
            i = d["text"].find("w11")
            out[d["id"]] = [Span(i, i + 3, "verbatim", 1.0, 1, "kjv:X.1")] if i >= 0 else []
        return out

    monkeypatch.setattr(R, "mask", fake_mask)
    R.run("t", docs_of=lambda g: [R._in_memory("doc", text)])
    import json

    rec = json.loads((tmp_path / "t" / "spans.jsonl").read_text())
    assert [(s["start"], s["end"]) for s in rec["spans"]] == [(target, target + 3)]  # one, not two


def test_failed_batch_is_split_and_mapped_back(monkeypatch):
    monkeypatch.setattr(R, "PIECE_OVERLAP", 2)
    text = " ".join(f"w{i}" for i in range(30))
    target = text.index("w25")

    def fake_mask(docs, work, params):
        if any(len(d["text"].split()) > 12 for d in docs):
            raise RuntimeError("passim failed at every heap size")
        out = {}
        for d in docs:
            i = d["text"].find("w25")
            out[d["id"]] = [Span(i, i + 3, "verbatim", 1.0, 1, "kjv:X.1")] if i >= 0 else []
        return out

    monkeypatch.setattr(R, "mask", fake_mask)
    log: list = []
    got = R.mask_resilient([{"id": "d", "text": text}], None, {}, log=log)
    assert [(s.start, s.end) for s in got["d"]] == [(target, target + 3)]
    assert log and log[0]["texts"] == ["d"]
