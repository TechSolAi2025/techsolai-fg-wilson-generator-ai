# RC5 Remediation Report

## Current verdict

**FAIL - NOT DEMO READY**

RC5 internal hardening has passed and an immutable candidate freeze has been created. Final release remains blocked by the independent blind holdout and independent qualified technician validation.

## Internal results

| Gate | Result |
|---|---:|
| Full pytest | 188/188 PASS |
| RC5 table tests | 24/24 PASS |
| Development | 40/40 PASS |
| Regression | 17/17 PASS |
| Adversarial | 8/8 PASS |
| Exact identifiers | 16/16 PASS |
| Streamlit HTTP startup | 2/2 PASS |

## Internal Gold Standard gates

```json
{
  "compilation": true,
  "full_tests_188": true,
  "rc5_table_tests_24": true,
  "development": true,
  "regression": true,
  "adversarial": true,
  "positive_answer_accuracy": true,
  "route_mismatches_zero": true,
  "errors_zero": true,
  "timeouts_zero": true,
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
  "units": true,
  "exact_identifiers_16": true,
  "schema": true,
  "active_split_leakage": true,
  "production_benchmark_literals": true,
  "two_streamlit_startups": true,
  "corpus_build_compatible": true,
  "artifact_hashes_verified": true,
  "source_review_verified": true,
  "table_group_count_6": true,
  "table_complete_groups_5": true,
  "table_complete_row_counts": true,
  "quarantine_count_43": true,
  "fg100_incomplete_contract": true,
  "sound_level_merged_contract": true
}
```

## Candidate freeze

`exports/evaluation_freeze_rc5_candidate.json`

SHA-256: `647044abca72f9b6b37026fa0bed26a54c40242348799e34f802ca275c1ff170`

Verified files: 67

## Remaining release blockers

- Independent blind holdout construction and once-only evaluation are NOT SATISFIED.
- Independent qualified FG Wilson technician validation remains PENDING.

No independent holdout was executed by this script. Historical/exposed benchmark sets remain diagnostic only and cannot satisfy independence.
