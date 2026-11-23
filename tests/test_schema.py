"""AC1: all 20 recorded responses pass Schema validation and every point has >= 1 citation."""

from __future__ import annotations

import pytest

from kb_answer.schema import validate_answer


def test_there_are_exactly_20_records(recorded: list[dict]) -> None:
    assert len(recorded) == 20


def test_all_20_records_valid(recorded: list[dict]) -> None:
    # AC1 part 1: every recorded response validates against the Draft 2020-12 schema.
    for rec in recorded:
        validate_answer(rec["response"])  # raises on violation


def test_every_point_has_citation(recorded: list[dict]) -> None:
    # AC1 part 2: every point of every non-refused response has at least 1 citation.
    # refused=true responses are exempt (their points array must be empty, enforced
    # by the schema's if/then branch -- verified above by validate_answer).
    checked = 0
    for rec in recorded:
        if rec["response"]["refused"]:
            assert rec["response"]["points"] == []
            continue
        for point in rec["response"]["points"]:
            assert len(point["citations"]) >= 1, f"{rec['response_id']}: point without citation"
            checked += 1
    assert checked > 0


def test_refused_records_have_empty_points(recorded: list[dict]) -> None:
    refused = [r for r in recorded if r["response"]["refused"]]
    assert len(refused) == 4
    for rec in refused:
        assert rec["response"]["points"] == []


def test_schema_rejects_point_without_citation() -> None:
    # Guard: a point missing citations must fail validation (negative case).
    bad = {"points": [{"text": "claim without citation", "citations": []}], "refused": False}
    with pytest.raises(Exception):
        validate_answer(bad)


def test_schema_rejects_refused_with_points() -> None:
    # Guard: refused=true with non-empty points must fail validation (negative case).
    bad = {"points": [{"text": "x[1]", "citations": [1]}], "refused": True}
    with pytest.raises(Exception):
        validate_answer(bad)
