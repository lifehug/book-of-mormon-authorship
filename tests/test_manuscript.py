"""BOM-34: the manuscript correction catalog and the 6.3 scribe/narrator comparison."""

import random

from eval.scribes import assess, verdict
from manuscript.corrections import events, kind_of, soundex

ZW = "​"


def test_kind_of_and_soundex() -> None:
    assert kind_of("where", "were") == "homophone"
    assert kind_of("There", "their") == "homophone"
    assert soundex("Robert") == soundex("Rupert") == "R163"
    assert kind_of("Robert", "Rupert") == "sound_alike"
    assert kind_of("wich", "with") == "spelling"
    assert kind_of("in", "unto") == "other"


def test_events_from_markup() -> None:
    page = {"scribes": [{"name": "Oliver Cowdery"}, {"name": "John  Whitmer"}],
            "expanded_html": (
                'and they <span class="deleted">where</span> &lt;' + ZW + "were" + ZW + "&gt; "
                'about to go <span class="deleted">migh</span> mightest '
                '<a class="new-scribe-note staticPopup" name="t1"></a> unto '
                '&lt;' + ZW + "the" + ZW + '&gt; land <span class="deleted">cattle</span> of '
                "Zarahemla")}  # fmt: skip
    evs, end = events(page, "Oliver Cowdery")
    assert [(e["event"], e["type"], e["scribe"]) for e in evs] == [
        ("substitution", "homophone", "Oliver Cowdery"),
        ("false_start", "false_start", "Oliver Cowdery"),
        ("insertion", "insertion", "John Whitmer"),
        ("deletion", "deletion", "John Whitmer"),
    ]
    assert end == "John Whitmer"


def test_scribe_comparison_on_synthetic_text() -> None:
    rng = random.Random(0)
    common = "the and of to in that it was he for".split()
    styles = {"A": "unto behold yea".split(), "B": "upon therefore nay".split()}

    def doc(style: str) -> list[str]:
        return [rng.choice(common + styles[style] * 3) for _ in range(400)]

    labels = ["A"] * 6 + ["B"] * 6
    docs = [doc(lab) for lab in labels]
    good = assess(docs, labels, mfw=12, perms=20, seed=1, min_frac=0.0)
    assert good["accuracy"] >= 0.9 and good["p"] < 0.1
    scrambled = ["A", "B"] * 6  # labels unrelated to style
    bad = assess(docs, scrambled, mfw=12, perms=20, seed=1, min_frac=0.0)
    assert bad["accuracy"] < good["accuracy"]
    v = verdict({"narrator": good, "scribe": bad, "dictation_order": bad}, 0.8)
    assert v["separable"] and v["chance_corrected_ranking"][0] == "narrator"
