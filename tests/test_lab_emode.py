"""BOM-119: the syntax extractors count what they say and leave out what they say."""

from lab.emode import auc, did_hits, did_n, measure, past_count, pre1700_author, rates, tokens

LEX = frozenset({"go", "take", "eat", "rejoice", "call", "love", "smite", "come"})


def kinds(text: str) -> list[str]:
    return [k for _, k in did_hits(tokens(text), LEX, 3)]


def test_affirmative_did_is_counted_by_kind():
    assert kinds("And they did go forth.") == ["adjacent"]
    assert kinds("And they did also go forth.") == ["adverbial"]
    assert kinds("And thus did they rejoice.") == ["subject"]
    assert kinds("And so did the people rejoice.") == ["subject"]


def test_negatives_questions_and_main_verb_did_are_not():
    assert kinds("They did not go.") == []
    assert kinds("Did they go forth?") == []
    assert kinds("Why did he take it?") == []
    assert kinds("He did all these things.") == []
    assert kinds("Neither did they go.") == ["neither"]


def test_simple_past_skips_participles_and_adjectives():
    lex = LEX
    past, ctp = past_count(tokens("He came and called them. It came to pass."), lex)
    assert (past, ctp) == (3, 1)
    past, _ = past_count(tokens("They had called him; the beloved son was loved."), lex)
    assert past == 0


def test_measure_and_rates():
    c = measure(
        "And they did go. They went and called. The more part of them caused that they "
        "should come. He commanded them to go. The men which came.",
        LEX,
        3,
    )
    assert did_n(c) == 1
    assert c["more_part"] == 1 and c["cause_fin"] == 1 and c["cmd_inf"] == 1
    assert c["rel_which"] == 1
    r = rates(c)
    assert r["cause_finite"] == 1.0 and r["command_finite"] == 0.0
    assert rates(c, min_past=100)["did_rate"] is None


def test_auc_and_reprint_rule():
    assert auc([3, 4], [1, 2]) == 1.0
    cfg = {"lab": {"emode": {"reprint_death_before": 1700, "reprint_birth_before": 1650}}}
    assert pre1700_author("Barrow, Isaac, 1630-1677.", cfg)
    assert not pre1700_author("Combe, William, 1742-1823.", cfg)
    assert not pre1700_author(None, cfg)
