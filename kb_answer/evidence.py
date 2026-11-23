"""Evidence-block assembly and per-user visibility filtering.

- build_evidence_blocks: concatenate evidence blocks in [n] order, each carrying
  doc title, version and heading_path plus the original text (order scope).
- filter_visible_evidences: generation-boundary visibility gate -- evidence that
  is outside the requester's visible scope never enters the prompt; an answer
  citing it is rejected downstream (gateway.generate_answer).
"""

from __future__ import annotations

from typing import Any


def build_evidence_blocks(evidences: list[dict[str, Any]]) -> str:
    """Concatenate evidence blocks in [n] order.

    Format per block (order scope, S3-KB-020):
        [n] 《doc_title》 version > heading_path
        evidence text verbatim
    """
    if not evidences:
        return ""
    ordered = sorted(evidences, key=lambda e: e["n"])
    blocks = []
    for ev in ordered:
        path = " > ".join(ev.get("heading_path", []))
        blocks.append(f"[{ev['n']}] 《{ev['doc_title']}》 {ev['version']} > {path}\n{ev['text']}")
    return "\n\n".join(blocks)


def filter_visible_evidences(
    evidences: list[dict[str, Any]], requester_scope: str | None
) -> list[dict[str, Any]]:
    """Keep only evidence the requester is allowed to see.

    Per-evidence rule: an evidence without a visible_scope field is public
    within the call; one with visible_scope is only visible to a requester
    whose scope matches exactly. Cross-tenant documents are therefore dropped
    before prompt assembly, so answers can never cite them.
    """
    out = []
    for ev in evidences:
        scope = ev.get("visible_scope")
        if not scope or (requester_scope and scope == requester_scope):
            out.append(ev)
    return out
