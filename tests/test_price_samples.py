"""AC3: price-sample answers quote figures verbatim from cited evidence, zero computed results."""

from __future__ import annotations

import re

NUM_TOKEN = re.compile(r"\d+(?:\.\d+)?")
# [n] citation marks are not answer figures; strip them before token extraction.
CITE_MARK = re.compile(r"\[\d+\]")


def answer_figures(text: str) -> list[str]:
    """Numeric tokens of an answer point, excluding [n] citation marks."""
    return NUM_TOKEN.findall(CITE_MARK.sub("", text))

# Calculator-detector: wording that indicates arithmetic performed on figures.
COMPUTE_PATTERN = re.compile(
    r"(合计|总计|总共|共计|折算|换算|折合|平均|相加|减去|乘以|除以|汇总|推算|估算|折后|优惠后)"
)


def _price_records(recorded: list[dict], sets_by_id: dict[str, dict]) -> list[dict]:
    return [
        rec
        for rec in recorded
        if "pricing" in sets_by_id[rec["evidence_set_id"]].get("tags", [])
    ]


def test_price_sample_sets_exist(evidence_sets: list[dict]) -> None:
    priced = [s for s in evidence_sets if "pricing" in s.get("tags", [])]
    assert len(priced) >= 5


def test_price_numbers_verbatim_in_cited_evidence(
    recorded: list[dict], sets_by_id: dict[str, dict]
) -> None:
    # Every numeric token in a price answer point must appear verbatim in the
    # original text of one of the evidence blocks that point cites.
    price_records = _price_records(recorded, sets_by_id)
    assert len(price_records) >= 5
    for rec in price_records:
        if rec["response"]["refused"]:
            continue
        evidences = {
            ev["n"]: ev["text"]
            for ev in sets_by_id[rec["evidence_set_id"]]["evidences"]
        }
        for point in rec["response"]["points"]:
            cited_texts = [evidences[n] for n in point["citations"]]
            for token in answer_figures(point["text"]):
                assert any(token in text for text in cited_texts), (
                    f"{rec['response_id']}: token {token!r} not found verbatim in cited "
                    f"evidence {point['citations']}"
                )


def test_no_computed_amounts(recorded: list[dict], sets_by_id: dict[str, dict]) -> None:
    # Calculator-detector: no price answer point contains computed/derived figures.
    for rec in _price_records(recorded, sets_by_id):
        for point in rec["response"]["points"]:
            text = point["text"]
            assert not COMPUTE_PATTERN.search(text), (
                f"{rec['response_id']}: possible computed amount in point: {text!r}"
            )
            # Belt and braces: every numeric token must still be traceable to cited evidence.
            evidences = {
                ev["n"]: ev["text"]
                for ev in sets_by_id[rec["evidence_set_id"]]["evidences"]
            }
            cited_texts = [evidences[n] for n in point["citations"]]
            for token in answer_figures(text):
                assert any(token in t for t in cited_texts), (
                    f"{rec['response_id']}: numeric token {token!r} absent from cited "
                    f"evidence (computed result?)"
                )


def test_prompt_instructs_verbatim_figures(prompt_text: str) -> None:
    # The no-calculation clause of the prompt instructs verbatim-only quoting.
    assert "禁止任何加减、折算、汇总、换算或推算出的结果" in prompt_text
