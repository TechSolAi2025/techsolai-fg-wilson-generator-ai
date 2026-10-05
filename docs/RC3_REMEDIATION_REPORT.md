# RC3 remediation report

FAIL — NOT DEMO READY

## Root cause and general correction

Ordinary query words matched controller UI identifiers, causing +0.04 exact-match contributions without controller context. Controller-specific descriptions displaced applicable general evidence and correctly triggered applicability refusal. Exact-match contributions now require explicit controller context for scoped chunks. Direct exact lookup and all grounding/refusal thresholds remain unchanged. No answer-generation change was needed.

Three new development questions reproduced this defect on different manufacturer passages before the change. All original queries, quotations and expected chunk IDs were retained. The two exposed cases moved from holdout to regression with exposed_holdout_failure_rc2 provenance; archived failed results remain unchanged.

A separate annotation defect was corrected: invert only the first complete manufacturer prohibition sentence, and distinguish a safe negative from its prohibited affirmative clause. This does not remove substantive source warnings. Eleven new development cases exercise routing, active-event reset negation, pressure/PPE conditions and unsupported code, SPN/FMI, interval, controller, bypass and internal-repair requests through production.

## Final measured results

Tests: 154; failures 0; errors 0. Live cases: 78/85 passed. Positive deterministic answer accuracy: 87.27%.

| Split | Passed / total | Positive accuracy |
|---|---:|---:|
| development | 35/35 | 1.0 |
| regression | 10/10 | 1.0 |
| adversarial | 8/8 | None |
| holdout | 25/32 | 0.7083333333333334 |

RC3 holdout retrieval: {'top1': 0.75, 'recall_at_3': 0.9166666666666666, 'recall_at_5': 0.9583333333333334}.
Supported exact identifiers: {'passed': 16, 'total': 16}. Two clean Streamlit startups: True.

```json
{
  "cases": 85,
  "passed": 78,
  "failed": 7,
  "answerable": 55,
  "deterministic_answer_accuracy": 0.8727272727272727,
  "failures_by_check": {
    "required": 7,
    "grounding": 3,
    "qualifiers": 2,
    "negations": 2,
    "safety": 4,
    "procedural_order": 1,
    "warnings": 1,
    "escalation": 1,
    "values": 1,
    "units": 1
  },
  "applicable_cases_by_check": {
    "grounding": 85,
    "required": 55,
    "negations": 13,
    "citation_document": 85,
    "citation_page_chunk": 85,
    "evidence_support": 85,
    "numerical_evidence": 52,
    "safety": 85,
    "prohibited": 9,
    "procedural_order": 11,
    "warnings": 27,
    "values": 7,
    "units": 7,
    "qualifiers": 23,
    "escalation": 12,
    "identifiers": 2,
    "unsupported_rejection": 30
  },
  "route_mismatches": 6,
  "route_mismatches_with_failure": 6,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 32.49279997544363,
  "p95_ms": 59.20369998784736
}
```

Failure categories overlap; a refusal may cause missing warning/qualifier requirements without emitting unsafe instructions. Zero failures with zero applicable fields do not certify coverage.

## One-time holdout and independence

The 32-case replacement was generated from source passages not used to design the remediation, with exact/paraphrase/noisy/symptom and unsupported/adversarial cases. Structured source annotations cover maintenance/procedure/safety/negation/qualifiers/warnings/escalation where present. An initial unevaluated draft lacked symptom coverage and was archived before a category-corrected draft was sealed. No RC3 results were read during implementation. The final holdout was run once after freeze. Its same-assistant construction is not genuinely independent; the generalization gate is NOT SATISFIED regardless of measured accuracy.

## Freeze and preservation

The new immutable evaluation_freeze_rc3.json and SHA-256 sidecar were verified immediately, before/after holdout, and at reporting. The freeze binds source code, evaluator, source PDF/manifest/review, processed chunks, actual in-memory BM25 state snapshot, FAISS artifacts, benchmark files, dependency versions, thread settings and exact commands. BM25 is reconstructed at runtime; its JSON snapshot records the real fitted state. Model fingerprint is bound to the corpus build. The stale freeze is retained as evaluation_freeze_rc1_historical.json and in the historical archive.

Compilation, full tests, corpus compatibility, source-literal scan, cross-split leakage checks, exact lookup and citation/safety tests ran. Original 64 queries/expected quotations/IDs were verified unchanged. Archived original holdout lineage is not counted as a duplicate current split; moved cases exist only in regression.

## Remaining blockers

- Independent construction of a new holdout is not demonstrated; same-assistant source-only construction is explicitly insufficient.
- Independent FG Wilson service-technician verification remains pending.
- One-time sealed RC3 live evaluation contains failures; no tuning or second unseen evaluation was performed.

## Commands

```powershell
python -m compileall -q src app tests scripts
python -m pytest -q --junitxml=exports/rc3_final_tests.xml
python -m src.benchmark --split development --mode hybrid --live-answers --report-tag rc3_development
python -m src.benchmark --split regression --mode hybrid --live-answers --report-tag rc3_regression
python -m src.benchmark --split adversarial --mode hybrid --live-answers --report-tag rc3_adversarial
python scripts/rc3_release.py holdout
python scripts/smoke_startup.py
python -m pytest -q tests/test_benchmarks.py::test_secret_scan
python scripts/rc3_release.py verify
```

Complete replacement code and current benchmark files are packaged in exports/rc3_replacement_files.zip. Source-specific evidence and all Top-5 scores are in RC3_FAILURE_ROOT_CAUSE.md and rc3_root_cause_evidence.json. Annotation coverage is in BENCHMARK_ANNOTATION_AUDIT.md and rc3_integrity.json.
