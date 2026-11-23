"""Renderer behaviour (rework majors 4+5): strict [n]-mark/citation consistency,
plus full-corpus assertions over all 20 recorded responses."""

from __future__ import annotations

import re

import pytest

from kb_answer.renderer import REFUSAL_TEXT, _extract_marks, render_markdown


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


def test_render_rejects_marks_missing_from_citations() -> None:
    # text carries [1][2] but citations only lists [1] -> mismatch error
    answer = {"points": [{"text": "陈述一句[1][2]", "citations": [1]}], "refused": False}
    evs = [{"n": 1, "doc_title": "t", "version": "v1", "heading_path": ["a"], "text": "..."},
           {"n": 2, "doc_title": "t2", "version": "v1", "heading_path": ["b"], "text": "..."}]
    with pytest.raises(ValueError):
        render_markdown(answer, evs)


def test_render_rejects_citation_missing_from_marks() -> None:
    # citations lists [1][2] but the text only marks [1] -> mismatch error
    answer = {"points": [{"text": "陈述一句[1]", "citations": [1, 2]}], "refused": False}
    evs = [{"n": 1, "doc_title": "t", "version": "v1", "heading_path": ["a"], "text": "..."},
           {"n": 2, "doc_title": "t2", "version": "v1", "heading_path": ["b"], "text": "..."}]
    with pytest.raises(ValueError):
        render_markdown(answer, evs)


def test_all_20_recorded_answers_render_with_correct_marks(
    recorded: list[dict], sets_by_id: dict[str, dict]
) -> None:
    # rework major 5: over ALL 20 recorded responses, every citation falls inside
    # that set's evidence numbering and every text mark matches its citations.
    checked_points = 0
    for rec in recorded:
        evs = sets_by_id[rec["evidence_set_id"]]["evidences"]
        valid_ns = {ev["n"] for ev in evs}
        response = rec["response"]
        if response["refused"]:
            continue
        for point in response["points"]:
            assert set(point["citations"]) <= valid_ns, (
                f"{rec['response_id']}: citation outside evidence range"
            )
            marks = _extract_marks(point["text"])
            assert set(marks) == set(point["citations"]), (
                f"{rec['response_id']}: marks {marks} != citations {point['citations']}"
            )
            md = render_markdown(response, evs)  # must render without error
            bullet = [ln for ln in md.splitlines()
                      if ln.startswith("- ") and point["text"] in ln]
            assert bullet, f"{rec['response_id']}: rendered bullet not found"
            for n in point["citations"]:
                assert f"[{n}]" in bullet[0]
            checked_points += 1
    assert checked_points == 24  # 16 non-refused responses x 1-3 points, exact


def test_render_references_sorted(sets_by_id: dict[str, dict], recorded: list[dict]) -> None:
    rec = next(r for r in recorded if r["response_id"] == "resp-n01")
    evs = sets_by_id[rec["evidence_set_id"]]["evidences"]
    md = render_markdown(rec["response"], evs)
    ref_nums = [int(m) for m in re.findall(r"^\[(\d+)\]", md, re.M)]
    assert ref_nums == sorted(ref_nums)
