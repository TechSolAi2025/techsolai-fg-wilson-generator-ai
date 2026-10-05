# Known limitations

- One 2021 operator/maintenance manual supports family-level FG Wilson P Series and PRO rental series guidance. No independent individual-model coverage, cross-document generalization, engine service diagnosis or comprehensive fault/SPN/FMI decoding is established.
- There are 215 chunks, including ten source-reviewed reconstructions; the 43 original quarantined chunks remain excluded from answering because they contain image-dependent instructions, illustrative data, source ambiguity or out-of-scope material. All pages remain in the extraction; exclusion is explicit in the source review.
- DeepSea fault tables on pages 55–56 were visually transcribed by the implementing agent. They retain row association but still require independent service-expert checking. Some multiple-symptom cells remain joined as in the original. The exact DSE model is unspecified.
- Section-based chunking keeps procedures together but sometimes yields long chunks. Semantic windows reduce truncation, although dense 160-word windows can exceed 256 subword tokens. A complete semantic coverage guarantee is not established.
- General source sections may contain several topics. Primary categories are not mutually exhaustive topic labels; air intake, automatic operation, symptom/cause/remedy and service escalation also appear within other categories. A separate standalone chunk is not invented for every topic.
- Answers are extractive. Verbatim source fidelity and matching numbers do not establish relevance, completeness, safe applicability or sufficient warnings. Some source-correct excerpts fail the curated expected-answer criterion. Responses can be longer than a concise service summary because procedures are kept complete.
- Safety context is selected heuristically. Section-level inherited warnings are preserved, but comprehensive cross-section warning recall and statement-level expert faithfulness are not certified. Qualified-service classification includes dealer-referral wording and reviewed section rules; the manual's overall qualified-personnel boundaries remain applicable.
- Conflict handling covers competing documents/revisions, multiple controller contexts and same-shape numerical contradictions. It is not a general semantic contradiction detector. The source itself contains inconsistent internal references and apparent numerical/wording issues; identified sections are quarantined instead of corrected.
- Injection protection combines extractive output, no tool execution from documents, source integrity, quarantine and lexical detection. Passing the test suite is a baseline, not proof against all paraphrased or encoded attacks. A party able to rewrite the approved manifest, source review and build metadata is outside the local integrity threat model; no digital-signature trust root is implemented.
- Question-leakage checks are lexical. The same agent authored both splits from one manual, so holdout is separate from tuning but not externally blind. No reranking, fine-tuning or benchmark-answer lookup is used. A larger independent holdout is still needed.
- The model and dependencies consume memory at cold start. Unbounded concurrent benchmark processes caused OpenBLAS/MemoryError failures during validation; sequential runs with OMP, MKL and OPENBLAS thread counts set to 2 succeeded. The launcher sets these limits. Do not interpret warm response latency as cold-start latency.
- Model files and source PDF must be transferred separately when reproducing from version control. The lock file records this Windows/Python 3.11 environment, not a guarantee of wheel availability on every platform. Runtime is local and does not download models automatically.
- Secret scanning covers known token/private-key patterns in project source, configuration, documents and exports. Zero findings is a scoped scan result, not a forensic guarantee.

See the final audit for measured metrics and the release verdict. Obtain the model/serial-specific technical, engine, alternator/AVR, controller and transfer-panel documents listed in the corpus audit before expanding scope.

## Live answer audit

The current 64-case live run passes 62 cases. Holdout-001 and holdout-016 return controller-ambiguity refusals, leaving required content and warnings absent. Full positive-answer accuracy is 42/44; holdout is 18/20. No production tuning was performed during evaluator repair. The legacy records lack exhaustive independent assertion annotations; prohibited-assertion annotation coverage is zero. Independent technician review remains pending. See GOLD_STANDARD_ANSWER_EVALUATION.md for measured counts and bounded grading limits.


## RC3 current status

The earlier live-answer figures above are historical. See RC3_REMEDIATION_REPORT.md for current results. Generic controller-identifier scope was corrected without changing answer thresholds. A replacement source-only sealed holdout is not independently constructed; its generalization gate is NOT SATISFIED. It was evaluated once after freeze. Independent FG Wilson technician validation remains pending.


## RC4 current status

Earlier sections are historical. RC4 remains FAIL — NOT DEMO READY. See RC4_REMEDIATION_REPORT.md for current measured diagnostics. Five exposed source-supported cases are now regressions, not independent tests. Anonymous table cells are refused pending header/context recovery. Broad table topics still need a reviewed completeness/clarification contract. Independent holdout authorship and technician validation remain pending.


## RC5 candidate status

RC5 internal hardening passes, but this is only a candidate freeze. Independent blind holdout evaluation has not been run and qualified FG Wilson technician validation remains pending. Therefore the project is not yet DEMO READY. The manual covers the documented FG Wilson P Series / PRO rental family boundary only; it does not establish inferred individual-model specifications, unsupported controller applicability, a numeric SPN/FMI dictionary, or undocumented internal repair procedures.
