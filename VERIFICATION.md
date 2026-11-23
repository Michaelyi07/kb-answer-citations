# VERIFICATION — S3-KB-020 kb_answer deliverable (rework round 1)

All outputs below are real captured runs on the delivery machine (Windows 11,
win32), executed from a clean checkout copy at `D:\tmp\kb1946r_verify` with a
dedicated virtualenv built from the repo's own `requirements.txt`.

## 1. Environment

```
$ python --version
Python 3.13.14
$ python -m pip install -r requirements.txt      (into a fresh venv; installs jsonschema==4.26.0, pytest==9.2.0)
$ python -m pip show jsonschema pytest | grep -E "^(Name|Version)"
Name: jsonschema
Version: 4.26.0
Name: pytest
Version: 9.2.0
```

Runtime: Python 3.13.14 (dedicated venv) on Windows (win32); dependencies
declared in requirements.txt: jsonschema 4.26.0, pytest 9.2.0 (plus pluggy
1.7.0 shipped with pytest).

## 2. Clean-environment collection and full suite (49 tests, one command)

```
$ python -m pytest -q
.................................................                        [100%]
49 passed in 1.79s

$ python -m pytest --collect-only -q
49 tests collected in 0.35s
```

The repo now declares dependencies (requirements.txt) and ships tests/__init__.py,
so `from tests.conftest import ROOT` imports cleanly and pytest collects all 49
tests in a fresh environment (the sandbox issue reported in the first round is
resolved — verified above in a clean venv built only from requirements.txt).

## 3. Full verbose run

```
$ python -m pytest -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0
cachedir: .pytest_cache
rootdir: D:\tmp\kb1946r_verify
configfile: pytest.ini
testpaths: tests
collecting ... collected 49 items

tests/test_evidence_blocks.py::test_blocks_in_n_order_with_header_and_text PASSED [  2%]
tests/test_evidence_blocks.py::test_blocks_sorted_by_n_even_if_input_unordered PASSED [  4%]
tests/test_evidence_blocks.py::test_block_numbers_are_contiguous PASSED  [  6%]
tests/test_evidence_blocks.py::test_empty_evidence_gives_empty_string PASSED [  8%]
tests/test_evidence_blocks.py::test_filter_visible_drops_out_of_scope_evidence PASSED [ 10%]
tests/test_gateway.py::test_replay_stub_returns_recorded_response PASSED [ 12%]
tests/test_gateway.py::test_stub_rejects_unknown_evidence_set PASSED     [ 14%]
tests/test_gateway.py::test_assemble_prompt_includes_evidence_blocks PASSED [ 16%]
tests/test_gateway.py::test_pipeline_all_20_answers_recorded_and_registered PASSED [ 18%]
tests/test_gateway.py::test_pipeline_records_round_trip_via_recorder PASSED [ 20%]
tests/test_gateway.py::test_evidence_blocks_concatenated_in_prompt PASSED [ 22%]
tests/test_price_samples.py::test_price_sample_sets_exist PASSED         [ 24%]
tests/test_price_samples.py::test_price_numbers_verbatim_in_cited_evidence PASSED [ 26%]
tests/test_price_samples.py::test_no_computed_amounts PASSED             [ 28%]
tests/test_price_samples.py::test_boundary_match_rejects_computed_substring PASSED [ 30%]
tests/test_price_samples.py::test_computed_amount_negative_case_is_caught PASSED [ 32%]
tests/test_price_samples.py::test_prompt_instructs_verbatim_figures PASSED [ 34%]
tests/test_records.py::test_every_record_has_prompt_version_and_model_name PASSED [ 36%]
tests/test_records.py::test_recorder_round_trip PASSED                   [ 38%]
tests/test_records.py::test_record_digest_is_stable PASSED               [ 40%]
tests/test_records.py::test_digest_changes_with_response PASSED          [ 42%]
tests/test_records.py::test_record_requires_model_name PASSED            [ 44%]
tests/test_records.py::test_write_rejects_incomplete_record PASSED       [ 46%]
tests/test_renderer.py::test_render_normal_answer PASSED                 [ 48%]
tests/test_renderer.py::test_render_refusal PASSED                       [ 51%]
tests/test_renderer.py::test_refusal_text_matches_prompt PASSED          [ 53%]
tests/test_renderer.py::test_render_rejects_out_of_range_citation PASSED [ 55%]
tests/test_renderer.py::test_render_rejects_marks_missing_from_citations PASSED [ 57%]
tests/test_renderer.py::test_render_rejects_citation_missing_from_marks PASSED [ 59%]
tests/test_renderer.py::test_all_20_recorded_answers_render_with_correct_marks PASSED [ 61%]
tests/test_renderer.py::test_render_references_sorted PASSED             [ 63%]
tests/test_schema.py::test_there_are_exactly_20_records PASSED           [ 65%]
tests/test_schema.py::test_all_20_records_valid PASSED                   [ 67%]
tests/test_schema.py::test_every_point_has_citation PASSED               [ 69%]
tests/test_schema.py::test_refused_records_have_empty_points PASSED      [ 71%]
tests/test_schema.py::test_schema_rejects_point_without_citation PASSED  [ 73%]
tests/test_schema.py::test_schema_rejects_refused_with_points PASSED     [ 75%]
tests/test_snapshot.py::test_prompt_snapshot_unchanged PASSED            [ 77%]
tests/test_snapshot.py::test_snapshot_hash_matches_content PASSED        [ 79%]
tests/test_snapshot.py::test_rule_present_in_prompt[mandatory_citation] PASSED [ 81%]
tests/test_snapshot.py::test_rule_present_in_prompt[refusal_on_insufficient_evidence] PASSED [ 83%]
tests/test_snapshot.py::test_rule_present_in_prompt[no_amount_calculation] PASSED [ 85%]
tests/test_snapshot.py::test_rule_mandatory_citation PASSED              [ 87%]
tests/test_snapshot.py::test_rule_refusal_on_insufficient_evidence PASSED [ 89%]
tests/test_snapshot.py::test_rule_no_amount_calculation PASSED           [ 91%]
tests/test_snapshot.py::test_all_three_rules_numbered_as_clauses PASSED  [ 93%]
tests/test_visibility.py::test_visible_case_passes_and_hides_cross_tenant_block PASSED [ 95%]
tests/test_visibility.py::test_leak_case_citing_hidden_evidence_is_refused PASSED [ 97%]
tests/test_visibility.py::test_leaked_answer_never_reaches_the_queue_unrefused PASSED [100%]

============================= 49 passed in 1.52s ==============================
```

## 4. Reverse check: deleting a rule sentence turns the tests red

With the refusal-rule operative sentence temporarily replaced by `[deleted]`
inside `prompts/kb_answer/v1.md`:

```
$ python -m pytest tests/test_snapshot.py -q
4 failed, 5 passed in 0.31s
FAILED tests/test_snapshot.py::test_prompt_snapshot_unchanged
FAILED tests/test_snapshot.py::test_rule_present_in_prompt[refusal_on_insufficient_evidence]
FAILED tests/test_snapshot.py::test_rule_refusal_on_insufficient_evidence
FAILED tests/test_snapshot.py::test_all_three_rules_numbered_as_clauses

$ (restore v1.md)
$ python -m pytest tests/test_snapshot.py -q
9 passed in 0.06s
```

## 5. Reverse check: removing the strict mark/citation consistency turns the tests red

With the `_check_marks_match_citations` call deleted from `renderer.render_markdown`:

```
$ python -m pytest tests/test_renderer.py -q
2 failed, 6 passed in 0.33s
FAILED tests/test_renderer.py::test_render_rejects_marks_missing_from_citations
FAILED tests/test_renderer.py::test_render_rejects_citation_missing_from_marks

$ (restore renderer.py)
$ python -m pytest tests/test_renderer.py -q
8 passed in 0.07s
```

## 6. Acceptance-criteria mapping (the 4 ACs + the rework items)

| Item | Proof |
|---|---|
| AC1 20 responses pass schema, >= 1 citation per point | `test_all_20_records_valid`, `test_every_point_has_citation` |
| AC2 snapshot covers the three rules | `test_prompt_snapshot_unchanged` + per-rule tests (section 4) |
| AC3 price figures verbatim at full-number boundaries, no computed results | `test_price_numbers_verbatim_in_cited_evidence`, `test_boundary_match_rejects_computed_substring` (12 vs 120 negative case), `test_computed_amount_negative_case_is_caught` (fabricated 210 = 120+90 caught end-to-end) |
| AC4 prompt version + model name recorded per answer | `test_every_record_has_prompt_version_and_model_name`, `test_recorder_round_trip`, and the pipeline: `test_pipeline_all_20_answers_recorded_and_registered` |
| rework 1 (S5-GW call path) | `kb_answer/gateway.py` pipeline + `test_pipeline_all_20_answers_recorded_and_registered` (assemble -> stub call -> schema validation -> record -> L0 registration), `test_assemble_prompt_includes_evidence_blocks`; real-gateway swap points in README |
| rework 2 (evidence-block assembly) | `evidence.build_evidence_blocks` + `test_blocks_in_n_order_with_header_and_text`, `test_block_numbers_are_contiguous`, `test_blocks_sorted_by_n_even_if_input_unordered` |
| rework 3 (L0 queue registration) | `review_queue.L0ReviewQueue` + 20/20 registrations asserted `level=L0`, `internal_only`, `dispatch=internal_review`, `audience=staff_only`; registration-only design (no outward-send path) |
| rework 4 (renderer marks) | strict consistency in `render_markdown` + `test_render_rejects_marks_missing_from_citations`, `test_render_rejects_citation_missing_from_marks`, reverse check in section 5 |
| rework 5 (all-20 citation checks) | `test_all_20_recorded_answers_render_with_correct_marks`: every citation within evidence range, every text mark equal to citations, 24 points rendered |
| rework 6 (visibility filter / no cross-tenant leak) | `evidence.filter_visible_evidences` + gateway post-check; `test_visible_case_passes_and_hides_cross_tenant_block`, `test_leak_case_citing_hidden_evidence_is_refused`, `test_leaked_answer_never_reaches_the_queue_unrefused`; fixtures/visibility_cases.json |
| rework 7 (declared deps, clean-env collection) | requirements.txt (jsonschema==4.26.0, pytest==9.2.0), tests/__init__.py; clean-venv run in section 2: 49 collected, 49 passed |
| rework 8 (boundary-verbatim figures) | `token_in_text_verbatim` full-number-boundary matching + negative cases in `test_boundary_match_rejects_computed_substring` and `test_computed_amount_negative_case_is_caught` |
