"""Shared fixtures: 20 evidence sets, 20 recorded gateway responses, prompt path."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def evidence_sets() -> list[dict]:
    data = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))
    return data["sets"]


@pytest.fixture(scope="session")
def recorded() -> list[dict]:
    data = json.loads(
        (ROOT / "fixtures" / "recorded_responses.json").read_text(encoding="utf-8")
    )
    return data["records"]


@pytest.fixture(scope="session")
def prompt_text() -> str:
    return (ROOT / "prompts" / "kb_answer" / "v1.md").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def sets_by_id(evidence_sets: list[dict]) -> dict[str, dict]:
    return {s["evidence_set_id"]: s for s in evidence_sets}
