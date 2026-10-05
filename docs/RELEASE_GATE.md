# AwanSolveAi release gate

Required: all syntax/import and automated tests pass; Top-1 >=95%, Recall@3 >=98%, Recall@5 preferably 100%; critical exact lookup, unsupported rejection, approved deterministic answers, citation identity, critical faithfulness and numerical consistency at 100%; no unsupported identifier hallucinations, safety regressions, exposed secrets, leakage or benchmark answer hard-coding. Build compatibility, repeatable startup, injection baseline, overfitting review, unseen holdout/paraphrase/noise performance and documented limitations are also required.

The machine-readable gate result is `exports/AwanSolveAi_gold_standard_demo_audit.json`; the human-readable report is `docs/AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md`. A limited sample or passing extractive checks cannot substitute for expert critical-answer review. Unmeasured required gates remain NOT ESTABLISHED, never automatically PASS.

