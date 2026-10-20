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


def test_prompt_names_every_label_and_forbids_explanation():
    p = genre.prompt_for({"title": "t", "author": "a", "year": 1800}, "x")
    for label in genre.LABELS:
        assert label in p
    assert "ONLY the label" in p
