# Benchmark annotation audit

All 64 original records audited against approved-source identity and pages. Queries, expected quotations and expected chunk IDs are unchanged. Structured fields add source-derived detail without relaxing expected outcomes. Historical JSONL files remain in exports/historical_pre_rc3/benchmarks.

Explicit empty lists and annotation_not_applicable distinguish absent annotations from measured success. Required value/unit lists are paired by position. Expected source document and route are citation/applicability metadata, never technical prose. Grader instructions and rationale stay outside assertions.

Prohibited assertions are affirmative counterparts of complete explicit manufacturer prohibitions. Conditional prohibitions are excluded from automatic inversion. The grader must distinguish the original safe negation from its prohibited affirmative counterpart. Unsupported cases require clean refusal; arbitrary fictional fault meanings are not invented just to fill annotation fields.

Meaningful field counts (original 64 records):

| Field | Covered cases |
|---|---:|
| expected_chunk_ids | 44 |
| expected_pages | 44 |
| expected_route | 64 |
| expected_source_document | 44 |
| prohibited_assertions | 8 |
| required_assertions | 44 |
| required_escalation | 10 |
| required_identifiers | 2 |
| required_negations | 12 |
| required_qualifiers | 19 |
| required_units | 8 |
| required_values | 8 |
| required_warnings | 24 |

| Case | Split | Positive | Native PDF / reviewed source |
|---|---|---|---|
| development-001 | development | True | native PDF text |
| development-002 | development | True | native PDF text |
| development-003 | development | True | native PDF text |
| development-004 | development | True | native PDF text |
| development-005 | development | True | native PDF text |
| development-006 | development | True | source-bound table/image transcription; visual page review required |
| development-007 | development | True | native PDF text |
| development-008 | development | True | native PDF text |
| development-009 | development | True | native PDF text |
| development-010 | development | True | native PDF text |
| development-011 | development | True | native PDF text |
| development-012 | development | True | native PDF text |
| development-013 | development | True | native PDF text |
| development-014 | development | True | source-bound table/image transcription; visual page review required |
| development-015 | development | True | native PDF text |
| development-016 | development | True | native PDF text |
| development-017 | development | True | native PDF text |
| development-018 | development | True | native PDF text |
| development-019 | development | True | native PDF text |
| development-020 | development | True | native PDF text |
| development-negative-001 | development | False | documented corpus boundary and clean refusal; no invented answer assertion |
| development-negative-002 | development | False | documented corpus boundary and clean refusal; no invented answer assertion |
| development-negative-003 | development | False | documented corpus boundary and clean refusal; no invented answer assertion |
| development-negative-004 | development | False | documented corpus boundary and clean refusal; no invented answer assertion |
| holdout-001 | holdout | True | native PDF text |
| holdout-002 | holdout | True | native PDF text |
| holdout-003 | holdout | True | native PDF text |
| holdout-004 | holdout | True | native PDF text |
| holdout-005 | holdout | True | native PDF text |
| holdout-006 | holdout | True | source-bound table/image transcription; visual page review required |
| holdout-007 | holdout | True | source-bound table/image transcription; visual page review required |
| holdout-008 | holdout | True | native PDF text |
| holdout-009 | holdout | True | native PDF text |
| holdout-010 | holdout | True | native PDF text |
| holdout-011 | holdout | True | native PDF text |
| holdout-012 | holdout | True | native PDF text |
| holdout-013 | holdout | True | native PDF text |
| holdout-014 | holdout | True | native PDF text |
| holdout-015 | holdout | True | native PDF text |
| holdout-016 | holdout | True | native PDF text |
| holdout-017 | holdout | True | native PDF text |
| holdout-018 | holdout | True | native PDF text |
| holdout-019 | holdout | True | native PDF text |
| holdout-020 | holdout | True | native PDF text |
| holdout-negative-001 | holdout | False | documented corpus boundary and clean refusal; no invented answer assertion |
| holdout-negative-002 | holdout | False | documented corpus boundary and clean refusal; no invented answer assertion |
| holdout-negative-003 | holdout | False | documented corpus boundary and clean refusal; no invented answer assertion |
| holdout-negative-004 | holdout | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-001 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-002 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-003 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-004 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-005 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-006 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-007 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| adversarial-negative-008 | adversarial | False | documented corpus boundary and clean refusal; no invented answer assertion |
| regression-negative-001 | regression | False | documented corpus boundary and clean refusal; no invented answer assertion |
| regression-negative-002 | regression | False | documented corpus boundary and clean refusal; no invented answer assertion |
| regression-negative-003 | regression | False | documented corpus boundary and clean refusal; no invented answer assertion |
| regression-negative-004 | regression | False | documented corpus boundary and clean refusal; no invented answer assertion |
| regression-001 | regression | True | native PDF text |
| regression-002 | regression | True | native PDF text |
| regression-003 | regression | True | native PDF text |
| regression-004 | regression | True | native PDF text |

Annotation defects separate from product defects: legacy records had only a short quote; unit pairs, source conditions, warnings and explicit prohibitions were under-annotated. Warning headings are formatting, not technical assertions. Source warnings themselves are retained. The two product failures remain incorrect routing followed by conservative refusal.

Image/table expectation checks use the approved original PDF and hash-bound reviewed rows; they are not independent technician verification. Separate source verification does not establish independent authorship.


Final original-64 coverage after correction:

```json
{
  "required_assertions": 44,
  "prohibited_assertions": 8,
  "required_identifiers": 2,
  "required_values": 8,
  "required_units": 8,
  "required_qualifiers": 19,
  "required_negations": 12,
  "required_warnings": 24,
  "required_escalation": 10,
  "expected_source_document": 44,
  "expected_pages": 44,
  "expected_chunk_ids": 44,
  "expected_route": 64
}
```

The four image-table expectations were visually checked against original PDF pages 55 and 56. A uniform pre-freeze annotation correction limited prohibited alternatives to the first complete source prohibition sentence; no required warnings or original quotations were relaxed.
