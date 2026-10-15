from ingest.eebo_tcp import tei_text, year_of

TEI = b"""<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><titleStmt>
<title>Header title must not appear</title></titleStmt></fileDesc></teiHeader>
<text><body><div><head>A Sermon</head><p>Hear ye this, <hi>O house</hi> of Jacob.</p>
<p>Second   paragraph.</p></div></body></text></TEI>"""


def test_tei_text_drops_header_and_keeps_blocks() -> None:
    out = tei_text(TEI)
    assert "Header title" not in out
    assert out.splitlines() == ["A Sermon", "Hear ye this, O house of Jacob.", "Second paragraph."]


def test_year_of() -> None:
    assert year_of("1625") == 1625
    assert year_of("[1625?]") == 1625
    assert year_of("n.d.") is None
