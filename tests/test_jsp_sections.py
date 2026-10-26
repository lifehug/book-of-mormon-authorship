from ingest import jsp


def page(n, body):
    return {"page": n, "clear_html": body}


def toc(link, title, date="1829-04-01"):
    return {"linkID": link, "pageTitle": title, "date": date}


def test_sections_cut_at_anchors_and_cross_pages():
    recs = [
        page(1, "<p>cover</p>"),
        page(2, '<p>tail of lost text</p><a name="A"></a><p>one two</p>'),
        page(3, '<p>three</p><a name="B"></a><p>four &amp; five</p>'),
    ]
    out = jsp.sections(recs, [toc("B", "Second"), toc("A", "First &amp; best")])
    assert [s["link_id"] for s in out] == [None, "A", "B"]
    front, a, b = out
    assert front["text"].split() == ["cover", "tail", "of", "lost", "text"]
    assert a["title"] == "First & best" and a["first_page"] == 2
    assert a["text"].split() == ["one", "two", "three"]
    assert b["text"].split() == ["four", "&", "five"] and b["words"] == 3


def test_missing_anchor_is_reported_not_dropped():
    out = jsp.sections([page(1, '<a name="A"></a>x')], [toc("A", "A"), toc("Z", "Lost")])
    lost = [s for s in out if s["link_id"] == "Z"]
    assert lost and lost[0]["anchor_found"] is False and lost[0]["text"] is None


def test_date_is_passed_through_not_interpreted():
    out = jsp.sections([page(1, '<a name="A"></a>x')], [toc("A", "circa Early 1830", "1830-01-01")])
    assert out[0]["toc_date"] == "1830-01-01"


def test_transcript_keeps_glossed_word_drops_note():
    # From History, circa Summer 1832: "Kees" is transcript, the gloss is editorial.
    frag = (
        '<span class="josephswriting">the </span><aside class="popup-wrapper" id="1">'
        '<a href="#1" class="reference staticPopup" title="Keys">'
        '<span class="josephswriting">Kees</span></a><div class="popup-content">'
        '<div class="note-data" isnote="Y"><p>Authority or knowledge of God.</p></div></div>'
        "</aside> of the kingdom"
    )
    text = jsp.transcript_text(frag)
    assert text.split() == ["the", "Kees", "of", "the", "kingdom"]


def test_transcript_drops_footnote_number_anchor():
    frag = (
        'marvilous experience<aside class="popup-wrapper" id="2">'
        '<a href="#2" class="editorial-note-static staticPopup" title="Note" name="trans1">'
        '<span id="documenttrans1">1</span></a><div class="popup-content">'
        '<div class="note-data editorial-footnote" isnote="Y"><p>OED.</p></div></div></aside> and'
    )
    assert jsp.transcript_text(frag).split() == ["marvilous", "experience", "and"]


def test_transcript_words_hand_split_and_brackets():
    frag = (
        '<p><span class="josephswriting">to instruct</span><span class="josephswriting">ing'
        '</span> me [p. 2] in <span class="hide-this">Hatter. Born 1793.</span>religion</p>'
    )
    assert jsp.transcript_words(frag) == [
        ("to", True),
        ("instructing", True),
        ("me", False),
        ("in", False),
        ("religion", False),
    ]


def test_gap_marker_kept_in_text_but_not_counted():
    # ingest.extant reads lost leaves from these; they must survive transcript_text.
    frag = (
        'and <span class="italic note-data editorial-comment" isnote="Y">2 pages not extant</span>]'
        ' then <span class="note-data" isnote="Y"><div>Editorial Note</div></span>more'
    )
    frag = frag.replace("and <span", "and [<span")
    assert "[2 pages not extant]" in jsp.transcript_text(frag)
    assert "Editorial" not in jsp.transcript_text(frag)
    assert [w for w, _ in jsp.transcript_words(frag)] == ["and", "then", "more"]
