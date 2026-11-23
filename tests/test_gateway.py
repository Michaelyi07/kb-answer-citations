"""Gateway call path (rework blocker 1): prompt assembly -> stub call -> schema
validation -> record -> L0 registration, covered end to end."""

from __future__ import annotations

import pytest

from kb_answer import PROMPT_ID, PROMPT_VERSION
from kb_answer.evidence import build_evidence_blocks
from kb_answer.gateway import S5GatewayStub, assemble_prompt, generate_answer
from kb_answer.review_queue import L0ReviewQueue
from kb_answer.recorder import load_records
from kb_answer.schema import is_valid_answer

RECORDED = "fixtures/recorded_responses.json"


@pytest.fixture()
def gateway() -> S5GatewayStub:
    return S5GatewayStub(RECORDED)


def test_replay_stub_returns_recorded_response(gateway: S5GatewayStub) -> None:
    gw = gateway.call("any prompt", evidence_set_id="EV-P01")
    assert gw["model_name"] == "Qwen2.5-14B-Instruct"
    assert gw["model_version"] == "2026-06"
    assert is_valid_answer(gw["response"])


def test_stub_rejects_unknown_evidence_set(gateway: S5GatewayStub) -> None:
    with pytest.raises(KeyError):
        gateway.call("any prompt", evidence_set_id="EV-NOPE")


def test_assemble_prompt_includes_evidence_blocks() -> None:
    from tests.conftest import ROOT
    import json

    sets = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))["sets"]
    ev01 = next(s for s in sets if s["evidence_set_id"] == "EV-P01")
    prompt = assemble_prompt(ev01["question"], ev01["evidences"])
    assert prompt.startswith("问题：大型会议室租一小时多少钱？")
    assert "[1] 《会议室与场地使用价目表》 v3.0 > 会议室 > 时租价格" in prompt
    assert "大型会议室（12 人以上）工作日时租为 ￥120/小时" in prompt
    assert "[2] 《会议室与场地使用价目表》 v3.0 > 会议室 > 预订方式" in prompt


def test_pipeline_all_20_answers_recorded_and_registered(
    gateway: S5GatewayStub, tmp_path
) -> None:
    from tests.conftest import ROOT
    import json

    sets = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))["sets"]
    queue = L0ReviewQueue(tmp_path / "queue.jsonl")
    for s in sets:
        result = generate_answer(s["question"], s, gateway=gateway, queue=queue)
        rec = result["record"]
        assert rec["prompt_id"] == PROMPT_ID
        assert rec["prompt_version"] == PROMPT_VERSION
        assert rec["model_name"] and rec["model_version"]
        assert is_valid_answer(result["response"])
    # every answer registered at L0, internal-only dispatch, never outbound
    registrations = queue.load()
    assert len(registrations) == 20
    assert all(r["level"] == "L0" for r in registrations)
    assert all(r["internal_only"] is True for r in registrations)
    assert all(r["dispatch"] == "internal_review" for r in registrations)
    assert all(r["audience"] == "staff_only" for r in registrations)


def test_pipeline_records_round_trip_via_recorder(gateway: S5GatewayStub, tmp_path) -> None:
    import json

    from tests.conftest import ROOT

    sets = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))["sets"]
    queue = L0ReviewQueue(tmp_path / "queue.jsonl")
    path = tmp_path / "records.jsonl"
    for s in sets:
        result = generate_answer(s["question"], s, gateway=gateway, queue=queue)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result["record"], ensure_ascii=False, sort_keys=True) + "\n")
    loaded = load_records(path)
    assert len(loaded) == 20
    assert all(r["prompt_version"] == PROMPT_VERSION for r in loaded)


def test_evidence_blocks_concatenated_in_prompt(gateway: S5GatewayStub, tmp_path) -> None:
    # the assembled prompt (what the gateway actually receives) carries the
    # [n]-ordered blocks with title/version/heading_path for multi-evidence sets
    import json

    from tests.conftest import ROOT

    sets = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))["sets"]
    ev_n01 = next(s for s in sets if s["evidence_set_id"] == "EV-N01")  # 3 evidence blocks
    result = generate_answer(ev_n01["question"], ev_n01, gateway=gateway,
                             queue=L0ReviewQueue(tmp_path / "q.jsonl"))
    assert result["prompt"].count("[1] 《") == 1
    assert result["prompt"].count("[2] 《") == 1
    assert result["prompt"].count("[3] 《") == 1
    assert build_evidence_blocks([]) == ""
