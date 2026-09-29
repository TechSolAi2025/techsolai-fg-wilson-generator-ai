# TechSolAi - FG Wilson Generator Operations, Preventive Maintenance & Basic Fault-Finding AI

A local, manufacturer-grounded Streamlit reference application for the **FG Wilson P Series and PRO rental series** scope stated in manual **356-5901(GB), V15 10/21**. It provides BM25, sentence-transformer/FAISS and hybrid retrieval, controller filtering, complete source procedures, exact citations and safe refusal. It does not establish individual-model service coverage or provide a numeric fault-code dictionary.

The repository contains the implementation, inspected corpus manifest, page-aware extraction, reviewed image-table transcriptions, processed chunks/indexes, separated benchmarks, automated tests and audit reports. The final release verdict is recorded in `docs/TECHSOLAI_GOLD_STANDARD_DEMO_AUDIT.md`; unit-test success alone is not demo readiness.

## Run on this workspace

```powershell
.\run_demo.ps1
```

Dependencies were installed locally in `.deps`; the launcher also supports `.venv`. The server binds to localhost. The pretrained model is stored under `data/models/all-MiniLM-L6-v2`; normal startup performs no model download. First model initialization is slower than subsequent searches.

## Reproduce in a new environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe scripts\download_model.py
.\.venv\Scripts\python.exe -m src.pipeline validate-manifest
.\.venv\Scripts\python.exe -m src.pipeline build
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.benchmark --split development --mode hybrid
.\.venv\Scripts\streamlit.exe run app\streamlit_app.py
```

The model download requires network access. The lock file records the Windows/Python 3.11 audit environment; other platforms may need compatible wheels. Retain the exact supplied source PDF filename and bytes. The source review is bound to its SHA-256 and is not reusable for an updated revision without a new audit. `scripts/register_source.py` reproduces registration for this inspected manual only; do not use it to auto-approve unrelated files. The manifest's approval is local user authorization, not certification by the manufacturer.

Builds validate every registered PDF, reject extras, duplicates and hash mismatches, preserve all 81 extracted pages, and quarantine reviewed problem sections. The completed build binds code, manifest, source review, model files, chunks and FAISS artifacts. Any incompatible or changed artifact disables technical answering at startup. `--lexical-only` is an explicit build option for development; the audited build includes semantic retrieval. Rebuild after source or core code changes. Never hand-edit processed artifacts to pass validation.

`data/raw/source_review.json` holds source-specific exclusions, applicability and image-table transcriptions. `data/processed` contains original page text, layout blocks, tables, review flags and deterministic chunks. `exports` contains case-level benchmark results, test output and the final machine-readable audit. No external chat model, API key or secret is required. Source documents are treated as data, not instructions.

## Scope and validation

Read `docs/MANUFACTURER_CORPUS_AUDIT.md`, `docs/V1_CORPUS_BOUNDARY.md`, `docs/EXTRACTION_QUALITY_REPORT.md`, `docs/CHUNK_QUALITY_REPORT.md`, `docs/BENCHMARK_METHODOLOGY.md` and `docs/KNOWN_LIMITATIONS.md`. Holdout results must not be used for ranking or grounding-rule tuning; improvements after the first evaluation need a new unseen holdout. No automatic deployment or publication is performed.

RC2 supports safety, pre-start inspections, operation, descriptive PowerWizard and DeepSea indications explicitly present in the manual, routine maintenance, service intervals, basic symptom/cause/remedy guidance, manufacturer-supported escalation and citations. It does not support a complete numerical fault-code dictionary, SPN/FMI diagnostics, controller internal service, wiring-level diagnosis, engine overhaul, component disassembly or unstated model-specific repair specifications. See `docs/RC2_REMEDIATION_REPORT.md` and `docs/QUARANTINE_REVIEW.md`.
