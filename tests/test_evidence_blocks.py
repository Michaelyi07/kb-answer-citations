"""Evidence-block assembly (rework major 2): [n]-ordered concatenation with
doc title, version, heading_path and verbatim text."""

from __future__ import annotations

import pytest

from kb_answer.evidence import build_evidence_blocks, filter_visible_evidences


@pytest.fixture(scope="module")
def ev_n01() -> list[dict]:
    from tests.conftest import ROOT
    import json

    sets = json.loads((ROOT / "fixtures" / "evidence_sets.json").read_text(encoding="utf-8"))["sets"]
    return next(s for s in sets if s["evidence_set_id"] == "EV-N01")["evidences"]


def test_blocks_in_n_order_with_header_and_text(ev_n01: list[dict]) -> None:
    out = build_evidence_blocks(ev_n01)
    parts = out.split("\n\n")
    assert len(parts) == len(ev_n01)
    for ev, part in zip(ev_n01, parts):
        header, text = part.split("\n", 1)
        assert header.startswith(f"[{ev['n']}] 《{ev['doc_title']}》 {ev['version']}")
        assert ev["doc_title"] and ev["version"] and ev["heading_path"]
        assert " > ".join(ev["heading_path"]) in header
        assert text == ev["text"]  # verbatim


def test_blocks_sorted_by_n_even_if_input_unordered(ev_n01: list[dict]) -> None:
    shuffled = [ev_n01[2], ev_n01[0], ev_n01[1]]
    out = build_evidence_blocks(shuffled)
    positions = [out.index(f"[{ev['n']}] 《") for ev in ev_n01]
    assert positions == sorted(positions)


def test_block_numbers_are_contiguous(ev_n01: list[dict]) -> None:
    out = build_evidence_blocks(ev_n01)
    ns = [int(m) for m in __import__("re").findall(r"^\[(\d+)\] 《", out, __import__("re").M)]
    assert ns == list(range(1, len(ev_n01) + 1))


def test_empty_evidence_gives_empty_string() -> None:
    assert build_evidence_blocks([]) == ""


def test_filter_visible_drops_out_of_scope_evidence() -> None:
    evs = [
        {"n": 1, "doc_title": "t", "version": "v1", "heading_path": ["a"], "text": "x",
         "visible_scope": None},
        {"n": 2, "doc_title": "h", "version": "v1", "heading_path": ["b"], "text": "y",
         "visible_scope": "org:other"},
    ]
    kept = filter_visible_evidences(evs, "org:mem-017")
    assert [ev["n"] for ev in kept] == [1]
    # matching scope keeps the scoped evidence
    kept2 = filter_visible_evidences(evs, "org:other")
    assert {ev["n"] for ev in kept2} == {1, 2}
    # no requester scope -> only public evidence
    kept3 = filter_visible_evidences(evs, None)
    assert [ev["n"] for ev in kept3] == [1]
