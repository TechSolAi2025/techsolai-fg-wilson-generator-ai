"""Generate the RC5 internal-hardening report and immutable candidate freeze.

IMPORTANT:
- This script does NOT evaluate an unseen/independent holdout.
- This script does NOT perform or claim technician validation.
- A successful run establishes only an RC5 candidate freeze.
- It must never declare the product DEMO READY by itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
import hashlib
import json
import os
import platform
import sys
import xml.etree.ElementTree as ET

from src.answer_evaluation import schema_errors, summarize
from src.benchmark import leakage, load
from src.retrieval import HybridRetriever
from src.store import code_fingerprint, validate_build


ROOT = Path(__file__).resolve().parents[1]

FINAL_REPORTS = {
    "development": ROOT
    / "exports"
    / "gold_standard_answer_results_rc5_final_internal_development.json",
    "regression": ROOT
    / "exports"
    / "gold_standard_answer_results_rc5_final_internal_regression.json",
    "adversarial": ROOT
    / "exports"
    / "gold_standard_answer_results_rc5_final_internal_adversarial.json",
}

FULL_TEST_XML = ROOT / "exports" / "rc5_final_internal_tests.xml"
TABLE_TEST_XML = ROOT / "exports" / "rc5_table_tests.xml"
STARTUP_JSON = ROOT / "exports" / "startup_smoke_rc5_final_internal.json"
DEPENDENCIES = ROOT / "exports" / "rc5_candidate_dependencies.txt"

FREEZE_JSON = ROOT / "exports" / "evaluation_freeze_rc5_candidate.json"
FREEZE_SHA = ROOT / "exports" / "evaluation_freeze_rc5_candidate.sha256"
FREEZE_VERIFY = ROOT / "exports" / "rc5_candidate_freeze_verification.json"

INTEGRITY_JSON = ROOT / "exports" / "rc5_integrity.json"
EXACT_JSON = ROOT / "exports" / "rc5_exact_lookup.json"
FINAL_JSON = ROOT / "exports" / "gold_standard_answer_results_rc5.json"

TABLE_REPORT = ROOT / "docs" / "RC5_TABLE_HARDENING_REPORT.md"
REMEDIATION_REPORT = ROOT / "docs" / "RC5_REMEDIATION_REPORT.md"
MAIN_AUDIT = ROOT / "docs" / "AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md"
KNOWN_LIMITATIONS = ROOT / "docs" / "KNOWN_LIMITATIONS.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def junit_summary(path: Path) -> dict:
    root = ET.parse(path).getroot()

    if root.tag == "testsuite":
        suites = [root]
    elif root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    else:
        raise ValueError(
            f"Unexpected JUnit root in {path}: {root.tag}"
        )

    def total(key: str) -> int:
        return sum(
            int(s.attrib.get(key, 0))
            for s in suites
        )

    return {
        "tests": total("tests"),
        "failures": total("failures"),
        "errors": total("errors"),
        "skipped": total("skipped"),
        "time": sum(
            float(s.attrib.get("time", 0))
            for s in suites
        ),
    }


def compile_project() -> list[str]:
    compiled: list[str] = []

    for directory in (
        "src",
        "app",
        "tests",
        "scripts",
        "benchmarks",
    ):
        folder = ROOT / directory

        if not folder.exists():
            continue

        for path in sorted(folder.glob("*.py")):
            compile(
                path.read_text(
                    encoding="utf-8-sig"
                ),
                str(path),
                "exec",
            )
            compiled.append(
                str(path.relative_to(ROOT))
            )

    return compiled


def production_text() -> str:
    text: list[str] = []

    for directory in ("src", "app"):
        folder = ROOT / directory

        if not folder.exists():
            continue

        for path in sorted(folder.glob("*.py")):
            text.append(
                path.read_text(
                    encoding="utf-8-sig"
                ).casefold()
            )

    return "\n".join(text)


def scan_production_literals() -> list[dict]:
    corpus = production_text()
    findings: list[dict] = []

    # These are all already-known benchmark sets.
    # Reading them here is only a static anti-hardcoding check.
    # No holdout is executed by this script.
    for path in sorted(
        (ROOT / "benchmarks").glob("*.jsonl")
    ):
        try:
            cases = load(path)
        except Exception as exc:
            findings.append(
                {
                    "file": str(
                        path.relative_to(ROOT)
                    ),
                    "kind": "load_error",
                    "value": str(exc),
                }
            )
            continue

        for case in cases:
            values = [
                ("query", case.get("query", "")),
                ("id", case.get("id", "")),
                (
                    "expected_quote",
                    case.get("expected_quote", ""),
                ),
            ]

            values.extend(
                ("chunk_id", chunk_id)
                for chunk_id in case.get(
                    "expected_chunk_ids",
                    [],
                )
            )

            for kind, value in values:
                if (
                    isinstance(value, str)
                    and value
                    and value.casefold() in corpus
                ):
                    findings.append(
                        {
                            "file": str(
                                path.relative_to(ROOT)
                            ),
                            "id": case.get("id"),
                            "kind": kind,
                            "value": value,
                        }
                    )

    return findings


def active_split_integrity(byid: dict) -> tuple:
    active = {
        name: load(
            ROOT
            / "benchmarks"
            / f"{name}.jsonl"
        )
        for name in (
            "development",
            "regression",
            "adversarial",
        )
    }

    schema = []

    for split, cases in active.items():
        for case in cases:
            errors = schema_errors(case, byid)

            if errors:
                schema.append(
                    {
                        "split": split,
                        "id": case.get("id"),
                        "errors": errors,
                    }
                )

    leaks = []

    for (
        split_a,
        cases_a,
    ), (
        split_b,
        cases_b,
    ) in combinations(
        active.items(),
        2,
    ):
        for finding in leakage(
            cases_a,
            cases_b,
        ):
            leaks.append(
                {
                    "split_a": split_a,
                    "split_b": split_b,
                    "finding": finding,
                }
            )

    return active, schema, leaks


def exact_identifier_check(
    chunks,
) -> list[dict]:
    source = ROOT / "exports" / "rc4_exact_lookup.json"

    if not source.exists():
        raise FileNotFoundError(
            "Missing exports/rc4_exact_lookup.json"
        )

    old = read_json(source)
    retriever = HybridRetriever(chunks)

    results = []

    for previous in old:
        identifier = previous["identifier"]
        hits = retriever.exact_lookup(identifier)

        results.append(
            {
                "identifier": identifier,
                "matched": bool(hits),
                "all_eligible": all(
                    not h.chunk.review_required
                    for h in hits
                ),
                "chunk_ids": [
                    h.chunk.chunk_id
                    for h in hits
                ],
            }
        )

    write_json(EXACT_JSON, results)

    return results


def verify_report(
    path: Path,
    expected_fingerprint: str,
) -> dict:
    report = read_json(path)

    if (
        report.get(
            "production_code_fingerprint"
        )
        != expected_fingerprint
    ):
        raise ValueError(
            f"Production fingerprint mismatch: {path.name}"
        )

    if (
        report.get(
            "files_unchanged_during_evaluation"
        )
        is not True
    ):
        raise ValueError(
            f"Files changed during evaluation: {path.name}"
        )

    for rel, digest in report.get(
        "hashes",
        {},
    ).items():
        target = ROOT / rel

        if not target.is_file():
            raise ValueError(
                f"Missing benchmark-bound file: {rel}"
            )

        if sha(target) != digest:
            raise ValueError(
                f"Benchmark-bound hash mismatch: {rel}"
            )

    summary = report.get("summary", {})

    if summary.get("failed") != 0:
        raise ValueError(
            f"Failed cases in {path.name}"
        )

    if summary.get("errors") != 0:
        raise ValueError(
            f"Errors in {path.name}"
        )

    if summary.get("timeouts") != 0:
        raise ValueError(
            f"Timeouts in {path.name}"
        )

    if (
        summary.get("route_mismatches")
        != 0
    ):
        raise ValueError(
            f"Route mismatches in {path.name}"
        )

    return report


def table_integrity(
    chunks,
    source_review: dict,
) -> dict:
    groups = {
        c.table["id"]: c.table
        for c in chunks
        if c.table
        and c.table.get("kind")
        != "obsolete"
    }

    complete = [
        t
        for t in groups.values()
        if t.get("complete")
    ]

    controls = [
        t
        for t in groups.values()
        if t.get("role") == "control"
    ]

    measurement = [
        t
        for t in groups.values()
        if t.get("role")
        == "measurement"
    ]

    sound_spec = next(
        spec
        for spec in source_review[
            "table_groups"
        ]
        if spec["section"]
        == "2.10 Sound Level Information"
    )

    sound_ok = (
        sound_spec.get("approved") is True
        and sound_spec.get("expected_rows")
        == 5
        and sound_spec.get("role")
        == "measurement"
        and sound_spec.get(
            "correct_headers"
        )
        is True
        and sound_spec.get("parts")
        == [
            {
                "page": 13,
                "table": 0,
                "header_row": 1,
                "merged_cells": [
                    {
                        "column": 0,
                        "start": 2,
                        "end": 6,
                    }
                ],
            }
        ]
    )

    return {
        "group_count": len(groups),
        "complete_group_count": len(
            complete
        ),
        "expected_rows_complete": sorted(
            t["expected_rows"]
            for t in complete
        ),
        "quarantined_chunks": sum(
            c.review_required
            for c in chunks
        ),
        "control_groups": len(controls),
        "control_incomplete": (
            len(controls) == 1
            and controls[0].get(
                "complete"
            )
            is False
        ),
        "measurement_groups": len(
            measurement
        ),
        "sound_level_review_contract":
            sound_ok,
    }


def freeze_paths(
    build: dict,
) -> list[Path]:
    paths: list[Path] = []

    for directory in (
        "src",
        "app",
        "tests",
        "scripts",
        "benchmarks",
    ):
        folder = ROOT / directory

        if not folder.exists():
            continue

        for path in folder.glob("*"):
            if path.suffix in (
                ".py",
                ".jsonl",
            ):
                paths.append(path)

    required = [
        ROOT
        / "data"
        / "raw"
        / "corpus_manifest.json",
        ROOT
        / "data"
        / "raw"
        / "source_review.json",
        ROOT
        / "data"
        / "processed"
        / "corpus_build.json",
        ROOT / "requirements-lock.txt",
        ROOT / "pyproject.toml",
        ROOT / "run_demo.ps1",
        FULL_TEST_XML,
        TABLE_TEST_XML,
        STARTUP_JSON,
        DEPENDENCIES,
        INTEGRITY_JSON,
        EXACT_JSON,
    ]

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(
                f"Required freeze input missing: {path}"
            )
        paths.append(path)

    for filename in build["artifacts"]:
        path = (
            ROOT
            / "data"
            / "processed"
            / filename
        )

        if not path.is_file():
            raise FileNotFoundError(
                f"Build artifact missing: {path}"
            )

        paths.append(path)

    manuals = (
        ROOT
        / "data"
        / "raw"
        / "manuals"
    ).glob("*.pdf")

    paths.extend(manuals)

    paths.extend(
        FINAL_REPORTS.values()
    )

    for path in FINAL_REPORTS.values():
        if not path.is_file():
            raise FileNotFoundError(
                f"Final RC5 report missing: {path}"
            )

    reviewer_docs = [
        ROOT
        / "docs"
        / "RC5_INDEPENDENT_HOLDOUT_PROTOCOL.md",
        ROOT
        / "docs"
        / "RC5_REVIEWER_BOUNDARY.md",
        ROOT
        / "docs"
        / "RC5_TECHNICIAN_VALIDATION_FORM.md",
    ]

    for path in reviewer_docs:
        if not path.is_file():
            raise FileNotFoundError(
                f"Reviewer package missing: {path}"
            )

        paths.append(path)

    return sorted(
        {
            path.resolve()
            for path in paths
        }
    )


def verify_freeze(
    frozen: Path,
    expected_sha: str,
) -> dict:
    current_sha = sha(frozen)

    if current_sha != expected_sha:
        raise ValueError(
            "Candidate freeze SHA mismatch"
        )

    freeze = read_json(frozen)
    failures = []

    for rel, digest in freeze["files"].items():
        path = ROOT / rel

        if not path.is_file():
            failures.append(
                {
                    "file": rel,
                    "error": "missing",
                }
            )
            continue

        actual = sha(path)

        if actual != digest:
            failures.append(
                {
                    "file": rel,
                    "error": "hash_mismatch",
                    "expected": digest,
                    "actual": actual,
                }
            )

    result = {
        "verified": not failures,
        "freeze_sha256": current_sha,
        "files_checked": len(
            freeze["files"]
        ),
        "failures": failures,
        "independent_holdout":
            freeze["independent_holdout"],
        "technician_validation":
            freeze["technician_validation"],
    }

    write_json(
        FREEZE_VERIFY,
        result,
    )

    if failures:
        raise ValueError(
            "Candidate freeze verification failed"
        )

    return result


def main() -> None:
    if FREEZE_JSON.exists():
        raise FileExistsError(
            "RC5 candidate freeze already exists. "
            "Refusing to overwrite it."
        )

    if FREEZE_SHA.exists():
        raise FileExistsError(
            "RC5 candidate freeze SHA already exists. "
            "Refusing to overwrite it."
        )

    manifest, build, chunks = validate_build(
        ROOT
    )

    current_fingerprint = code_fingerprint(
        ROOT
    )

    if (
        build["code_fingerprint"]
        != current_fingerprint
    ):
        raise ValueError(
            "Corpus build fingerprint does not match current production code"
        )

    byid = {
        c.chunk_id: c
        for c in chunks
    }

    reports = {
        split: verify_report(
            path,
            current_fingerprint,
        )
        for split, path
        in FINAL_REPORTS.items()
    }

    rows = [
        case
        for report in reports.values()
        for case in report["cases"]
    ]

    summary = summarize(rows)

    full_tests = junit_summary(
        FULL_TEST_XML
    )

    table_tests = junit_summary(
        TABLE_TEST_XML
    )

    startups = read_json(
        STARTUP_JSON
    )

    if not isinstance(startups, list):
        raise ValueError(
            "Startup smoke result must be a list"
        )

    compiled = compile_project()

    active, schema, leaks = (
        active_split_integrity(byid)
    )

    literals = (
        scan_production_literals()
    )

    exact = exact_identifier_check(
        chunks
    )

    source_review = read_json(
        ROOT
        / "data"
        / "raw"
        / "source_review.json"
    )

    tables = table_integrity(
        chunks,
        source_review,
    )

    exact_pass = all(
        x["matched"]
        and x["all_eligible"]
        for x in exact
    )

    benchmark_gate = {
        split: (
            reports[split]["summary"][
                "failed"
            ]
            == 0
        )
        for split
        in reports
    }

    gates = {
        "compilation": True,
        "full_tests_188": (
            full_tests["tests"] == 188
            and full_tests["failures"] == 0
            and full_tests["errors"] == 0
        ),
        "rc5_table_tests_24": (
            table_tests["tests"] == 24
            and table_tests["failures"] == 0
            and table_tests["errors"] == 0
        ),
        "development": (
            benchmark_gate["development"]
            and reports[
                "development"
            ]["summary"]["passed"]
            == 40
        ),
        "regression": (
            benchmark_gate["regression"]
            and reports[
                "regression"
            ]["summary"]["passed"]
            == 17
        ),
        "adversarial": (
            benchmark_gate["adversarial"]
            and reports[
                "adversarial"
            ]["summary"]["passed"]
            == 8
        ),
        "positive_answer_accuracy": (
            reports[
                "development"
            ]["summary"][
                "deterministic_answer_accuracy"
            ]
            == 1.0
            and reports[
                "regression"
            ]["summary"][
                "deterministic_answer_accuracy"
            ]
            == 1.0
        ),
        "route_mismatches_zero": all(
            report["summary"][
                "route_mismatches"
            ]
            == 0
            for report in reports.values()
        ),
        "errors_zero": all(
            report["summary"]["errors"]
            == 0
            for report in reports.values()
        ),
        "timeouts_zero": all(
            report["summary"]["timeouts"]
            == 0
            for report in reports.values()
        ),
        "unsupported_rejection": (
            summary[
                "failures_by_check"
            ].get(
                "unsupported_rejection",
                0,
            )
            == 0
        ),
        "citation_document": (
            summary[
                "failures_by_check"
            ].get(
                "citation_document",
                0,
            )
            == 0
        ),
        "citation_page_chunk": (
            summary[
                "failures_by_check"
            ].get(
                "citation_page_chunk",
                0,
            )
            == 0
        ),
        "evidence_support": (
            summary[
                "failures_by_check"
            ].get(
                "evidence_support",
                0,
            )
            == 0
        ),
        "safety": (
            summary[
                "failures_by_check"
            ].get(
                "safety",
                0,
            )
            == 0
        ),
        "qualifiers": (
            summary[
                "failures_by_check"
            ].get(
                "qualifiers",
                0,
            )
            == 0
        ),
        "negations": (
            summary[
                "failures_by_check"
            ].get(
                "negations",
                0,
            )
            == 0
        ),
        "warnings": (
            summary[
                "failures_by_check"
            ].get(
                "warnings",
                0,
            )
            == 0
        ),
        "escalation": (
            summary[
                "failures_by_check"
            ].get(
                "escalation",
                0,
            )
            == 0
        ),
        "values": (
            summary[
                "failures_by_check"
            ].get(
                "values",
                0,
            )
            == 0
        ),
        "units": (
            summary[
                "failures_by_check"
            ].get(
                "units",
                0,
            )
            == 0
        ),
        "exact_identifiers_16": (
            exact_pass
            and len(exact) == 16
        ),
        "schema": not schema,
        "active_split_leakage": (
            not leaks
        ),
        "production_benchmark_literals": (
            not literals
        ),
        "two_streamlit_startups": (
            len(startups) == 2
            and all(
                x.get("http_health")
                is True
                for x in startups
            )
        ),
        "corpus_build_compatible": True,
        "artifact_hashes_verified": True,
        "source_review_verified": True,
        "table_group_count_6": (
            tables["group_count"] == 6
        ),
        "table_complete_groups_5": (
            tables[
                "complete_group_count"
            ]
            == 5
        ),
        "table_complete_row_counts": (
            tables[
                "expected_rows_complete"
            ]
            == [
                5,
                10,
                10,
                12,
                17,
            ]
        ),
        "quarantine_count_43": (
            tables[
                "quarantined_chunks"
            ]
            == 43
        ),
        "fg100_incomplete_contract": (
            tables[
                "control_incomplete"
            ]
            is True
        ),
        "sound_level_merged_contract": (
            tables[
                "sound_level_review_contract"
            ]
            is True
        ),
    }

    integrity = {
        "current_code_fingerprint":
            current_fingerprint,
        "corpus_build_code_fingerprint":
            build["code_fingerprint"],
        "model_fingerprint":
            build["model_fingerprint"],
        "manifest_fingerprint":
            build["manifest_fingerprint"],
        "source_sha256":
            manifest["documents"][0][
                "sha256"
            ],
        "source_review_sha256":
            build[
                "source_review_sha256"
            ],
        "schema_errors": schema,
        "active_split_leakage": leaks,
        "production_literals":
            literals,
        "table_integrity": tables,
        "compiled_files": compiled,
        "historical_rc5_attempts_preserved":
            all(
                (
                    ROOT
                    / "exports"
                    / name
                ).exists()
                for name in (
                    "gold_standard_answer_results_rc5_attempt1_development.json",
                    "gold_standard_answer_results_rc5_attempt1_regression.json",
                    "gold_standard_answer_results_rc5_attempt1_adversarial.json",
                    "gold_standard_answer_results_rc5_attempt2_development.json",
                    "gold_standard_answer_results_rc5_attempt2_regression.json",
                    "gold_standard_answer_results_rc5_attempt2_adversarial.json",
                )
            ),
    }

    write_json(
        INTEGRITY_JSON,
        integrity,
    )

    if not all(gates.values()):
        failed = [
            key
            for key, value
            in gates.items()
            if not value
        ]

        raise RuntimeError(
            "RC5 internal gate failure(s): "
            + ", ".join(failed)
        )

    stamp = datetime.now(
        timezone.utc
    ).isoformat()

    commands = [
        "python -B -m pytest tests/test_rc5_tables.py -q -p no:cacheprovider --junitxml=exports/rc5_table_tests.xml",
        "python -B -m pytest -q -p no:cacheprovider --junitxml=exports/rc5_final_internal_tests.xml",
        reports[
            "development"
        ]["command"],
        reports[
            "regression"
        ]["command"],
        reports[
            "adversarial"
        ]["command"],
        "python scripts/smoke_startup.py --report-tag rc5_final_internal",
        "python scripts/rc5_report.py",
    ]

    paths = freeze_paths(build)

    freeze = {
        "release": "RC5",
        "kind": (
            "candidate internal-hardening freeze; "
            "not a release authorization"
        ),
        "created_at": stamp,
        "files": {
            str(
                path.relative_to(ROOT)
            ): sha(path)
            for path in paths
        },
        "code_fingerprint":
            current_fingerprint,
        "model_fingerprint":
            build["model_fingerprint"],
        "source_sha256":
            manifest["documents"][0][
                "sha256"
            ],
        "source_review_sha256":
            build[
                "source_review_sha256"
            ],
        "manifest_fingerprint":
            build[
                "manifest_fingerprint"
            ],
        "python": sys.version,
        "python_executable":
            sys.executable,
        "platform":
            platform.platform(),
        "thread_limits": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
            )
        },
        "commands": commands,
        "gates": gates,
        "internal_status":
            "PASS",
        "independent_holdout":
            "NOT SATISFIED - NOT RUN",
        "technician_validation":
            "PENDING",
        "release_authorized":
            False,
        "demo_ready":
            False,
    }

    with FREEZE_JSON.open(
        "x",
        encoding="utf-8",
    ) as handle:
        json.dump(
            freeze,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    freeze_digest = sha(
        FREEZE_JSON
    )

    with FREEZE_SHA.open(
        "x",
        encoding="utf-8",
    ) as handle:
        handle.write(
            freeze_digest + "\n"
        )

    verification = verify_freeze(
        FREEZE_JSON,
        freeze_digest,
    )

    blockers = [
        (
            "Independent blind holdout construction and "
            "once-only evaluation are NOT SATISFIED."
        ),
        (
            "Independent qualified FG Wilson technician "
            "validation remains PENDING."
        ),
    ]

    result = {
        "release": "RC5",
        "evaluation_kind": (
            "production-pipeline final internal "
            "hardening diagnostics; not unseen "
            "release evaluation"
        ),
        "completed_at": stamp,
        "internal_verdict":
            "PASS - RC5 CANDIDATE FREEZE CREATED",
        "release_verdict":
            "FAIL - NOT DEMO READY",
        "summary": summary,
        "splits": {
            split: report["summary"]
            for split, report
            in reports.items()
        },
        "tests": full_tests,
        "table_tests": table_tests,
        "startup": startups,
        "gates": gates,
        "supported_exact_identifiers": {
            "passed": sum(
                x["matched"]
                and x["all_eligible"]
                for x in exact
            ),
            "total": len(exact),
        },
        "integrity": integrity,
        "freeze_sha256":
            freeze_digest,
        "freeze_verification":
            verification,
        "remaining_blockers":
            blockers,
        "independent_holdout": {
            "evaluated": False,
            "status":
                "NOT SATISFIED - NOT RUN",
        },
        "technician_validation": {
            "status": "PENDING",
        },
        "cases": rows,
    }

    write_json(
        FINAL_JSON,
        result,
    )

    table_lines = [
        "# RC5 Table Hardening Report",
        "",
        "## Status",
        "",
        "**PASS - internal RC5 table hardening.**",
        "",
        (
            "This is internal structural validation only. "
            "Independent technician validation remains pending."
        ),
        "",
        "## Verified structure",
        "",
        f"- Table groups: {tables['group_count']}",
        (
            "- Complete table groups: "
            f"{tables['complete_group_count']}"
        ),
        (
            "- Complete row counts: "
            f"{tables['expected_rows_complete']}"
        ),
        (
            "- Quarantined chunks retained: "
            f"{tables['quarantined_chunks']}"
        ),
        (
            "- FG100 incomplete-table refusal contract: "
            f"{tables['control_incomplete']}"
        ),
        (
            "- Sound-level merged-span review contract: "
            f"{tables['sound_level_review_contract']}"
        ),
        "",
        "## RC5 explicit table tests",
        "",
        (
            f"**{table_tests['tests']} tests, "
            f"{table_tests['failures']} failures, "
            f"{table_tests['errors']} errors.**"
        ),
        "",
        (
            "Explicit coverage includes missing members, "
            "quarantine, revision/section mismatch, ordering, "
            "controller applicability, connected retrieval, "
            "prompt injection, duplicate membership, false "
            "continuation, conflicting merged cells, verified "
            "merged-span propagation, real FG100 complete-table "
            "refusal, and real five-row sound-level provenance."
        ),
        "",
        "## Release boundary",
        "",
        (
            "The table hardening result does not replace the "
            "independent holdout or qualified technician review."
        ),
        "",
    ]

    TABLE_REPORT.write_text(
        "\n".join(table_lines),
        encoding="utf-8",
    )

    remediation_lines = [
        "# RC5 Remediation Report",
        "",
        "## Current verdict",
        "",
        "**FAIL - NOT DEMO READY**",
        "",
        (
            "RC5 internal hardening has passed and an immutable "
            "candidate freeze has been created. Final release "
            "remains blocked by the independent blind holdout "
            "and independent qualified technician validation."
        ),
        "",
        "## Internal results",
        "",
        "| Gate | Result |",
        "|---|---:|",
        (
            f"| Full pytest | "
            f"{full_tests['tests']}/"
            f"{full_tests['tests']} PASS |"
        ),
        (
            f"| RC5 table tests | "
            f"{table_tests['tests']}/"
            f"{table_tests['tests']} PASS |"
        ),
        (
            "| Development | "
            f"{reports['development']['summary']['passed']}/"
            f"{reports['development']['summary']['cases']} PASS |"
        ),
        (
            "| Regression | "
            f"{reports['regression']['summary']['passed']}/"
            f"{reports['regression']['summary']['cases']} PASS |"
        ),
        (
            "| Adversarial | "
            f"{reports['adversarial']['summary']['passed']}/"
            f"{reports['adversarial']['summary']['cases']} PASS |"
        ),
        (
            "| Exact identifiers | "
            f"{result['supported_exact_identifiers']['passed']}/"
            f"{result['supported_exact_identifiers']['total']} PASS |"
        ),
        (
            "| Streamlit HTTP startup | "
            f"{sum(x['http_health'] for x in startups)}/"
            f"{len(startups)} PASS |"
        ),
        "",
        "## Internal Gold Standard gates",
        "",
        "```json",
        json.dumps(
            gates,
            indent=2,
        ),
        "```",
        "",
        "## Candidate freeze",
        "",
        (
            "`exports/evaluation_freeze_rc5_candidate.json`"
        ),
        "",
        f"SHA-256: `{freeze_digest}`",
        "",
        (
            f"Verified files: "
            f"{verification['files_checked']}"
        ),
        "",
        "## Remaining release blockers",
        "",
        *[
            "- " + blocker
            for blocker in blockers
        ],
        "",
        (
            "No independent holdout was executed by this script. "
            "Historical/exposed benchmark sets remain diagnostic "
            "only and cannot satisfy independence."
        ),
        "",
    ]

    remediation_text = "\n".join(
        remediation_lines
    )

    REMEDIATION_REPORT.write_text(
        remediation_text,
        encoding="utf-8",
    )

    # Replace the stale legacy audit with the current RC5 report.
    MAIN_AUDIT.write_text(
        remediation_text,
        encoding="utf-8",
    )

    limitation_heading = (
        "## RC5 candidate status"
    )

    limitation_text = (
        "\n\n"
        + limitation_heading
        + "\n\n"
        + "RC5 internal hardening passes, but this is only a "
        + "candidate freeze. Independent blind holdout "
        + "evaluation has not been run and qualified FG Wilson "
        + "technician validation remains pending. Therefore the "
        + "project is not yet DEMO READY. The manual covers the "
        + "documented FG Wilson P Series / PRO rental family "
        + "boundary only; it does not establish inferred "
        + "individual-model specifications, unsupported "
        + "controller applicability, a numeric SPN/FMI "
        + "dictionary, or undocumented internal repair "
        + "procedures.\n"
    )

    existing = (
        KNOWN_LIMITATIONS.read_text(
            encoding="utf-8"
        )
        if KNOWN_LIMITATIONS.exists()
        else ""
    )

    if limitation_heading not in existing:
        with KNOWN_LIMITATIONS.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                limitation_text
            )

    audit_machine = {
        key: value
        for key, value in result.items()
        if key != "cases"
    }

    write_json(
        ROOT
        / "exports"
        / "AwanSolveAi_gold_standard_demo_audit.json",
        audit_machine,
    )

    print(
        json.dumps(
            {
                "internal_verdict":
                    result[
                        "internal_verdict"
                    ],
                "release_verdict":
                    result[
                        "release_verdict"
                    ],
                "tests": full_tests,
                "table_tests":
                    table_tests,
                "splits":
                    result["splits"],
                "exact_identifiers":
                    result[
                        "supported_exact_identifiers"
                    ],
                "freeze_sha256":
                    freeze_digest,
                "freeze_verified":
                    verification[
                        "verified"
                    ],
                "remaining_blockers":
                    blockers,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
