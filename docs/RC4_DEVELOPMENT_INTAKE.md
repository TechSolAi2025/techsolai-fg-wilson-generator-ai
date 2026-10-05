# RC4 development intake

A new development cycle is opened from the completed, one-time RC3 evaluation. These seven cases are now exposed. RC3 code, thresholds, benchmark bytes and results remain frozen; no post-evaluation patch or rerun was performed. Measured failures are retained. Some causes may be annotation defects rather than product defects; they must be independently checked against manufacturer pages before regression promotion.

| Exposed case | Status | Manufacturer pages | Investigation |
|---|---|---|---|
| rc3-sealed-003 | grounded | [74] | Annotation/field placement review: expected quotation is a qualified-service warning. Verify whether it is already correctly present in emitted warnings before defining a technical-answer failure. |
| rc3-sealed-007 | insufficient | [10] | Product answerability/retrieval investigation: a positive case is refused. Verify framing-token coverage on separate new source passages. |
| rc3-sealed-013 | insufficient | [11] | Product answerability/retrieval investigation: a positive case is refused. Verify framing-token coverage on separate new source passages. |
| rc3-sealed-014 | insufficient | [52] | Product answerability/retrieval investigation: a positive case is refused. Verify framing-token coverage on separate new source passages. |
| rc3-sealed-015 | grounded | [35] | Annotation and corpus review: broad query is mapped to one particular table row; some rows contain empty or displaced column labels. Verify whether the expectation is uniquely warranted before treating the route as a product defect. |
| rc3-sealed-023 | grounded | [32] | Evidence composition review: illustration labels were returned in place of substantive explanatory text. Verify source paragraph and surrounding context. |
| rc3-sealed-024 | grounded | [13] | Annotation and corpus review: broad query is mapped to one particular table row; some rows contain empty or displaced column labels. Verify whether the expectation is uniquely warranted before treating the route as a product defect. |

Next-cycle entry criteria: separately verify expectations, construct new development examples from different passages, test generic causes there, and obtain genuinely independent holdout authorship. Do not convert these recorded failures into passes by changing the existing frozen expectations.
