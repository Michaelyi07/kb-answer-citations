"""Visibility gate (rework major 6): evidence outside the requester's scope
never enters the prompt; an answer citing it is rejected (refused)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from kb_answer.gateway import S5GatewayStub, generate_answer
from kb_answer.review_queue import L0ReviewQueue

CASES = "fixtures/visibility_cases.json"


@pytest.fixture(scope="module")
def cases() -> list[dict]:
    return json.loads(Path(CASES).read_text(encoding="utf-8"))["cases"]


def _gateway_for(cases: list[dict]) -> S5GatewayStub:
    stub = S5GatewayStub.__new__(S5GatewayStub)  # build from the case file layout
    stub.records = {
        c["case_id"]: {
            "response": c["recorded_response"]["response"],
            "model_name": c["recorded_response"]["model_name"],
            "model_version": c["recorded_response"]["model_version"],
            "recorded_at": c["recorded_response"]["recorded_at"],
        }
        for c in cases
    }
    return stub


def _queue() -> L0ReviewQueue:
    return L0ReviewQueue(Path(tempfile.mkdtemp()) / "q.jsonl")


def test_visible_case_passes_and_hides_cross_tenant_block(cases: list[dict]) -> None:
    ok = next(c for c in cases if c["case_id"] == "VIS-OK")
    result = generate_answer(
        ok["question"], {**ok, "evidence_set_id": "VIS-OK"},
        gateway=_gateway_for(cases), queue=_queue(),
        requester_scope=ok["requester_scope"],
    )
    # the cross-tenant block (n=2) must not enter the prompt
    assert result["visible_evidence_ids"] == [1]
    assert "[2] 《会员预订摘录（外部租户）》" not in result["prompt"]
    assert "A 科技公司" not in result["prompt"]
    # the answer cites only the public block and passes as recorded
    assert result["response"]["refused"] is False
    assert result["response"]["points"][0]["citations"] == [1]


def test_leak_case_citing_hidden_evidence_is_refused(cases: list[dict]) -> None:
    leak = next(c for c in cases if c["case_id"] == "VIS-LEAK")
    result = generate_answer(
        leak["question"], {**leak, "evidence_set_id": "VIS-LEAK"},
        gateway=_gateway_for(cases), queue=_queue(),
        requester_scope=leak["requester_scope"],
    )
    # the recorded response cited the hidden block [2]; the pipeline must refuse
    assert result["response"] == {"points": [], "refused": True}
    assert result["record"]["response"]["refused"] is True


def test_leaked_answer_never_reaches_the_queue_unrefused(cases: list[dict]) -> None:
    leak = next(c for c in cases if c["case_id"] == "VIS-LEAK")
    queue = _queue()
    result = generate_answer(
        leak["question"], {**leak, "evidence_set_id": "VIS-LEAK"},
        gateway=_gateway_for(cases), queue=queue,
        requester_scope=leak["requester_scope"],
    )
    regs = queue.load()
    assert len(regs) == 1
    # what is registered is the refused answer, never the leaking raw response
    assert regs[0]["item"]["response"] == {"points": [], "refused": True}
    assert regs[0]["level"] == "L0" and regs[0]["internal_only"] is True
