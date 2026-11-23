"""Markdown renderer for kb_answer outputs.

Renders {points:[{text, citations}], refused} to Markdown:
- normal answer : one bullet per point (text already carries [n] marks) +
                  a "## 引用来源" section listing cited evidence blocks
- refused answer: exactly the fixed refusal line 「知识库中没有找到」
"""

from __future__ import annotations

from typing import Any

REFUSAL_TEXT = "知识库中没有找到"


def _evidence_index(evidences: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    return {ev["n"]: ev for ev in evidences}


def render_markdown(answer: dict[str, Any], evidences: list[dict[str, Any]]) -> str:
    """Render an answer dict to Markdown given the evidence blocks for the call.

    evidences: list of {"n", "doc_title", "version", "heading_path", "text"}
               (heading_path is a list of heading strings).
    Raises ValueError on citation numbers outside the evidence blocks.
    """
    if answer.get("refused"):
        return REFUSAL_TEXT

    index = _evidence_index(evidences)
    lines: list[str] = []
    cited: set[int] = set()

    for point in answer.get("points", []):
        for n in point["citations"]:
            if n not in index:
                raise ValueError(f"citation [{n}] has no matching evidence block")
            cited.add(n)
        lines.append(f"- {point['text']}")

    if cited:
        lines.append("")
        lines.append("## 引用来源")
        for n in sorted(cited):
            ev = index[n]
            path = " > ".join(ev.get("heading_path", []))
            lines.append(f"[{n}] 《{ev['doc_title']}》 {ev['version']} > {path}")

    return "\n".join(lines)
