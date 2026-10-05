# RC3 methodology update

The earlier methodology below describes the historical 64-case audit. RC3 retains the original queries, quotations and chunk expectations, adds structured source annotations and eleven development cases, and moves the two exposed failures to regression. The other 22 original holdout records remain for history/leakage validation and are not counted as unseen release evidence.

Release evaluation uses development (35), regression (10), adversarial (8) and the replacement holdout (32): 85 cases total. The replacement was evaluated exactly once after the immutable RC3 freeze. Same-assistant source-only generation does not demonstrate independent construction; generalization is NOT SATISFIED. Pre-freeze annotation and category-coverage revisions are archived and documented in the provenance. No holdout results were consulted during implementation.

Structured required_assertions, prohibited_assertions, identifiers, paired values/units, qualifiers, negations, warnings and escalation come from approved source excerpts. Source document/pages/route are separately validated metadata. Prohibited alternatives are the first complete sentence of explicit, unconditional manufacturer prohibitions. The grader accounts for a not/never/cannot prefix so that quoting the manufacturer's prohibition is not mistaken for giving its unsafe affirmative alternative. This is bounded deterministic clause handling, not a semantic judge.

Use --report-tag to preserve prior result artifacts. The one-time release command is python scripts/rc3_release.py holdout; it requires a verified freeze and refuses a second attempt. Final reports are gold_standard_answer_results_rc3.json and RC3_REMEDIATION_REPORT.md. The failed RC3 cases are recorded in RC4_DEVELOPMENT_INTAKE.md without changing frozen code or expectations.

## Historical methodology

# Benchmark methodology

## Live answer evaluation audit, 2026-09-15

`python -m src.benchmark` already executed real retrieval, safety-evidence lookup and `src.answering.answer` before this audit. It was never retrieval-only. Original grading checked Top-1/Recall, positive expected-quote inclusion, negative refusal, selected citation identity fields, extractive answer fidelity, claim provenance and numerical inclusion. It did not validate record schemas or comprehensively grade units, conditions, negation, procedural order, prohibited assertions, warning completeness or citation applicability.

The existing runner now supports `--live-answers`, backed by `src/answer_evaluation.py`. A duplicate `benchmarks/evaluate_gold_standard_answers.py` was not created because the production pipeline runner already exists. Genuine mutation and integration tests are in `tests/test_gold_standard_answer_evaluator.py`. No 150-case dataset or earlier evaluator has been verified. There are 64 unchanged records: development 24, holdout 24, adversarial 8 and regression 8. Positive cases number 20, 20, 0 and 4 respectively.

## Commands

Run with local dependencies and bounded CPU threads:

```powershell
$env:PYTHONPATH='.deps;.'
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
$env:OPENBLAS_NUM_THREADS='2'
python -m src.benchmark --split all --mode hybrid --live-answers --case-timeout 30
```

Outputs are `exports/gold_standard_answer_results.json` and `docs/GOLD_STANDARD_ANSWER_EVALUATION.md`. Exit status 1 means the live gate or preflight failed; it need not indicate a process crash. `--split development` and `--split holdout` select one split explicitly. All four splits are schema-validated and checked for cross-split leakage before any case executes. The same `evaluate` function calls production retrieval and answering in both legacy and strict modes. A persistent spawned worker enforces per-case deadlines; startup has a separate 60-second deadline. No LLM judge is used.

Baseline reproduction used these real commands before evaluator changes:

```powershell
python -m pytest -q
python -m src.benchmark --split development --mode hybrid
python -m src.benchmark --split holdout --mode hybrid
python -m src.benchmark --split adversarial --mode hybrid
python -m src.benchmark --split regression --mode hybrid
python -m src.benchmark --split development --mode bm25
python -m src.benchmark --split development --mode semantic
```

All 97 original tests passed. Every RC2 case outcome and non-latency metric reproduced; `exports/live_evaluation_baseline_reproduction.json` preserves the comparison. Final compilation and testing use `python -m compileall -q src app tests scripts` and `python -m pytest -q`.

## Deterministic grading and schema

Optional `assertions` fields are technical string lists named `required`, `prohibited`, `identifiers`, `qualifiers`, `negations`, `order`, `warnings` and `escalation`. `quantities` is a list of objects containing exact string `value` and `unit`. Unsupported keys, units/number grammar, malformed types, missing/excluded evidence IDs, source hash/page errors and grader-instruction quotations fail validation. `metadata`, `rationale`, `topic` and `grader_instructions` are never answer requirements. Existing records and expected answers were not changed to add assertions.

Legacy `expected_quote` remains the explicit technical assertion. Relevant source paragraphs retain conditions and negation; numbered source procedures retain order; source warning metadata supplies warning obligations. Explicit and derived checks report applicability counts. The legacy records have no explicit prohibited assertion annotations: this is a coverage gap, not a successful prohibited-assertion test. No rubric claims full semantic completeness.

Every emitted answer, step and warning requires a claim supported by eligible cited evidence. Checks cover document/revision/hash/applicability, page/chunk identity, selected controller/model compatibility and value/unit associations in the particular cited claim's source. Inherited warning citations must reference their actual warning pages. These source-text checks do not establish independent field safety or every implied technical claim.

Normalization uses NFC, collapsed whitespace and a fixed map of typographic quotes/hyphens. String assertions ignore case; number/unit checks preserve exact values and unit case. No synonyms, stemming, fuzzy grading, unit conversion or negation removal occurs. Supported quantity grammar is a signed integer/decimal followed by the enumerated units in `QUANTITY`; unsupported explicit units fail schema validation.

All applicable substantive checks must pass. Route mismatch is reported separately and is diagnostic only when the final answer still passes content, grounding, citation and safety checks. Negative cases must emit a clean production refusal, not technical steps disguised by a refused status. Errors and timeouts count as failures. Median and nearest-rank p95 measure production retrieval, safety-evidence lookup and answering, excluding grading, model startup and UI rendering. Legacy benchmark p95 retains its original formula for reproducibility.

## Provenance and holdout separation

`exports/evaluation_freeze.json` is the original RC1 freeze. Its source/model and benchmark hashes remain relevant, but code/build hashes do not match RC2. Before evaluator edits, `exports/rc2_freeze.json` matched all frozen files and the current build. The evaluation-only edit to `src/benchmark.py` intentionally changes that file's RC2 hash; retrieval, answering and the runtime corpus fingerprint remain unchanged. New live results bind current evaluator, benchmark, source-review and build hashes. Historical freezes are preserved rather than rewritten.

The live run is an audit rerun of the already exposed RC2 holdout, not a new unseen validation set. Retrieval, answering and thresholds were not tuned using it. Generic grader mutation tests do not establish a release pass; the verdict depends on the completed production run. A final generic grader check for controller/model citation compatibility and unsupported explicit unit grammar was added and the entire test/live run repeated; it did not alter production answers or repair the two holdout refusals.

Benchmarks were originally curated from source sections by `scripts/curate_benchmarks.py`, without retrieval calls. Expected chunk IDs and quotations remain unchanged. Exact/near-duplicate question leakage is checked across each pair of splits with normalized SequenceMatcher >=0.85 or token Jaccard >=0.80. No training, fine-tuning, reranker or question-specific routes are used. Same-author, single-manual labels are not externally blind and lexical leakage detection does not prove semantic independence.

## Existing production retrieval and limits

BM25 uses Okapi. Semantic retrieval uses the local pretrained all-MiniLM-L6-v2 model, overlapping 160-word windows at 120-word stride, 384-dimensional normalized vectors and FAISS IndexFlatIP. Maximum per-window scores collapse to chunks. Dense windows can exceed the 256-subword limit; complete source evidence is retained for answers. RRF uses k=60, eligibility filters, exact-identifier contributions of 0.04 and a general section-title coverage contribution. Vocabulary typo correction uses cutoff 0.84. Safety context is retrieved separately from Top-k measurement.

The single approved manufacturer manual, small same-author benchmark, missing comprehensive assertion rubrics and lack of independent service-technician review limit generalization and commercial/pilot readiness. Numerical fault-code dictionaries, SPN/FMI diagnostics, controller internal service, wiring-level diagnosis, engine overhaul, component disassembly and unstated model-specific specifications remain outside V1.
