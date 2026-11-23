"""Markdown renderer for kb_answer outputs.

Renders {points:[{text, citations}], refused} to Markdown:
- normal answer : one bullet per point; the [n] marks in the point text are
                  strictly validated against citations (any mismatch raises)
                  and the answer is rendered with a "## 引用来源" section
- refused answer: exactly the fixed refusal line 「知识库中没有找到」
"""

from __future__ import annotations

import re
from typing import Any

REFUSAL_TEXT = "知识库中没有找到"

_MARK = re.compile(r"\[(\d+)\]")


def _extract_marks(text: str) -> list[int]:
    return [int(m) for m in _MARK.findall(text)]


def _check_marks_match_citations(text: str, citations: list[int]) -> None:
    """Strict consistency: the [n] marks in the point text must match the
    citations list exactly (same set); any mismatch is an error."""
    marks = _extract_marks(text)
    if sorted(set(marks)) != sorted(set(citations)):
        raise ValueError(
            f"citation marks {marks} in text do not match citations {citations}"
        )


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
        _check_marks_match_citations(point["text"], point["citations"])
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
