# kb_answer — Citation-Grounded Answer Generation (Prompt Template + Output Schema)

Deliverable for order S3-KB-020 (member-space platform, knowledge-base module).
It contains the frozen prompt template `prompts/kb_answer/v1.md`, the JSON Schema
for model output, a Markdown renderer with `[n]` citation marks, a file-backed
S5-GW interface stub that records the prompt version and model identity with
every answer, and a pytest suite covering all four acceptance criteria over
20 synthetic evidence sets with recorded responses.

## Layout

```
prompts/kb_answer/v1.md        frozen prompt template v1 (three hard rules)
prompts/kb_answer/CHANGELOG.md prompt version change record
kb_answer/schema.py            JSON Schema (Draft 2020-12) + validate_answer()
kb_answer/renderer.py          render {points, refused} to Markdown with [n] marks
kb_answer/recorder.py          file-backed S5-GW interface stub (JSONL records)
fixtures/evidence_sets.json    20 synthetic evidence sets (post-visibility-filter)
fixtures/recorded_responses.json  20 recorded gateway responses (synthetic)
tests/                         pytest suite (AC1-AC4 + negative/reverse checks)
pytest.ini                     pythonpath=. / testpaths=tests
```

## Run

Requirements: Python 3.11+, `jsonschema` (any recent 4.x), `pytest`.

```bash
python -m pip install jsonschema pytest
python -m pytest -q
```

One command runs the whole suite (30 tests). See `VERIFICATION.md` for real
command outputs captured on the delivery machine.

## Component notes

### Prompt template (`prompts/kb_answer/v1.md`)

Three hard rules, stated as numbered clauses:

1. **Mandatory citation** — every point must carry at least one `[n]` mark,
   n drawn from the evidence-block numbering.
2. **Refusal on insufficient evidence** — if the evidence does not answer the
   question, output `{"points": [], "refused": true}`; the rendered text is
   「知识库中没有找到」.
3. **No amount calculation** — prices/fees are quoted verbatim from evidence
   text; no addition, conversion, aggregation or derived figures.

Evidence blocks are concatenated in `[n]` order, each carrying document title,
version and heading_path. v1 is frozen (hash-pinned by the snapshot test);
any wording change must create v2 and a CHANGELOG entry.

### Output Schema (`kb_answer/schema.py`)

`{points: [{text, citations: [n]}], refused}` — Draft 2020-12, `minItems: 1`
on citations (mechanically enforces AC1's per-point rule), plus an `if/then`
branch requiring empty `points` when `refused=true`. `validate_answer(data)`
raises on the first violation; `is_valid_answer(data)` returns a bool.

### Renderer (`kb_answer/renderer.py`)

`render_markdown(answer, evidences)` — one bullet per point (the point text
already carries its `[n]` marks), a `## 引用来源` section listing each cited
evidence as `[n] 《title》 version > heading_path`, and the fixed refusal line
for `refused=true`. Citation numbers outside the evidence blocks raise
`ValueError`.

### S5-GW interface stub (`kb_answer/recorder.py`)

The real model gateway (S5-GW) is out of scope for this order. Per the unified
technical agreement this file-backed stub is the agreed interface: every answer
is recorded as one JSONL line

```
{prompt_id, prompt_version, model_name, model_version, response_digest, recorded_at, response}
```

**Connection points for the real gateway** (no prompt or schema change needed):
- gateway persists one line per call via `make_record()` + `write_records()`;
  `load_records()` reads them back in write order.
- `response_digest()` is a stable sha256 over the canonical JSON of the answer.
- `PROMPT_ID` / `PROMPT_VERSION` in `kb_answer/__init__.py` must match the
  template file name and its `prompt_version` header; the AC4 tests pin them
  to the fixture records.

### AI review queue (L0 registration)

Answers are registered at level L0 (internal staff reference only, never sent
to members directly). The registration payload is the record produced by the
recorder; no further integration is part of this order.

## Data

All 20 evidence sets and recorded responses are synthetic (document titles,
companies, figures are fictional). Evidence sets carry `visible_scope` to
record the result of the per-user visibility filtering that the (out-of-scope)
retrieval side applies upstream. Sets tagged `pricing` are the price samples
exercised by the verbatim-figure tests (AC3).
