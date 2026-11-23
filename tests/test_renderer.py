"""Renderer behaviour: bullets with [n] marks, references section, refusal line."""

from __future__ import annotations

import re

import pytest

from kb_answer.renderer import REFUSAL_TEXT, render_markdown


def test_render_normal_answer(sets_by_id: dict[str, dict], recorded: list[dict]) -> None:
    rec = next(r for r in recorded if r["response_id"] == "resp-n01")
    evs = sets_by_id[rec["evidence_set_id"]]["evidences"]
    md = render_markdown(rec["response"], evs)
    lines = md.splitlines()
    # one bullet per point, each carrying an [n] mark
    bullets = [ln for ln in lines if ln.startswith("- ")]
    assert len(bullets) == len(rec["response"]["points"])
    for point, bullet in zip(rec["response"]["points"], bullets):
        for n in point["citations"]:
            assert f"[{n}]" in bullet
    # references section lists each cited evidence with title/version/heading_path
    assert "## 引用来源" in md
    ev1 = evs[0]
    assert f"[{ev1['n']}] 《{ev1['doc_title']}》 {ev1['version']}" in md


def test_render_refusal() -> None:
    answer = {"points": [], "refused": True}
    assert render_markdown(answer, []) == REFUSAL_TEXT
    assert REFUSAL_TEXT == "知识库中没有找到"


def test_refusal_text_matches_prompt(prompt_text: str) -> None:
    assert REFUSAL_TEXT in prompt_text


def test_render_rejects_out_of_range_citation() -> None:
    answer = {"points": [{"text": "x[9]", "citations": [9]}], "refused": False}
    evs = [{"n": 1, "doc_title": "t", "version": "v1", "heading_path": ["a"], "text": "..."}]
    with pytest.raises(ValueError):
        render_markdown(answer, evs)


def test_render_references_sorted(sets_by_id: dict[str, dict], recorded: list[dict]) -> None:
    rec = next(r for r in recorded if r["response_id"] == "resp-n01")
    evs = sets_by_id[rec["evidence_set_id"]]["evidences"]
    md = render_markdown(rec["response"], evs)
    ref_nums = [int(m) for m in re.findall(r"^\[(\d+)\]", md, re.M)]
    assert ref_nums == sorted(ref_nums)
