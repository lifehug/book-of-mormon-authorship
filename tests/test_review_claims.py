"""Pure logic of the simulated review (BOM-38) and the claims table (BOM-42)."""

from eval.claims import build, evidence
from review.simulate import header, parse, response_plan

REPLY = """## Summary
It claims things.
## Major points
1. The rule is too strict.
2. Chunks are not independent.
## Minor points
1. A typo.
## Recommendation
Major revision, because of point 1.
"""


def test_parse_shape() -> None:
    r = parse(REPLY)
    assert r and r["major"] == ["The rule is too strict.", "Chunks are not independent."]
    assert r["minor"] == ["A typo."] and r["recommendation"] == "major revision"
    assert parse("## Summary\nx\n## Recommendation\naccept") is None  # sections missing
    assert parse(REPLY.replace("Major revision", "Fine")) is None  # no recognised verdict


def test_header_and_plan_label_simulated() -> None:
    assert "SIMULATED" in header("statistician", "m", "abc")
    plan = response_plan({"statistician": parse(REPLY)})
    assert plan.count("[pending]") == 3 and "SIMULATED" in plan


def test_claims_untestable_and_pending() -> None:
    reg = {
        "sources": {"s": {"stance": "critical"}},
        "claims": [
            {"id": "a", "source": "s", "testable": "none", "reason": "genetics", "verdict": None},
            {
                "id": "b",
                "source": "s",
                "testable": "full",
                "verdict": None,
                "evidence": ["file:/no/such/file.json"],
            },
        ],
    }
    doc = build(reg)
    assert doc["by_status"] == {"untestable": 1, "pending": 1}
    assert doc["rows"][1]["evidence"][0]["status"] == "pending"
    assert evidence("file:/no/such/file.json")["status"] == "pending"
