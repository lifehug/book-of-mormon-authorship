"""BOM-121: the play parser, the spread measure and the known-answer arithmetic."""

import numpy as np

from lab import voices
from metadata import config

CFG = config.load()

PLAY = """Enter Sir Thomas.
 Bor.
How how? Whats the matter?
Enter Aretina.
 Are.
I am angry with my self,
 FINIS.
Nothing more.
 Bor.
Angry sweet heart?
"""


def test_parse_play_keeps_speech_and_drops_stage_and_non_speakers() -> None:
    by, ordered = voices.parse_play(PLAY, CFG)
    assert by["bor"] == "how how whats the matter angry sweet heart".split()
    assert by["are"] == "i am angry with my self".split()
    assert "finis" not in by and "nothing" not in ordered and "enter" not in ordered
    assert len(ordered) == len(by["bor"]) + len(by["are"])


def test_genre_of() -> None:
    assert voices.genre_of("The lady of pleasure A comedie") == "comedy"
    assert voices.genre_of("A tragi-comedy") == "tragedy"
    assert voices.genre_of("A masque") == "other"


def test_auc_and_share_below() -> None:
    assert voices.auc([2, 3], [0, 1]) == 1.0
    assert voices.auc([0, 1], [2, 3]) == 0.0
    assert voices.auc([1], [1]) == 0.5
    assert voices.share_below([1, 2, 3, 4], 4) == 0.875
    assert voices.share_below([1, 2, 3, 4], 0) == 0.0


def test_spread_is_larger_for_more_different_voices() -> None:
    class C(voices.Ctx):
        def __init__(self) -> None:
            self.pcs = np.eye(3, 4)

    c = C()
    near = [np.zeros(4), np.ones(4) * 0.1, np.ones(4) * 0.2]
    far = [np.zeros(4), np.ones(4), np.ones(4) * 2.0]
    assert c.spread(far)[0] > c.spread(near)[0]
    assert abs(c.spread([np.zeros(4), np.ones(4)])[0] - 1.0) < 1e-9


def test_settings_are_in_the_config_and_not_in_the_code() -> None:
    t = CFG["lab"]["voices"]
    assert t["known_bar"] >= t["known_bar_genre"] > 0.5
    assert t["larger_share"] > t["typical_share"]
    assert t["sample_words"] > 0 and t["k_voices"] >= 3
