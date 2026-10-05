# Live gold-standard answer evaluation

CONDITIONAL PASS — CONTROLLED DEMO ONLY

The existing `src.benchmark` runner executes the production retrieval, safety-evidence and answering pipeline. There is no verified 150-case evaluator. This run uses existing benchmark records; selected split counts are reported below.

Command: `python -m src.benchmark --split adversarial --mode hybrid --live-answers --case-timeout 30 --report-tag rc3_adversarial`

Completed: 2026-09-15T11:36:55.729758+00:00

| Split | Cases | Passed | Failed | Deterministic positive-answer accuracy |
|---|---:|---:|---:|---:|
| adversarial | 8 | 8 | 0 | None |

## Aggregate measured results

```json
{
  "cases": 8,
  "passed": 8,
  "failed": 0,
  "answerable": 0,
  "deterministic_answer_accuracy": null,
  "failures_by_check": {},
  "applicable_cases_by_check": {
    "grounding": 8,
    "unsupported_rejection": 8,
    "citation_document": 8,
    "citation_page_chunk": 8,
    "evidence_support": 8,
    "safety": 8
  },
  "route_mismatches": 0,
  "route_mismatches_with_failure": 0,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 0.01575000351294875,
  "p95_ms": 0.5581000004895031
}
```

## Failures


## Interpretation and limits

- A route mismatch alone is diagnostic; it fails only alongside substantive checks. All positive checks must pass for deterministic answer accuracy. Negative refusals are counted separately.
- Legacy expected quotations remain unchanged. Grading also retains relevant source paragraph conditions/negation, numbered procedure order, and source warning metadata. No rationale, topic, metadata or grader instruction is treated as a technical assertion.
- Optional typed assertion fields support explicit prohibited statements, identifiers, value/unit pairs, qualifiers, negation, sequence, warnings and escalation. Current legacy cases do not provide a complete independent assertion rubric. Zero failures in a category with zero applicable cases means unmeasured, not verified.
- Normalization is NFC, whitespace collapse and a fixed map of typographic quotes/hyphens. Technical substring checks ignore letter case; numeric/unit pairs preserve unit case and exact values. No conversions, fuzzy grading, stemming, synonyms or LLM judge. Units and numbers are checked within the cited claim evidence.
- Evidence support covers every emitted answer, step and warning, plus document/revision/hash/applicability and page/chunk identity. It cannot establish every implicit semantic implication or detect every harmful statement in the approved manual.
- Safety results are bounded source-warning/condition/negation/escalation and negative-refusal checks. Independent service-technician review remains pending.
- No retrieval, answer-generation, benchmark labels or existing retrieval thresholds were changed. Holdout is used for audit only, not tuning. Exact/near-duplicate leakage checks run across all splits before production evaluation.
- Per-case timeout terminates the worker process; subsequent cases use a fresh worker. Startup deadline is 60 seconds. Per-query latency is production retrieval plus answering; grading/startup are outside that timing. p95 uses the nearest-rank definition.

## Preflight and provenance

```json
{
  "command": "python -m src.benchmark --split adversarial --mode hybrid --live-answers --case-timeout 30 --report-tag rc3_adversarial",
  "completed_at": "2026-09-15T11:36:55.729758+00:00",
  "verdict": "CONDITIONAL PASS \u2014 CONTROLLED DEMO ONLY",
  "schema_errors": [],
  "leakage": [],
  "report_tag": "rc3_adversarial",
  "hashes": {
    "src\\answer_evaluation.py": "fb55d3acb25f03c0e4b116858f1e8e1fbdb2495c01adb36d8e9637a171763d92",
    "src\\benchmark.py": "ff291d1740d88bbdf3baa6515f5bd8a32a668bd17cb517e2a28be0919cffdf6d",
    "data\\processed\\corpus_build.json": "ae69e453752fa3d27382d071b7553dd1964d7e976c49648b17fc5ffabeca9a32",
    "data\\raw\\source_review.json": "550e2f2176435ed84f7697982d31c78901c0c8feb26d262120e6187693211211",
    "data\\raw\\corpus_manifest.json": "feadf6b032d811c670007730112b4e03199071bf99774bec7540d2ceb549288b",
    "benchmarks\\development.jsonl": "914bd7adf1632091499ea71f052d6fca8ea460caf545d81335acd550861430e1",
    "benchmarks\\holdout.jsonl": "8a1688d7d92ae574a95cb835ddfadbd4cd0d6e86bcef7ad954031a6c239fed73",
    "benchmarks\\adversarial.jsonl": "d71365cbf30f83e7fbc79cd8a98d17372ac2f12768f868a8820ec1ee10144852",
    "benchmarks\\regression.jsonl": "452eed87418772f76da05252a8d6a870aac783a10d6dffc134867e8d6deb5c2a"
  },
  "production_code_fingerprint": "ef0a20f811c9014a7da1d84a36e661d63bbbb337f14c31331f1d0fd271758168",
  "corpus_build": {
    "schema_version": 3,
    "manifest_fingerprint": "2e7256712e2ac29d766606f90428b58f9bd991ec8bcdfd4b4121bd4500f90b5c",
    "code_fingerprint": "ef0a20f811c9014a7da1d84a36e661d63bbbb337f14c31331f1d0fd271758168",
    "source_review_sha256": "550e2f2176435ed84f7697982d31c78901c0c8feb26d262120e6187693211211",
    "chunk_count": 215,
    "page_count": 81,
    "semantic": true,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "model_fingerprint": "82df1d38da8f87d5ce84fcbc474c92b0c058b9cec863e9b75857648900397c4c",
    "fusion": "Reciprocal rank fusion k=60; +0.04 per exact identifier; eligible candidates only",
    "artifacts": {
      "fgw_356_5901_v15_pages.json": "ffeaa9fd9b1fc039e124e3a7ad73db882565696ffcdf0f86d44d2b23aa52b5e7",
      "chunks.json": "d5664b0de29e761665422c544f37960b784a77234ed1ed590ea8d0bca8de2ef8",
      "extraction_quality.json": "8b726a24b78533a5455c40d8c0a9e0928ac498c21afa6fea41d21f6ed85ac813",
      "chunk_statistics.json": "0f48e814a5c30222ce2c836af3b387e7fdc9c2c16188dd20978801e5903003d9",
      "vectors.faiss": "ae20ca0b733b60391c97826514e4b005ecfe6410c50151f0c3b83d2e6dd487f5",
      "vector_mapping.json": "8168cb616b677ab2c09de80e62939ed92a62cb13e57c2f0983b33a149d841d5a"
    },
    "build_seconds": 32.15612320002401
  },
  "cold_start_seconds": [
    4.390842600027099
  ],
  "files_unchanged_during_evaluation": true
}
```
