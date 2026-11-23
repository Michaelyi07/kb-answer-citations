"""AC3 (rework minor 8): price figures verbatim at full-number boundaries,
zero computed results -- with a negative case proving computed figures fail."""

from __future__ import annotations

import re

NUM_TOKEN = re.compile(r"\d+(?:\.\d+)?")
# [n] citation marks are not answer figures; strip them before token extraction.
CITE_MARK = re.compile(r"\[\d+\]")
# Calculator-detector: wording that indicates arithmetic performed on figures.
COMPUTE_PATTERN = re.compile(
    r"(合计|总计|总共|共计|折算|换算|折合|平均|相加|减去|乘以|除以|汇总|推算|估算|折后|优惠后)"
)


def answer_figures(text: str) -> list[str]:
    """Numeric tokens of an answer point, excluding [n] citation marks."""
    return NUM_TOKEN.findall(CITE_MARK.sub("", text))


def token_in_text_verbatim(token: str, text: str) -> bool:
    """Full-number-boundary match: a computed figure like 12 must NOT match an
    evidence token like 120 (plain substring would)."""
    return re.search(rf"(?<![\d.]){re.escape(token)}(?![\d.])", text) is not None


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
    # Every numeric token in a price answer point must appear verbatim (at full
    # number boundaries) in the original text of one of the cited evidence blocks.
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
                assert any(token_in_text_verbatim(token, text) for text in cited_texts), (
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
            evidences = {
                ev["n"]: ev["text"]
                for ev in sets_by_id[rec["evidence_set_id"]]["evidences"]
            }
            cited_texts = [evidences[n] for n in point["citations"]]
            for token in answer_figures(text):
                assert any(token_in_text_verbatim(token, t) for t in cited_texts), (
                    f"{rec['response_id']}: numeric token {token!r} absent from cited "
                    f"evidence (computed result?)"
                )


def test_boundary_match_rejects_computed_substring() -> None:
    # Negative case (rework minor 8): 12 (computed) must not match 120 (source).
    assert token_in_text_verbatim("120", "工作日时租为 ￥120/小时")
    assert token_in_text_verbatim("90", "非工作日为 ￥90/小时")
    assert not token_in_text_verbatim("12", "工作日时租为 ￥120/小时"), (
        "computed 12 would pass a plain-substring check but must fail boundary match"
    )
    assert not token_in_text_verbatim("21", "工作日时租为 ￥120/小时")
    # decimals: 0.2 must not be satisfied by neighbouring-number fragments
    assert token_in_text_verbatim("0.2", "A4 黑白打印 0.2 元/页")
    assert not token_in_text_verbatim("0.25", "A4 黑白打印 0.2 元/页")


def test_computed_amount_negative_case_is_caught(sets_by_id: dict[str, dict]) -> None:
    # End-to-end negative case: a fabricated answer with a computed total (210
    # = 120 + 90, absent from the source) against the real EV-P01 evidence must
    # fail the check. (12 would be a legal figure here: the source says 12 人以上.)
    ev01 = sets_by_id["EV-P01"]["evidences"]
    cited_texts = [ev["text"] for ev in ev01 if ev["n"] == 1]
    fabricated_point = "租一天合计 210 元[1]"
    figures = answer_figures(fabricated_point)
    assert "210" in figures
    assert not any(token_in_text_verbatim("210", t) for t in cited_texts), (
        "the computed figure must be caught by the boundary-matched check"
    )
    # and the detector wording rule also fires on 合计
    assert COMPUTE_PATTERN.search(fabricated_point)


def test_prompt_instructs_verbatim_figures(prompt_text: str) -> None:
    # The no-calculation clause of the prompt instructs verbatim-only quoting.
    assert "禁止任何加减、折算、汇总、换算或推算出的结果" in prompt_text
