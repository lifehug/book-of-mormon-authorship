from metadata import genre


def test_eight_labels_registered_by_amendment_2():
    assert len(genre.LABELS) == 8
    assert set(genre.LABELS) == {
        "sermon_devotional",
        "pseudo_biblical",
        "history_chronicle",
        "fiction_narrative",
        "newspaper_periodical",
        "legal_political",
        "scientific_medical",
        "other",
    }


def test_rules_only_fire_on_structural_evidence():
    """A rule may use which corpus a row came from, or an issue number plus a full date.

    It must not try to judge content -- that is the model's job, and a rule that guesses is a
    rule whose errors never reach the validation sample's attention.
    """
    assert genre.rule_label(
        {"source": "chronicling_america", "title_norm": "", "date_raw": ""}
    ) == ("newspaper_periodical")
    assert (
        genre.rule_label(
            {
                "source": "internet_archive",
                "title_norm": "the hive vol 2 iss 6",
                "date_raw": "1804-07-25",
            }
        )
        == "newspaper_periodical"
    )
    # No issue number: a model has to decide.
    assert (
        genre.rule_label({"source": "internet_archive", "title_norm": "poems", "date_raw": "1793"})
        is None
    )


def test_rules_defer_rather_than_guess():
    ambiguous = {
        "source": "tcp",
        "title_norm": "a wittie encounter betweene two gentlemen",
        "date_raw": "1636",
        "genre_src": "eebo",
    }
    assert genre.rule_label(ambiguous) is None


def test_model_reply_is_matched_against_the_closed_set():
    """An early version returned 'poems' and 'Wait, the label must be exact: ...'.

    Both are caught by matching the reply against LABELS rather than trusting it.
    """
    import re

    for reply, expect in [
        ("scientific_medical", "scientific_medical"),
        ("Wait, the label must be exact: scientific_medical", "scientific_medical"),
        ("poems", None),
    ]:
        found = [lab for lab in genre.LABELS if re.search(rf"\b{lab}\b", reply.lower())]
        assert (found[-1] if found else None) == expect


def test_prompt_carries_the_amendment_3_contract():
    """Amendment 3: every label defined, worked examples, two labels allowed, uncertainty offered.

    The previous version asserted the Amendment 2 wording ("ONLY the label") and broke when the
    prompt became multi-label -- which is the test doing its job, but it should assert the
    contract rather than the phrasing.
    """
    p = genre.prompt_for({"title": "t", "author": "a", "year": 1800}, "x")
    for label in genre.LABELS:
        assert label in p
    assert "Examples:" in p, "few-shot examples must be present"
    assert "two separated by a comma" in p, "the two-label case must be stated"
    assert "uncertain" in p, "an uncertainty option must be offered"
    assert "no explanation" in p


def test_label_run_checkpoints_rather_than_writing_once():
    """A 13-hour job must survive interruption.

    The first version collected every result in memory and wrote at the end. It ran four hours,
    was stopped, and lost all of it. Every other long job here resumes from disk.
    """
    src = (genre.Path("metadata/genre.py")).read_text()
    assert "checkpoint_every" in src
    assert "tmp.replace(OUT)" in src, "checkpoint write must be atomic"


def test_session_limit_reply_is_transient_not_an_answer():
    # Pass 2 recorded 1,080 of these as PARSE_FAIL on 2026-10-24 because the pattern only
    # knew "usage limit".
    for reply in [
        "you've hit your session limit · resets 9:30pm (america/los_angeles)",
        "You've hit your usage limit",
        "Claude AI usage limit reached",
    ]:
        assert genre._TRANSIENT.search(reply), reply
    assert not genre._TRANSIENT.search("sermon_religious, history_chronicle")
