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
                               (strict mark/citation consistency, mismatch raises)
kb_answer/evidence.py          evidence-block assembly ([n] order, title/version/
                               heading_path) + per-user visibility filter
kb_answer/gateway.py           S5-GW call path: assemble prompt -> stub call ->
                               schema validation -> record -> L0 registration
kb_answer/review_queue.py      L0 AI-review-queue registration stub (internal only)
kb_answer/recorder.py          file-backed S5-GW interface stub (JSONL records)
fixtures/evidence_sets.json    20 synthetic evidence sets (post-visibility-filter)
fixtures/recorded_responses.json  20 recorded gateway responses (synthetic)
fixtures/visibility_cases.json visibility-gate cases (public + cross-tenant blocks)
tests/                         pytest suite (AC1-AC4 + negative/reverse checks)
pytest.ini                     pythonpath=. / testpaths=tests
requirements.txt               jsonschema==4.26.0, pytest==9.2.0
```

## Run

Requirements: Python 3.11+, `jsonschema` (any recent 4.x), `pytest`.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

One command runs the whole suite (49 tests) and works in a clean environment:
requirements.txt declares the exact dependencies, and the tests/ package is
importable from the repo root. See `VERIFICATION.md` for real captured outputs.

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

### S5-GW call path (`kb_answer/gateway.py`)

`generate_answer(question, evidence_set, gateway=..., queue=..., requester_scope=...)`
is the full call path mandated by the order:

1. **Visibility gate** — `evidence.filter_visible_evidences` drops any evidence
   outside the requester's visible scope before prompt assembly (cross-tenant
   blocks never enter the prompt).
2. **Prompt assembly** — `assemble_prompt` concatenates the evidence blocks in
   [n] order (each `[n] 《doc_title》 version > heading_path` plus the verbatim
   text, via `evidence.build_evidence_blocks`) under the frozen v1 template.
3. **Gateway call** — `S5GatewayStub.call(prompt)` replays the recorded response
   for the evidence set through the same signature a real gateway exposes
   (prompt in, model output + model identity out).
4. **Schema validation** — the response is validated against the Draft 2020-12
   schema (`schema.validate_answer`).
5. **Visibility post-check** — an answer citing evidence that was filtered out
   of the prompt is rejected (refused); other members' data can never leak.
6. **Record + L0 registration** — `recorder.make_record` builds the record
   (prompt_id=kb_answer/v1, prompt_version, model_name, model_version,
   response_digest, recorded_at) and `review_queue.L0ReviewQueue.register`
   registers the answer at level L0 with `internal_only: true`.

**Real-gateway swap points**: implement `call(prompt, *, evidence_set_id)`
against the real S5-GW endpoint and keep the return shape
`{response, model_name, model_version, recorded_at}` — prompt, schema, records
and queue need no change. `recorder.py` remains the file-backed JSONL interface
for the records themselves.

### AI review queue (L0 registration, `kb_answer/review_queue.py`)

`L0ReviewQueue` appends one registration payload per answer to a JSONL file:

```
{level: "L0", internal_only: true, audience: "staff_only", dispatch: "internal_review", question, evidence_set_id, item: <record>}
```

The stub is registration-only by design — there is no outward-send path. Tests
assert every answer is registered at L0 with internal-only dispatch (20/20
through the pipeline), and that a leaking response is registered as refused,
never in raw form. The real S5 review queue plugs in by consuming these
payloads.

## Data

All evidence sets, recorded responses and visibility cases are synthetic
(document titles, companies, figures are fictional). Evidence sets carry
`visible_scope` (the post-filter result of the retrieval side); visibility-case
evidence additionally carries per-evidence `visible_scope` to demonstrate the
cross-tenant filtering boundary. Sets tagged `pricing` are the price samples
exercised by the verbatim-figure tests (AC3, full-number-boundary matching).
