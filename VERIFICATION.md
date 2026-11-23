# VERIFICATION — S3-KB-020 kb_answer deliverable

All outputs below are real captured runs on the delivery machine (Windows 11,
win32), executed from a clean checkout copy at `D:\tmp\kb1946_verify` with a
dedicated virtualenv.

## 1. Environment

```
$ python --version
Python 3.13.14
$ python -m pip show jsonschema pytest | grep -E "^(Name|Version)"
Name: jsonschema
Version: 4.26.0
Name: pytest
Version: 9.2.0
```

Runtime: Python 3.13.14 (dedicated venv) on Windows (win32); dependencies:
jsonschema 4.26.0, pytest 9.2.0 (plus pluggy 1.7.0 shipped with pytest). No
other third-party dependencies; the code targets Python 3.11+.

## 2. Full test suite

```
$ python -m pytest -v
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.2.0, pluggy-1.7.0 -- D:\tmp\kb1946_venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\tmp\kb1946_verify
configfile: pytest.ini
testpaths: tests
collecting ... collected 30 items

tests/test_price_samples.py::test_price_sample_sets_exist PASSED         [  3%]
tests/test_price_samples.py::test_price_numbers_verbatim_in_cited_evidence PASSED [  6%]
tests/test_price_samples.py::test_no_computed_amounts PASSED             [ 10%]
tests/test_price_samples.py::test_prompt_instructs_verbatim_figures PASSED [ 13%]
tests/test_records.py::test_every_record_has_prompt_version_and_model_name PASSED [ 16%]
tests/test_records.py::test_recorder_round_trip PASSED                   [ 20%]
tests/test_records.py::test_record_digest_is_stable PASSED               [ 23%]
tests/test_records.py::test_digest_changes_with_response PASSED          [ 26%]
tests/test_records.py::test_record_requires_model_name PASSED            [ 30%]
tests/test_records.py::test_write_rejects_incomplete_record PASSED       [ 33%]
tests/test_renderer.py::test_render_normal_answer PASSED                 [ 36%]
tests/test_renderer.py::test_render_refusal PASSED                       [ 40%]
tests/test_renderer.py::test_refusal_text_matches_prompt PASSED          [ 43%]
tests/test_renderer.py::test_render_rejects_out_of_range_citation PASSED [ 46%]
tests/test_renderer.py::test_render_references_sorted PASSED             [ 50%]
tests/test_schema.py::test_there_are_exactly_20_records PASSED           [ 53%]
tests/test_schema.py::test_all_20_records_valid PASSED                   [ 56%]
tests/test_schema.py::test_every_point_has_citation PASSED               [ 60%]
tests/test_schema.py::test_refused_records_have_empty_points PASSED      [ 63%]
tests/test_schema.py::test_schema_rejects_point_without_citation PASSED  [ 66%]
tests/test_schema.py::test_schema_rejects_refused_with_points PASSED     [ 70%]
tests/test_snapshot.py::test_prompt_snapshot_unchanged PASSED            [ 73%]
tests/test_snapshot.py::test_snapshot_hash_matches_content PASSED        [ 76%]
tests/test_snapshot.py::test_rule_present_in_prompt[mandatory_citation] PASSED [ 80%]
tests/test_snapshot.py::test_rule_present_in_prompt[refusal_on_insufficient_evidence] PASSED [ 83%]
tests/test_snapshot.py::test_rule_present_in_prompt[no_amount_calculation] PASSED [ 86%]
tests/test_snapshot.py::test_rule_mandatory_citation PASSED              [ 90%]
tests/test_snapshot.py::test_rule_refusal_on_insufficient_evidence PASSED [ 93%]
tests/test_snapshot.py::test_rule_no_amount_calculation PASSED           [ 96%]
tests/test_snapshot.py::test_all_three_rules_numbered_as_clauses PASSED  [100%]

============================= 30 passed in 1.35s ==============================
```

## 3. Reverse check: deleting a rule sentence turns the tests red

The refusal-rule operative sentence was temporarily replaced with
`[deleted]` inside `prompts/kb_answer/v1.md`, then the snapshot module was
re-run, then the file was restored:

```
$ python -m pytest tests/test_snapshot.py -q      (with the sentence deleted)
4 failed, 5 passed in 0.31s
FAILED tests/test_snapshot.py::test_prompt_snapshot_unchanged
FAILED tests/test_snapshot.py::test_rule_present_in_prompt[refusal_on_insufficient_evidence]
FAILED tests/test_snapshot.py::test_rule_refusal_on_insufficient_evidence
FAILED tests/test_snapshot.py::test_all_three_rules_numbered_as_clauses

$ cp /tmp/v1.bak.md prompts/kb_answer/v1.md       (restore)
$ python -m pytest tests/test_snapshot.py -q
9 passed in 0.06s
```

This proves the snapshot pins the full v1.md content and each of the three
rules is asserted by its own independent test (AC2).

## 4. Smoke run (schema / renderer / recorder)

```
$ python - <<'EOF'
import json
from kb_answer.schema import is_valid_answer
from kb_answer.renderer import render_markdown
from kb_answer.recorder import make_record, write_records, load_records
import tempfile, pathlib

sets = json.load(open('fixtures/evidence_sets.json', encoding='utf-8'))['sets']
recs = json.load(open('fixtures/recorded_responses.json', encoding='utf-8'))['records']

ev01 = next(s for s in sets if s['evidence_set_id'] == 'EV-P01')
r01 = next(r for r in recs if r['response_id'] == 'resp-p01')
print('[smoke 1] schema check resp-p01:', is_valid_answer(r01['response']))
print('[smoke 2] rendered markdown (EV-P01):')
print(render_markdown(r01['response'], ev01['evidences']))
evr01 = next(s for s in sets if s['evidence_set_id'] == 'EV-R01')
rr01 = next(r for r in recs if r['response_id'] == 'resp-r01')
print('[smoke 3] rendered markdown (EV-R01, refused):', repr(render_markdown(rr01['response'], evr01['evidences'])))
rec = make_record(r01['response'], r01['model_name'], r01['model_version'], recorded_at=r01['recorded_at'])
tmp = pathlib.Path(tempfile.mkdtemp()) / 'demo.jsonl'
write_records([rec], tmp)
back = load_records(tmp)
print('[smoke 4] recorder round-trip equal:', back == [rec])
print('[smoke 4] record keys:', sorted(rec.keys()))
print('[smoke 4] response_digest:', rec['response_digest'][:16] + '...')
EOF
[smoke 1] schema check resp-p01: True
[smoke 2] rendered markdown (EV-P01):
- 大型会议室工作日的时租为 ￥120/小时，非工作日为 ￥90/小时[1]。

## 引用来源
[1] 《会议室与场地使用价目表》 v3.0 > 会议室 > 时租价格
[smoke 3] rendered markdown (EV-R01, refused): '知识库中没有找到'
[smoke 4] recorder round-trip equal: True
[smoke 4] record keys: ['model_name', 'model_version', 'prompt_id', 'prompt_version', 'recorded_at', 'response', 'response_digest']
[smoke 4] response_digest: a66b26ea5d9d9f20...
```

## 5. Acceptance-criteria mapping

| AC (order text) | Proof |
|---|---|
| 1. 20 recorded responses pass the Schema check, every point has >= 1 citation | `test_all_20_records_valid`, `test_every_point_has_citation` (section 2) |
| 2. Snapshot test covers mandatory citation / refusal on insufficient evidence / no amount calculation | `test_prompt_snapshot_unchanged` + three per-rule tests; reverse check in section 3 |
| 3. Price-sample figures verbatim from evidence, no computed results | `test_price_numbers_verbatim_in_cited_evidence`, `test_no_computed_amounts` (section 2) |
| 4. Prompt version and model name recorded per answer | `test_every_record_has_prompt_version_and_model_name`, `test_recorder_round_trip` (section 2) |
