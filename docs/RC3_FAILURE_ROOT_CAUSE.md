# RC3 failure root cause

Phase 1 completed without modifying production code. Expectations were re-derived from the original approved PDF, pages 7 and 33, including visual page inspection; this is a separate source check by the implementing assistant, not independent FG Wilson technician approval. Original failures and freezes are preserved in exports/historical_pre_rc3.

## Shared architectural cause

Quoted controller UI labels are indexed as identifiers. Search applies the +0.04 exact-key contribution even when a generic query uses the label as an ordinary word and no controller is selected. STOP and LEFT therefore promote controller-specific descriptions over applicable general guidance. The applicability refusal is correct for the incorrectly selected source. Grounding thresholds and the conservative refusal must remain unchanged. The generic correction is to condition contributions from controller-scoped identifiers on explicit controller context; direct exact lookup remains available.

## Individual diagnosis

### holdout-001

Query: Is the emergency stop suitable for ordinary stopping?

Intended route: 2.1.1 Emergency Stop Button, manufacturer PDF/printed page 7; no controller required.
Actual route: 5.3.1 PowerWizard 2.1+ Control Module Description; controller ['PowerWizard 2.1+']. Exact identifier incorrectly triggered by ordinary word STOP.
Expected answerability: true. Actual status: ambiguous; Select the fitted controller to resolve applicability.

| Rank | Chunk ID | Score | PDF pages | Evidence reasons |
|---|---|---:|---|---|
| 1 | `fgw_356_5901_v15:814e915d66b54ae7f9be8d2f` | 0.06519288 | [46, 47] | BM25=1.69720; coverage=0.29336; cosine=0.27466; deterministic exact identifier |
| 2 | `fgw_356_5901_v15:cb3d98473f199ca5f8669621` | 0.06430556 | [48, 49] | BM25=1.50227; coverage=0.29336; cosine=0.28171; deterministic exact identifier |
| 3 | `fgw_356_5901_v15:fc9dfae558dfe2d5997ccc7e` | 0.03477375 | [7, 7] | BM25=12.23256; coverage=0.47073; cosine=0.52542 |
| 4 | `fgw_356_5901_v15:e0d1744679540039337b19e7` | 0.03252247 | [71, 71] | BM25=9.78141; coverage=0.47073; cosine=0.54990 |
| 5 | `fgw_356_5901_v15:b8fe3e348da2a27bf6e9f048` | 0.03174603 | [45, 45] | BM25=6.21481; coverage=0.28141; cosine=0.35210 |

Selected evidence supplied to answering: `fgw_356_5901_v15:814e915d66b54ae7f9be8d2f`, `fgw_356_5901_v15:cb3d98473f199ca5f8669621`, `fgw_356_5901_v15:fc9dfae558dfe2d5997ccc7e`, `fgw_356_5901_v15:e0d1744679540039337b19e7`, `fgw_356_5901_v15:b8fe3e348da2a27bf6e9f048`, `fgw_356_5901_v15:65c1499d4f89fc6f9a39a292`. No evidence was emitted because applicability rejected the first hit.

Expected and missing obligations (all missing from the refused answer):

required:
- DO NOT use emergency shutoff devices or controls for normal stopping procedure.
qualifiers:
- Not applicable.
negations:
- I DO NOT use emergency shutoff devices or controls for normal stopping procedure.
warnings:
- Warning:
- I Read and understand all safety precautions and warnings before operating the generator set.
- I Failure to follow the instructions, procedures and safety precautions in this manual may increase the possibility of accidents and injuries.
- I Never start the generator set unless it is safe to do so.
- I Do not attempt to operate the generator set with a known unsafe condition.
- I If the generator set is unsafe, fit danger notices and disconnect the battery negative (–) lead so that it cannot be started until the condition is corrected.
- I Ensure the generator set is protected from any unauthorised use, use signs were appropriate.
- I Disconnect the battery negative (–) lead prior to attempting installation, repairs or cleaning on the generator set.
- I Install and operate this generator set only in full compliance with relevant National, Local, or Federal Codes, Standards or other requirements.
- I Familiarise yourself with the location of the Emergency Stop Button. Emergency shutoff controls are for EMERGENCY use ONLY.
- I DO NOT use emergency shutoff devices or controls for normal stopping procedure.
- I Do not start the engine until the problem necessitating the emergency stop has been located and corrected.
escalation:
- Not applicable.

Origin: retrieval identifier scope and consequent evidence selection. Not missing manufacturer evidence, a mistaken positive label, or unsafe answer composition. The raw query coverage of the approved excerpt must still meet the existing answer threshold; no threshold changes are authorized. Warning/qualifier/escalation omissions are downstream of refusal. The warning heading alone is annotation formatting, not a technical obligation; substantive warnings remain required.

### holdout-016

Query: Engine left idle for longer than one month storage protection

Intended route: 4.5.1 Engine Storage, manufacturer PDF/printed page 33; no controller required.
Actual route: 5.3.1 PowerWizard 2.1+ Control Module Description; controller ['PowerWizard 2.1+']. Exact identifier incorrectly triggered by ordinary word LEFT.
Expected answerability: true. Actual status: ambiguous; Select the fitted controller to resolve applicability.

| Rank | Chunk ID | Score | PDF pages | Evidence reasons |
|---|---|---:|---|---|
| 1 | `fgw_356_5901_v15:814e915d66b54ae7f9be8d2f` | 0.06093382 | [46, 47] | BM25=6.65109; coverage=0.27821; cosine=0.13474; deterministic exact identifier |
| 2 | `fgw_356_5901_v15:cb3d98473f199ca5f8669621` | 0.06050135 | [48, 49] | BM25=6.10698; coverage=0.27821; cosine=0.13463; deterministic exact identifier |
| 3 | `fgw_356_5901_v15:5df3887ff95481e9b09b8aac` | 0.03409313 | [33, 33] | BM25=19.41570; coverage=0.50579; cosine=0.52671 |
| 4 | `fgw_356_5901_v15:1b43373076b0114a0937bf92` | 0.03297578 | [33, 33] | BM25=15.29868; coverage=0.36870; cosine=0.36506 |
| 5 | `fgw_356_5901_v15:ea91854c470a63a107812c42` | 0.03248738 | [33, 33] | BM25=7.53323; coverage=0.16328; cosine=0.40993 |

Selected evidence supplied to answering: `fgw_356_5901_v15:814e915d66b54ae7f9be8d2f`, `fgw_356_5901_v15:cb3d98473f199ca5f8669621`, `fgw_356_5901_v15:5df3887ff95481e9b09b8aac`, `fgw_356_5901_v15:1b43373076b0114a0937bf92`, `fgw_356_5901_v15:ea91854c470a63a107812c42`, `fgw_356_5901_v15:65c1499d4f89fc6f9a39a292`. No evidence was emitted because applicability rejected the first hit.

Expected and missing obligations (all missing from the refused answer):

required:
- complete protection procedure is recommended
qualifiers:
- The engine should be put through an engine “preservation” procedure that includes cleaning the engine and replacing all the fluids with new or preserving fluids. If an engine is out of operation and if use of the engine is not planned, special precautions should be made. If the engine will be stored for more than 1 month, a complete protection procedure is recommended. Please consult your local FG Wilson Dealer for more information on engine storage.
negations:
- The engine should be put through an engine “preservation” procedure that includes cleaning the engine and replacing all the fluids with new or preserving fluids. If an engine is out of operation and if use of the engine is not planned, special precautions should be made. If the engine will be stored for more than 1 month, a complete protection procedure is recommended. Please consult your local FG Wilson Dealer for more information on engine storage.
warnings:
- I Before storage of the generator set please perform all required maintenance as recommended. For storage periods greater than one year please contact your local FG Wilson dealer for proper storage instructions.
escalation:
- The engine should be put through an engine “preservation” procedure that includes cleaning the engine and replacing all the fluids with new or preserving fluids. If an engine is out of operation and if use of the engine is not planned, special precautions should be made. If the engine will be stored for more than 1 month, a complete protection procedure is recommended. Please consult your local FG Wilson Dealer for more information on engine storage.

Origin: retrieval identifier scope and consequent evidence selection. Not missing manufacturer evidence, a mistaken positive label, or unsafe answer composition. The raw query coverage of the approved excerpt must still meet the existing answer threshold; no threshold changes are authorized. Warning/qualifier/escalation omissions are downstream of refusal. The warning heading alone is annotation formatting, not a technical obligation; substantive warnings remain required.
