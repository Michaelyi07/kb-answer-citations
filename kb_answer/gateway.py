"""S5-GW gateway call path: prompt assembly -> stub call -> schema validation ->
record with prompt version + model name -> L0 queue registration.

The real model gateway (S5-GW) is out of scope for this order; S5GatewayStub
replays recorded responses through the same call signature, so swapping in the
real gateway later requires no prompt, schema or pipeline change (README
"S5-GW integration").
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kb_answer import PROMPT_ID, PROMPT_VERSION
from kb_answer.evidence import build_evidence_blocks, filter_visible_evidences
from kb_answer.recorder import make_record
from kb_answer.review_queue import L0ReviewQueue
from kb_answer.schema import validate_answer


class S5GatewayStub:
    """Recorded-response replay stub. call() mirrors the real gateway's shape:
    it receives the assembled prompt and returns the model output plus model
    identity, so the pipeline is identical for the real gateway."""

    def __init__(self, recorded_path: str | Path):
        data = json.loads(Path(recorded_path).read_text(encoding="utf-8"))
        self.records = {r["evidence_set_id"]: r for r in data["records"]}

    def call(
        self,
        prompt: str,
        *,
        evidence_set_id: str,
    ) -> dict[str, Any]:
        rec = self.records.get(evidence_set_id)
        if rec is None:
            raise KeyError(f"no recorded response for evidence set {evidence_set_id}")
        return {
            "response": rec["response"],
            "model_name": rec["model_name"],
            "model_version": rec["model_version"],
            "recorded_at": rec["recorded_at"],
        }


def assemble_prompt(question: str, evidences: list[dict[str, Any]]) -> str:
    """User-layer prompt: the question plus evidence blocks concatenated in [n]
    order (each with doc title, version, heading_path and verbatim text). The
    frozen system template is prompts/kb_answer/v1.md."""
    return f"问题：{question}\n\n证据块：\n{build_evidence_blocks(evidences)}"


def generate_answer(
    question: str,
    evidence_set: dict[str, Any],
    *,
    gateway: S5GatewayStub,
    queue: L0ReviewQueue,
    requester_scope: str | None = None,
) -> dict[str, Any]:
    """Full call path for one question.

    1. visibility gate: evidence outside requester_scope never enters the prompt
    2. assemble prompt (question + [n]-ordered evidence blocks)
    3. call the gateway stub -> recorded response
    4. schema validation (Draft 2020-12)
    5. visibility post-check: an answer citing evidence that was filtered out
       of the prompt is rejected (refused) -- other members' data never leaks
    6. record with prompt version + model name; register at L0 (internal only)
    """
    evidences = evidence_set["evidences"]
    visible = filter_visible_evidences(evidences, requester_scope)
    visible_ns = {ev["n"] for ev in visible}

    prompt = assemble_prompt(question, visible)
    gw = gateway.call(prompt, evidence_set_id=evidence_set["evidence_set_id"])
    response = gw["response"]

    validate_answer(response)

    leaked = any(
        n not in visible_ns
        for point in response["points"]
        for n in point["citations"]
    )
    if leaked:
        response = {"points": [], "refused": True}

    record = make_record(
        response,
        gw["model_name"],
        gw["model_version"],
        prompt_id=PROMPT_ID,
        prompt_version=PROMPT_VERSION,
        recorded_at=gw["recorded_at"],
    )
    registration = queue.register(
        record, question=question, evidence_set_id=evidence_set["evidence_set_id"]
    )
    return {
        "prompt": prompt,
        "response": response,
        "record": record,
        "registration": registration,
        "visible_evidence_ids": sorted(visible_ns),
    }
