# Live gold-standard answer evaluation

PASS — SELECTED CASES ONLY; RELEASE NOT ASSESSED

The existing `src.benchmark` runner executes the production retrieval, safety-evidence and answering pipeline. There is no verified 150-case evaluator. This run uses existing benchmark records; selected split counts are reported below.

Command: `python -m src.benchmark --split regression --mode hybrid --live-answers --case-timeout 30 --report-tag rc4_regression`

Completed: 2026-09-29T06:00:16.338547+00:00

| Split | Cases | Passed | Failed | Deterministic positive-answer accuracy |
|---|---:|---:|---:|---:|
| regression | 15 | 15 | 0 | 1.0 |

## Aggregate measured results

```json
{
  "cases": 15,
  "passed": 15,
  "failed": 0,
  "answerable": 11,
  "deterministic_answer_accuracy": 1.0,
  "failures_by_check": {},
  "applicable_cases_by_check": {
    "grounding": 15,
    "unsupported_rejection": 4,
    "citation_document": 15,
    "citation_page_chunk": 15,
    "evidence_support": 15,
    "safety": 15,
    "required": 11,
    "escalation": 5,
    "warnings": 6,
    "numerical_evidence": 11,
    "prohibited": 2,
    "negations": 4,
    "qualifiers": 4,
    "values": 1,
    "units": 1,
    "procedural_order": 1
  },
  "route_mismatches": 0,
  "route_mismatches_with_failure": 0,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 55.8049000101164,
  "p95_ms": 72.84479995723814
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
  "command": "python -m src.benchmark --split regression --mode hybrid --live-answers --case-timeout 30 --report-tag rc4_regression",
  "completed_at": "2026-09-29T06:00:16.338547+00:00",
  "verdict": "PASS \u2014 SELECTED CASES ONLY; RELEASE NOT ASSESSED",
  "schema_errors": [],
  "leakage": [],
  "report_tag": "rc4_regression",
  "hashes": {
    "src\\answer_evaluation.py": "ec2c092f8d77bbde202b8a69f26668457f38e68a9ade1cfd839831d9c091fc05",
    "src\\benchmark.py": "ff291d1740d88bbdf3baa6515f5bd8a32a668bd17cb517e2a28be0919cffdf6d",
    "data\\processed\\corpus_build.json": "c7a7fe47d62ec58928fe1569dc3c9fcce42bd4a5fbca67910a36d3ade9a6c08b",
    "data\\raw\\source_review.json": "550e2f2176435ed84f7697982d31c78901c0c8feb26d262120e6187693211211",
    "data\\raw\\corpus_manifest.json": "feadf6b032d811c670007730112b4e03199071bf99774bec7540d2ceb549288b",
    "benchmarks\\development.jsonl": "c39fd22c74ba2e9793f64b136cda5ebaf26177f38ef41e302aa6eadf790f4d72",
    "benchmarks\\holdout.jsonl": "8a1688d7d92ae574a95cb835ddfadbd4cd0d6e86bcef7ad954031a6c239fed73",
    "benchmarks\\adversarial.jsonl": "d71365cbf30f83e7fbc79cd8a98d17372ac2f12768f868a8820ec1ee10144852",
    "benchmarks\\regression.jsonl": "18bab93901fd1955fd1413c87cd453083065d606ff2ad1e83b36cbb38e2e173f"
  },
  "production_code_fingerprint": "9fb9ac88444acd6c282a2f865969819d1f85ff61f8ec809c6dd0c3ab96821d9f",
  "corpus_build": {
    "schema_version": 3,
    "manifest_fingerprint": "2e7256712e2ac29d766606f90428b58f9bd991ec8bcdfd4b4121bd4500f90b5c",
    "code_fingerprint": "9fb9ac88444acd6c282a2f865969819d1f85ff61f8ec809c6dd0c3ab96821d9f",
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
    "build_seconds": 33.66942159994505
  },
  "cold_start_seconds": [
    5.469977999920957
  ],
  "files_unchanged_during_evaluation": true
}
```
