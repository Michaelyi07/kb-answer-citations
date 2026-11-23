"""AC2: snapshot test of prompts/kb_answer/v1.md covering the three hard rules.

- test_prompt_snapshot_unchanged pins the full v1.md content via a hash-pinned
  fixture; any drift fails with a unified diff. v1 is frozen: wording changes
  must create v2 (see CHANGELOG), never edit v1 in place.
- The three per-rule tests each grep for that rule's operative sentence
  independently, so deleting any single rule sentence turns its test red
  (reverse check: remove a rule line from v1.md and the matching test fails).
"""

from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

import pytest

from tests.conftest import ROOT

SNAPSHOT = ROOT / "tests" / "fixtures" / "prompt_snapshot.json"

# Operative sentence of each of the three hard rules in v1.md.
RULE_MANDATORY_CITATION = "每个要点必须至少标注一个 [n] 引用"
RULE_REFUSAL_ON_INSUFFICIENT_EVIDENCE = "如果给定证据不足以回答问题，必须拒绝回答"
RULE_NO_AMOUNT_CALCULATION = "涉及价格、费用时只能原样引用证据原文中的数字"

ALL_RULES = (
    RULE_MANDATORY_CITATION,
    RULE_REFUSAL_ON_INSUFFICIENT_EVIDENCE,
    RULE_NO_AMOUNT_CALCULATION,
)


def _snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_prompt_snapshot_unchanged(prompt_text: str) -> None:
    snap = _snapshot()
    current_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    if prompt_text != snap["content"] or current_hash != snap["sha256"]:
        diff = "\n".join(
            difflib.unified_diff(
                snap["content"].splitlines(),
                prompt_text.splitlines(),
                fromfile="snapshot:v1.md",
                tofile="current:v1.md",
                lineterm="",
            )
        )
        pytest.fail(
            "prompts/kb_answer/v1.md drifted from the pinned snapshot.\n"
            "v1 is frozen; wording changes must create v2 + CHANGELOG entry.\n"
            f"Diff:\n{diff}"
        )


def test_snapshot_hash_matches_content() -> None:
    snap = _snapshot()
    assert (
        hashlib.sha256(snap["content"].encode("utf-8")).hexdigest() == snap["sha256"]
    ), "snapshot fixture is self-inconsistent (content/sha256 mismatch)"


@pytest.mark.parametrize(
    "sentence",
    ALL_RULES,
    ids=["mandatory_citation", "refusal_on_insufficient_evidence", "no_amount_calculation"],
)
def test_rule_present_in_prompt(prompt_text: str, sentence: str) -> None:
    assert sentence in prompt_text, f"rule operative sentence missing from v1.md: {sentence}"


def test_rule_mandatory_citation(prompt_text: str) -> None:
    assert RULE_MANDATORY_CITATION in prompt_text


def test_rule_refusal_on_insufficient_evidence(prompt_text: str) -> None:
    assert RULE_REFUSAL_ON_INSUFFICIENT_EVIDENCE in prompt_text


def test_rule_no_amount_calculation(prompt_text: str) -> None:
    assert RULE_NO_AMOUNT_CALCULATION in prompt_text


def test_all_three_rules_numbered_as_clauses(prompt_text: str) -> None:
    # The three rules appear as the numbered clauses 1./2./3. of the RULES section.
    rules_section = prompt_text.split("## 规则")[1].split("补充纪律")[0]
    assert "1." in rules_section and "2." in rules_section and "3." in rules_section
    for sentence in ALL_RULES:
        assert sentence in rules_section
