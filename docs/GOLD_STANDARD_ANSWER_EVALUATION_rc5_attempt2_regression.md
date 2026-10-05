# Live gold-standard answer evaluation

PASS — SELECTED CASES ONLY; RELEASE NOT ASSESSED

The existing `src.benchmark` runner executes the production retrieval, safety-evidence and answering pipeline. There is no verified 150-case evaluator. This run uses existing benchmark records; selected split counts are reported below.

Command: `python -m src.benchmark --split regression --mode hybrid --live-answers --case-timeout 30 --report-tag rc5_attempt2_regression`

Completed: 2026-09-29T06:26:24.554294+00:00

| Split | Cases | Passed | Failed | Deterministic positive-answer accuracy |
|---|---:|---:|---:|---:|
| regression | 17 | 17 | 0 | 1.0 |

## Aggregate measured results

```json
{
  "cases": 17,
  "passed": 17,
  "failed": 0,
  "answerable": 13,
  "deterministic_answer_accuracy": 1.0,
  "failures_by_check": {},
  "applicable_cases_by_check": {
    "grounding": 17,
    "unsupported_rejection": 4,
    "citation_document": 17,
    "citation_page_chunk": 17,
    "evidence_support": 17,
    "safety": 17,
    "required": 13,
    "escalation": 6,
    "warnings": 7,
    "numerical_evidence": 13,
    "prohibited": 2,
    "negations": 6,
    "qualifiers": 6,
    "values": 2,
    "units": 2,
    "procedural_order": 3
  },
  "route_mismatches": 0,
  "route_mismatches_with_failure": 0,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 29.84720002859831,
  "p95_ms": 38.38799998629838
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
  "command": "python -m src.benchmark --split regression --mode hybrid --live-answers --case-timeout 30 --report-tag rc5_attempt2_regression",
  "completed_at": "2026-09-29T06:26:24.554294+00:00",
  "verdict": "PASS \u2014 SELECTED CASES ONLY; RELEASE NOT ASSESSED",
  "schema_errors": [],
  "leakage": [],
  "report_tag": "rc5_attempt2_regression",
  "hashes": {
    "src\\answer_evaluation.py": "03d2030c0869e0c474767cee7ebecb96a01c0e580e1ac492d12ac58bc9575c6c",
    "src\\benchmark.py": "ff291d1740d88bbdf3baa6515f5bd8a32a668bd17cb517e2a28be0919cffdf6d",
    "data\\processed\\corpus_build.json": "99a6f9043fe2ab2c59730d648a4ce5437b83b40b2c8d2065f5c7a415cc296110",
    "data\\raw\\source_review.json": "f50b247f09a50385dbd3391f8cee53fd91621feb8692efb94fc4ffb6703d8825",
    "data\\raw\\corpus_manifest.json": "feadf6b032d811c670007730112b4e03199071bf99774bec7540d2ceb549288b",
    "benchmarks\\development.jsonl": "f423c3a50d4f167a8d1991dab56b31e6e3cba1d0a683f53ff9eebd3fb6308579",
    "benchmarks\\holdout.jsonl": "8a1688d7d92ae574a95cb835ddfadbd4cd0d6e86bcef7ad954031a6c239fed73",
    "benchmarks\\adversarial.jsonl": "d71365cbf30f83e7fbc79cd8a98d17372ac2f12768f868a8820ec1ee10144852",
    "benchmarks\\regression.jsonl": "506cb9cdc61f6542f41862848d35501045018a3f04efbc3202eb29ee36303e94"
  },
  "production_code_fingerprint": "0c7c3d9d3846f1c6b386e5624cac0c1afd9f578de13522546f909902ae3ec3eb",
  "corpus_build": {
    "schema_version": 3,
    "manifest_fingerprint": "2e7256712e2ac29d766606f90428b58f9bd991ec8bcdfd4b4121bd4500f90b5c",
    "code_fingerprint": "0c7c3d9d3846f1c6b386e5624cac0c1afd9f578de13522546f909902ae3ec3eb",
    "source_review_sha256": "f50b247f09a50385dbd3391f8cee53fd91621feb8692efb94fc4ffb6703d8825",
    "chunk_count": 220,
    "page_count": 81,
    "semantic": true,
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "model_fingerprint": "82df1d38da8f87d5ce84fcbc474c92b0c058b9cec863e9b75857648900397c4c",
    "fusion": "Reciprocal rank fusion k=60; +0.04 per exact identifier; eligible candidates only",
    "artifacts": {
      "fgw_356_5901_v15_pages.json": "ffeaa9fd9b1fc039e124e3a7ad73db882565696ffcdf0f86d44d2b23aa52b5e7",
      "chunks.json": "c077a4df20e0298a12a686d0a901e4d7a0dd5d4ebeb9b720b78cad9dcce1003f",
      "extraction_quality.json": "8b726a24b78533a5455c40d8c0a9e0928ac498c21afa6fea41d21f6ed85ac813",
      "chunk_statistics.json": "b5b98d452825f1d90919dd634a8096fbce2a8126e91a3e869abcbd1685e268d1",
      "vectors.faiss": "64ac6572daccd48a3ae321cf4f8843e979489cedb8ac5921a4f3331248034f6d",
      "vector_mapping.json": "dd264ecd758cfd5dec5ea0d9e311dd00d7df715cb7196d72c476b814e2979c39"
    },
    "build_seconds": 32.71901450003497
  },
  "cold_start_seconds": [
    4.208724600030109
  ],
  "files_unchanged_during_evaluation": true
}
```
