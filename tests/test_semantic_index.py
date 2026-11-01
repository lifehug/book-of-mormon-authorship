from semantic.index import spans


def test_spans_cut_whitespace_words_and_drop_a_short_tail():
    text = " ".join(f"w{i}" for i in range(300))
    sp = spans(text, 128, 32)
    assert [w for _, _, w in sp] == [128, 128, 44]
    a, b, _ = sp[1]
    assert text[a:b].split()[0] == "w128" and text[a:b].split()[-1] == "w255"
    assert [w for _, _, w in spans(" ".join(["x"] * 150), 128, 32)] == [128]
