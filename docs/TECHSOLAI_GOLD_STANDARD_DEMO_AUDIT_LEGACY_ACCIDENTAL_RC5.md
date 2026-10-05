# AwanSolveAi Gold Standard Demo Audit

**FAIL â€” NOT DEMO READY**

The repository has a working local reference application and verified corpus build. Retrieval thresholds pass on the small development/holdout samples, but required deterministic-answer and exact-identifier gates do not. Critical service-expert validation and wider generalization are not established.

## 1. Exact manual inspected

**FG Wilson Generator Set Operator & Maintenance Instruction Manual**, **356-5901(GB), V15 10/21**, English, **81 PDF pages**. Exact filename: `FG Wilson Generator Set  Operator & Maintenance  Instruction Manual.pdf`. SHA-256: `ddb5a113826d97cb24456117cd1964223dc3cbb78ed1dc9cc8571b4ed1b029e5`. All pages were text-inspected and visually surveyed; image tables received enlarged inspection.

## 2. Exact V1 boundary

FG Wilson P Series and PRO rental series of generator sets; individual model applicability must be confirmed from the supplied set documentation. No individual generator model is approved by inference. Operator guidance, named controller functions, selected engine/filter procedures and qualified-technician maintenance reference only. See MANUFACTURER_CORPUS_AUDIT.md and V1_CORPUS_BOUNDARY.md.

## 3â€“4. Extraction and chunks

**81 pages extracted; 220 chunks; 43 quarantined; 177 eligible.** Printed pages are separate from PDF pages. Blank and weak pages remain recorded. See EXTRACTION_QUALITY_REPORT.md and CHUNK_QUALITY_REPORT.md.

| Primary category | Count |
|---|---:|
| alarms-shutdowns | 7 |
| alternator | 1 |
| battery-charging | 6 |
| control-panel-operation | 16 |
| cooling-system | 3 |
| electrical-checks | 4 |
| exhaust | 3 |
| fault-finding | 51 |
| fuel-system | 9 |
| general | 46 |
| generator-identification | 8 |
| installation-handling | 15 |
| lubrication | 3 |
| operating-procedures | 2 |
| pre-start-inspections | 1 |
| preventive-maintenance | 3 |
| qualified-service-escalation | 1 |
| safety | 18 |
| service-intervals | 1 |
| specifications | 13 |
| starting-stopping | 5 |
| storage | 4 |

## 5. Fault/alarm coverage

20 PowerWizard table rows and 17 visually transcribed DeepSea rows; FG100 protection-level descriptions. Controller scopes are preserved. There is **no numeric fault-code or SPN/FMI decoding dictionary**. Critical-failure rows and context also contribute to the 51 fault-finding chunks; that count is not a code count.

## 6. Tests and startup

**58 tests passed**, zero failures (28.85 seconds). **8 targeted follow-up checks passed** after UI/document/launcher changes. 21 Python files compiled. Corpus/index and frozen-core checks passed. Streamlit AppTest covers normal and degraded startup; two real HTTP startups passed. All smoke-test child processes were stopped.

## 7â€“8. Retrieval and answer metrics

| Split / mode | Top-1 | Recall@3 | Recall@5 | Unsupported rejection | Approved answer |
|---|---:|---:|---:|---:|---:|
| development_bm25 | 85.0% | 100.0% | 100.0% | 100.0% | 85.0% |
| development_semantic | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| development_hybrid | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| holdout_bm25 | 95.0% | 100.0% | 100.0% | 100.0% | 95.0% |
| holdout_semantic | 85.0% | 100.0% | 100.0% | 100.0% | 85.0% |
| holdout_hybrid | 90.0% | 100.0% | 100.0% | 100.0% | 90.0% |
| adversarial_hybrid | not measured | not measured | not measured | 100.0% | not measured |
| regression_hybrid | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

Development/holdout each contain 20 positive and 4 negative cases; adversarial has 8 negative cases; regression has 4 positive and 4 negative cases. No holdout ranking/grounding tuning was performed. Semantic-only retrieval is weaker here; the fixed hybrid design was not selected by tuning on holdout. Case-level results, including misses, are in exports.

Citation identity, extractive answer fidelity and numerical inclusion are 100% on emitted benchmark answers. These are source-text checks, not independent judgments of critical relevance, warning completeness or service safety. Exact lookup passes **13/16** audited keys; missing keys are listed below.

## 9. Leakage / overfitting

**0 exact/near-duplicate question pairs detected** across all four splits using the documented lexical tests. No full benchmark questions/answers were found embedded in production lookup logic; exact source identifier literals are permitted. Core build and benchmark hashes match the pre-holdout freeze. Same-author, single-manual and semantic-leakage limitations remain.

## 10. Latency

Hybrid cold start: **10.06 s development**, **17.69 s holdout**. Median query latency: **70.48 ms / 90.98 ms**; holdout p95 **112.93 ms**. Full build: **32.34 s**. HTTP server health became ready in approximately 0.58 s, 0.52 s. HTTP health excludes app/model initialization.

Measured locally on CPU with bounded thread counts and sequential evaluations. Unbounded parallel processes initially exhausted memory; successful runs use OMP/MKL/OPENBLAS=2. The local dependency layout also required disabling Streamlit development mode in the launcher. These operational fixes did not alter frozen retrieval or grounding.

## 11. Remaining blockers

- Expected-answer gate below 100%: development 90%, holdout 95%, regression 75%.
- Deterministic critical lookup incomplete: ISO 22241-1 and spelled-out Every Two Weeks / Every Month are not indexed as exact keys (13/16 checked keys pass). Lexical/semantic retrieval may still locate these sources.
- Independent service-expert verification of critical answers, warnings, numerical/source ambiguities and image transcriptions is pending.
- 43 chunks remain quarantined, including icon-dependent FG100 instructions, lifting diagrams, illustrative specifications and source discrepancies.
- One small, same-author/manual holdout cannot establish cross-document or broader field generalization. Further ranking/grounding changes need a new unseen holdout.
- Exact model/serial-specific engine/controller/alternator service documents and diagnostic code catalogs are absent.

## 12. Final gate

**FAIL â€” NOT DEMO READY.** The application can be run locally for engineering review with `./run_demo.ps1`. Do not present it as having passed the AwanSolveAi Gold Standard. The JSON audit records PASS, sampled baseline results and NOT ESTABLISHED gates separately.

| Required gate | Result |
|---|---|
| syntax_imports | PASS |
| automated_regression_tests | PASS |
| retrieval_top1 | PASS |
| retrieval_recall_at_3 | PASS |
| retrieval_recall_at_5 | PASS |
| exact_critical_identifiers | FAIL |
| unsupported_rejection | PASS_ON_SAMPLES |
| approved_deterministic_answers | FAIL |
| citation_source_identity | PASS_ON_EMITTED_SAMPLES |
| critical_citation_faithfulness | NOT_ESTABLISHED |
| unsupported_identifier_hallucinations | ZERO_OBSERVED_ON_SAMPLES |
| critical_grounded_answer_failures | NOT_ESTABLISHED |
| safety_regressions | ZERO_OBSERVED_ON_TESTS |
| critical_numerical_unit_consistency | BASELINE_PASS_EXPERT_REVIEW_PENDING |
| corpus_index_compatibility | PASS |
| exposed_secrets | ZERO_PATTERN_MATCHES |
| repeatable_startup | PASS |
| unseen_holdout_generalization | LIMITED_SINGLE_MANUAL_ONLY |
| unseen_paraphrase_robustness | LIMITED_SAMPLE |
| typo_noisy_robustness | LIMITED_SAMPLE |
| benchmark_leakage | PASS_LEXICAL_BASELINE |
| hard_coded_benchmark_answers | ZERO_DETECTED |
| overfitting_audit | BASELINE_PASS |
| prompt_document_injection_baseline | PASS_ON_TESTS |
| known_limitations | DOCUMENTED |

