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
