# Benchmark data

Use `development.jsonl` for development only. Freeze the implementation before evaluating `holdout.jsonl`. `adversarial.jsonl` and `regression.jsonl` exercise rejection and retained behavior. See `docs/BENCHMARK_METHODOLOGY.md` for source labeling, metrics, leakage checks, limitations and split discipline.

Run `python -m src.benchmark --split development --mode hybrid`. Each run validates the corpus/build before loading indexes and writes an outcome report under `exports/`. Modes: `bm25`, `semantic`, `hybrid`. Do not copy questions or expected answers into application code.
