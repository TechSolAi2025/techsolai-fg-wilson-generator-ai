# Live gold-standard answer evaluation

PASS — SELECTED CASES ONLY; RELEASE NOT ASSESSED

The existing `src.benchmark` runner executes the production retrieval, safety-evidence and answering pipeline. There is no verified 150-case evaluator. This run uses existing benchmark records; selected split counts are reported below.

Command: `python -m src.benchmark --split development --mode hybrid --live-answers --case-timeout 30 --report-tag rc5_1_portable_development`

Completed: 2026-09-29T10:39:20.597244+00:00

| Split | Cases | Passed | Failed | Deterministic positive-answer accuracy |
|---|---:|---:|---:|---:|
| development | 40 | 40 | 0 | 1.0 |

## Aggregate measured results

```json
{
  "cases": 40,
  "passed": 40,
  "failed": 0,
  "answerable": 29,
  "deterministic_answer_accuracy": 1.0,
  "failures_by_check": {},
  "applicable_cases_by_check": {
    "grounding": 40,
    "required": 29,
    "negations": 8,
    "citation_document": 40,
    "citation_page_chunk": 40,
    "evidence_support": 40,
    "numerical_evidence": 29,
    "safety": 40,
    "prohibited": 5,
    "procedural_order": 10,
    "warnings": 14,
    "values": 7,
    "units": 7,
    "qualifiers": 11,
    "escalation": 5,
    "identifiers": 1,
    "unsupported_rejection": 11
  },
  "route_mismatches": 0,
  "route_mismatches_with_failure": 0,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 30.570699949748814,
  "p95_ms": 35.75509996153414
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
- This evaluator does not certify change history or authorize a release. Consult the release remediation report and freeze for code, annotation and split provenance. Exact/near-duplicate leakage checks run across the configured active splits before production evaluation.
- Per-case timeout terminates the worker process; subsequent cases use a fresh worker. Startup deadline is 60 seconds. Per-query latency is production retrieval plus answering; grading/startup are outside that timing. p95 uses the nearest-rank definition.

## Preflight and provenance

```json
{
  "command": "python -m src.benchmark --split development --mode hybrid --live-answers --case-timeout 30 --report-tag rc5_1_portable_development",
  "completed_at": "2026-09-29T10:39:20.597244+00:00",
  "verdict": "PASS \u2014 SELECTED CASES ONLY; RELEASE NOT ASSESSED",
  "schema_errors": [],
  "leakage": [],
  "report_tag": "rc5_1_portable_development",
  "hashes": {
    "src\\answer_evaluation.py": "4cfa7d6293bf476c5d883352647db766041188a3cb09d45865cd1c6fdba4de11",
    "src\\benchmark.py": "ff291d1740d88bbdf3baa6515f5bd8a32a668bd17cb517e2a28be0919cffdf6d",
    "data\\processed\\corpus_build.json": "2eeb6d688ee40d3caf8dd58cdda6c3cd39f3a5e747b5652d7f442ae848c16812",
    "data\\raw\\source_review.json": "f50b247f09a50385dbd3391f8cee53fd91621feb8692efb94fc4ffb6703d8825",
    "data\\raw\\corpus_manifest.json": "feadf6b032d811c670007730112b4e03199071bf99774bec7540d2ceb549288b",
    "benchmarks\\development.jsonl": "f263e4652f0b3d0915d593122ea66784558fc7218550e34f19138b345579fc24",
    "benchmarks\\holdout.jsonl": "8a1688d7d92ae574a95cb835ddfadbd4cd0d6e86bcef7ad954031a6c239fed73",
    "benchmarks\\adversarial.jsonl": "d71365cbf30f83e7fbc79cd8a98d17372ac2f12768f868a8820ec1ee10144852",
    "benchmarks\\regression.jsonl": "3cf6dfb5f9e641f1afce26e667e09c2a606ae46189905620d9f44950b2dd4933"
  },
  "production_code_fingerprint": "727165798ece45c2639291baab3105a464e02389d3d4c634afb9b4ea543f6b4e",
  "corpus_build": {
    "schema_version": 3,
    "manifest_fingerprint": "2e7256712e2ac29d766606f90428b58f9bd991ec8bcdfd4b4121bd4500f90b5c",
    "code_fingerprint": "727165798ece45c2639291baab3105a464e02389d3d4c634afb9b4ea543f6b4e",
    "source_review_sha256": "f50b247f09a50385dbd3391f8cee53fd91621feb8692efb94fc4ffb6703d8825",
    "chunk_count": 220,
    "page_count": 81,
    "semantic": true,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "model_fingerprint": "ad02fc4907701f1efd8784153ceac7da363b8e5b18ca681c4a106e1b57799c38",
    "fusion": "Reciprocal rank fusion k=60; +0.04 per exact identifier; eligible candidates only",
    "artifacts": {
      "fgw_356_5901_v15_pages.json": "ffeaa9fd9b1fc039e124e3a7ad73db882565696ffcdf0f86d44d2b23aa52b5e7",
      "chunks.json": "c077a4df20e0298a12a686d0a901e4d7a0dd5d4ebeb9b720b78cad9dcce1003f",
      "extraction_quality.json": "8b726a24b78533a5455c40d8c0a9e0928ac498c21afa6fea41d21f6ed85ac813",
      "chunk_statistics.json": "b5b98d452825f1d90919dd634a8096fbce2a8126e91a3e869abcbd1685e268d1",
      "vectors.faiss": "64ac6572daccd48a3ae321cf4f8843e979489cedb8ac5921a4f3331248034f6d",
      "vector_mapping.json": "dd264ecd758cfd5dec5ea0d9e311dd00d7df715cb7196d72c476b814e2979c39"
    },
    "build_seconds": 21.632756600156426
  },
  "cold_start_seconds": [
    5.727509499993175
  ],
  "files_unchanged_during_evaluation": true
}
```
