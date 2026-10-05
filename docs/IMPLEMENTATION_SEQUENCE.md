# Implementation and release sequence

1. Inspect the exact FG Wilson source, register its hash and preserve its stated applicability.
2. Retain every extracted page; record weak/image content and reviewed transcriptions.
3. Preserve section/procedure units, source warnings and separate table rows; quarantine unresolved content.
4. Build BM25, embeddings and FAISS with explicit artifact/code/source compatibility.
5. Curate development and separate holdout/adversarial/regression cases from source evidence.
6. Verify development behavior, corruption/refusal tests and UI startup; freeze the implementation.
7. Evaluate the untouched holdout and remaining suites without tuning to their results.
8. Publish a truthful gate report. Changes after holdout evaluation require a new unseen holdout for any renewed generalization claim.

Current measured results and outstanding release work are in `AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md`.

