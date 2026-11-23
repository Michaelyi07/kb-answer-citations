"""AC4: every answer records the prompt version and model name; recorder round-trips."""

from __future__ import annotations

import pytest

from kb_answer import PROMPT_ID, PROMPT_VERSION
from kb_answer.recorder import load_records, make_record, response_digest, write_records


def test_every_record_has_prompt_version_and_model_name(recorded: list[dict]) -> None:
    assert len(recorded) == 20
    for rec in recorded:
        assert rec["prompt_id"] == PROMPT_ID, rec["response_id"]
        assert rec["prompt_version"] == PROMPT_VERSION, rec["response_id"]
        assert rec["prompt_version"] == 1, rec["response_id"]
        assert isinstance(rec["model_name"], str) and rec["model_name"], rec["response_id"]
        assert isinstance(rec["model_version"], str) and rec["model_version"], rec["response_id"]
        assert rec["recorded_at"], rec["response_id"]


def test_recorder_round_trip(recorded: list[dict], tmp_path) -> None:
    # write -> read -> compare, for all 20 records through the recorder interface.
    out = tmp_path / "records.jsonl"
    full = [
        make_record(
            rec["response"],
            rec["model_name"],
            rec["model_version"],
            prompt_id=rec["prompt_id"],
            prompt_version=rec["prompt_version"],
            recorded_at=rec["recorded_at"],
        )
        for rec in recorded
    ]
    write_records(full, out)
    loaded = load_records(out)
    assert loaded == full
    assert len(loaded) == 20


def test_record_digest_is_stable() -> None:
    response = {"points": [{"text": "x[1]", "citations": [1]}], "refused": False}
    a = make_record(response, "m", "v", recorded_at="2026-11-20T00:00:00+00:00")
    b = make_record(response, "m", "v", recorded_at="2026-11-20T00:00:00+00:00")
    assert a == b
    assert a["response_digest"] == response_digest(response)


def test_digest_changes_with_response() -> None:
    r1 = {"points": [{"text": "x[1]", "citations": [1]}], "refused": False}
    r2 = {"points": [{"text": "y[1]", "citations": [1]}], "refused": False}
    assert response_digest(r1) != response_digest(r2)


def test_record_requires_model_name() -> None:
    with pytest.raises(ValueError):
        make_record({"points": [], "refused": True}, "", "v")


def test_write_rejects_incomplete_record(tmp_path) -> None:
    bad = {"prompt_id": PROMPT_ID}  # missing required fields
    with pytest.raises(ValueError):
        write_records([bad], tmp_path / "x.jsonl")
