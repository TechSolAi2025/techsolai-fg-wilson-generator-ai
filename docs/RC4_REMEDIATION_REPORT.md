# RC4 remediation report

FAIL — NOT DEMO READY

Current-state verification initially found only RC4 intake files. All 50 RC3 frozen files and corpus/model compatibility verified. In-memory compilation and 154 tests passed; read-only production baselines reproduced 35/35 development, 10/10 regression and 8/8 adversarial. No Git repository was present. The only stated corpus-count discrepancy was 215 rather than 205 chunks (ten previously reviewed recoveries).

## Implemented changes

General retrieval normalization adds show, advise and observed to the bounded stop list. A leading directive plus guidance/instructions/precautions plus for/about/concerning is removed only from query terms; document terms remain unchanged. Unknown technical terms, negation, quantities and conditions remain. Subject ranking uses Fault cells for troubleshooting rows and rewards focused titles only when existing 0.55 evidence coverage is met. Answering refuses anonymous/incomplete table cells. An explicitly annotated warning can satisfy a required warning in the warning field; citation and claim checks still apply. No answer quotation route, benchmark-ID rule, chunk-ID rule, weaker refusal threshold or LLM judge was introduced.

Five source-verified exposed cases were promoted with unchanged technical expectations. Two new source-defined development cases exercise oils safety and a different PowerWizard fault row. Two ambiguous table-row annotations remain diagnostics and are not counted as repaired. Full forensics and corpus decisions are in RC4_FAILURE_FORENSICS.md and RC4_CORPUS_COVERAGE_DECISION.md.

## Completed production diagnostics

| Split | Passed / total | Positive accuracy |
|---|---:|---:|
| development | 37/37 | 100.00% |
| regression | 15/15 | 100.00% |
| adversarial | 8/8 | N/A |

Tests: 164 passed with 0 failures and 0 errors. Exact identifiers: 16/16. Two Streamlit HTTP startups: True.

```json
{
  "cases": 60,
  "passed": 60,
  "failed": 0,
  "answerable": 38,
  "deterministic_answer_accuracy": 1.0,
  "failures_by_check": {},
  "applicable_cases_by_check": {
    "grounding": 60,
    "required": 38,
    "negations": 11,
    "citation_document": 60,
    "citation_page_chunk": 60,
    "evidence_support": 60,
    "numerical_evidence": 38,
    "safety": 60,
    "prohibited": 7,
    "procedural_order": 9,
    "warnings": 19,
    "values": 6,
    "units": 6,
    "qualifiers": 13,
    "escalation": 9,
    "identifiers": 1,
    "unsupported_rejection": 22
  },
  "route_mismatches": 0,
  "route_mismatches_with_failure": 0,
  "errors": 0,
  "timeouts": 0,
  "median_ms": 52.588250022381544,
  "p95_ms": 58.77710005734116
}
```

These are real production retrieval and answering runs, not mocked verdicts. Latencies include retrieval/answering, exclude model cold start, and use nearest-rank p95. No RC3 holdout was rerun. Historical 25/32 and 17/24 positive accuracy remain historical, not RC4 accuracy. Diagnostic success does not satisfy independence or technician validation.

## Gates

```json
{
  "compilation": true,
  "tests": true,
  "development": true,
  "regression": true,
  "adversarial": true,
  "exact_identifiers": true,
  "schema": true,
  "leakage": true,
  "production_literals": true,
  "two_streamlit_startups": true,
  "unsupported_rejection": true,
  "citation_document": true,
  "citation_page_chunk": true,
  "evidence_support": true,
  "safety": true,
  "qualifiers": true,
  "negations": true,
  "warnings": true,
  "escalation": true,
  "values": true,
  "units": true
}
```

No new release evaluation is authorized by this development freeze. Corpus remains 81 pages, 215 chunks, 43 quarantined. Original RC2/RC3 reports and freezes remain; all 50 RC3 inputs are recoverable and hash-verified in rc3_frozen_state_before_rc4.zip. Current code intentionally differs from RC3. Original holdout bytes are unchanged. Intermediate RC4 diagnostic attempts are retained.

## Remaining blockers

- Independent holdout construction is NOT SATISFIED; no RC4 holdout was created or evaluated.
- Independent qualified FG Wilson technician validation remains pending.
- Broad critical-failure questions lack a reviewed multi-row/clarification answer contract.
- Sound-level table header, applicability and measurement-context recovery remains unfinished; anonymous table answers now require review.

## Commands

Set PYTHONPATH=.deps;., PYTHONIOENCODING=utf-8, and OMP_NUM_THREADS/MKL_NUM_THREADS/OPENBLAS_NUM_THREADS=2.

```powershell
python -m compileall -q src app tests scripts benchmarks
python -B -m pytest -q -p no:cacheprovider --junitxml=exports/rc4_tests.xml
python -m src.benchmark --split development --mode hybrid --live-answers --case-timeout 30 --report-tag rc4_development
python -m src.benchmark --split regression --mode hybrid --live-answers --case-timeout 30 --report-tag rc4_regression
python -m src.benchmark --split adversarial --mode hybrid --live-answers --case-timeout 30 --report-tag rc4_adversarial
python scripts/smoke_startup.py --report-tag rc4
python scripts/rc4_report.py
```

Complete replacement files: exports/rc4_replacement_files.zip. Machine-readable results and immutable development freeze: exports/gold_standard_answer_results_rc4.json and exports/evaluation_freeze_rc4.json.
