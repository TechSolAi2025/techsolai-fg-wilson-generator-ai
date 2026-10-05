# Manufacturer corpus audit

Audit date: 2026-09-10. One PDF was found recursively under `data/raw/manuals`. All 81 PDF pages were text-inspected; rendered contact sheets were reviewed across the whole document, with enlarged inspection of image-only fault tables and critical pages. This is an agent source audit; independent FG Wilson service-expert approval has not been obtained.

| Field | Source finding |
|---|---|
| Exact filename | `FG Wilson Generator Set  Operator & Maintenance  Instruction Manual.pdf` (double spaces preserved) |
| Exact title | FG Wilson Generator Set Operator & Maintenance Instruction Manual |
| Manufacturer / commercial brand | FG Wilson |
| Legal manufacturer named | Caterpillar (NI) Limited, declarations on PDF/printed 20–21; Caterpillar NI Ltd on 19 |
| Document number | 356-5901(GB) |
| Revision / printed date | V15 10/21; October 2021. No publication day stated. |
| Language | English; marked ORIGINAL INSTRUCTIONS |
| PDF pages | 81 |
| Printed pages | Cover unnumbered; PDF 2–81 correspond to printed 2–81. Footer glyph duplication yields text such as `7676`, not printed page 7,676. |
| PDF metadata dates | Creation 2022-02-21; modification 2022-03-18. These are file metadata, not the printed publication date. |
| SHA-256 | `ddb5a113826d97cb24456117cd1964223dc3cbb78ed1dc9cc8571b4ed1b029e5` |
| Stated applicability | Cover: FG Wilson P Series and PRO rental series of generator sets. |
| Individual generator models | No approved individual-model list. Pxxx-x and rating-plate values are illustrative placeholders, not product-specific coverage. |
| Approval | User authorized this supplied manual for implementation; identity verified against cover. Approval does not certify every procedure. |

## Explicit engine references

PDF/printed 13: the regional sound table names 400 Series (6.8–24 kVA), 1100 Series (24–220 kVA), 1500 Series (225–375 kVA), 2000 Series (350–938 kVA), and 4000 Series (800–2500 kVA). This is sound-emission context, not a service applicability matrix. PDF 18 names 4008, 4012 and 4016 powered models only in the vibration-isolator mounting description. Section 6.1, page 66, names 1100 Series priming; 6.1.2, page 67, names Perkins 1506, 2206, 2506 and 2806 with pre-filter/water separator. Racor is an optional filter configuration in 6.1.3, page 68. No engine overhaul or full engine diagnostic coverage is established by these mentions.

## Controllers and transfer panels

- 5.2, pages 38–45: PowerWizard 1.1, 1.1+, 2.1. The clock and fuel-transfer subsections specifically name 2.1. Under-voltage row applies to 2.1 only; over-voltage is standard on 2.1 and optional on 1.1+.
- 5.3, pages 46–52: PowerWizard 2.1+ and 4.1; their module descriptions are separate. Stop-related remedies differ from 5.2 and must not be mixed.
- 5.4, pages 53–56: DeepSea Controller. No explicit numerical DSE model designation was found; do not infer a model from panel appearance.
- 5.5, pages 57–63: FG100. Includes indicators, event viewing, operating modes, protection levels and programming. Some button identities exist only as images.
- Section 7, page 72: CTI and ATI Series Intelligent Transfer Panels are named. Detailed user guides are not actually included in this supplied PDF.

## Document sections

| Section | PDF / printed pages | Coverage |
|---|---|---|
| Cover / contents | 1–5 | Scope, revision, contents; page 2 blank apart from footer |
| 1 Introduction | 6 | Authorized/trained personnel, identification, illustrative images |
| 2 Safety | 7–17 | General, PPE, air/water pressure, spillage, hoses, waste, fire, exhaust, mechanical, chemical, noise, electrical isolation, sound, first aid, aftertreatment, hazard labels |
| 3 General Description | 18–23 | Typical rating/PIN plates, example declarations, components, power factor |
| 4 Installation, Handling and Storage | 24–35 | Siting, lifting, foundations, storage, expected life, limiting conditions and critical failures |
| 5 Control System Description and Trouble Shooting | 36–65 | Pre-start inspection, controller-specific operation, event logs, symptom/remedy tables, options |
| 6 Operation | 66–71 | Selected fuel priming/draining procedures, jump starting, conservation, cold weather, fluids, engine operation, inducement override |
| 7 Load Transfer Panels | 72–73 | CTI/ATI overview and output circuit breaker |
| 8 Maintenance | 74–78 | Battery, preventive intervals, alternator/engine referral, DEF filters, welding, disposal |
| Notes / blank | 79–81 | No technical answer content |

## Safety-warning types and scope

The manual uses Warning / WARNING, triangular hazard symbols that extract as `I`, Notes / NOTE, IMPORTANT text, and pictorial hazard labels. No standalone textual `Caution` label was found. Hazards include automatic starting, electrocution, hot/pressurized fluids, fuel/fire/explosion, battery acid/gas, moving parts, noise, lifting/crushing, and DEF exposure. Source instructions remain data and cannot alter application rules. First-aid instructions and emissions-override activation are excluded from technical answering. Installation/lifting drawings are retained but lifting procedures require further diagram-aware validation.

## Maintenance schedules actually supplied

Section 8, page 74, reserves maintenance/service for qualified technicians. Section 8.2, page 76, limits operators to section 5 pre-start checks and warns that engine intervals may be more frequent.

- Daily / each startup: walk-around and pre-start checks; standby sets may use weekly checks.
- Every two weeks: standby sets that have not run, operational check for only 5 minutes.
- Monthly: standby sets not run on load, at least 50% load for 1–2 hours; fuel tank water/sediment and applicable dual-wall bund drainage.
- Every twelve months or 500 hours: daily procedures plus safety-device testing by simulated faults, battery cap vents, exhaust/electrical connections and instrument observation. This is qualified-technician work.
- Battery condition/electrolyte, pages 10 and 75: 500 running hours; high ambient conditions may require more frequent checks, example 200 running hours. Section 8.1.2 also mentions three months under stated fluid conditions; preserve context rather than presenting one universal interval.
- Storage page 33: battery refreshing charge every 12 weeks, 8 weeks in tropical climate; contact dealer for storage beyond one year. DEF time/temperature storage table has 36, 18, 12 and 6 months at 10, 25, 30 and 35°C respectively.
- Page 67: weekly separator-bowl drain for the named Perkins engines/configuration.
- Page 70: weekly rubber-part inspection and daily air intake/cleaner inspection, more often in snow, in cold-weather guidance.
- Engine-specific oil/filter/valve schedules, capacities and overhaul intervals are deferred to other manuals/dealer.

## Fault/alarm and diagnostic coverage

Two PowerWizard tables (pages 45 and 52) each contain 10 fault/symptom/remedy rows. They cover no crank, low oil pressure, high coolant temperature, overspeed, under-/over-voltage, no load, failure to stop manually/automatically, and not-in-auto warnings. Many remedies end at dealer referral. DeepSea pages 55–56 contain 17 image-based rows including shared symptom cells, CAN DATA FAIL and CAN ECU WARNING / SHUTDOWN. A source-hash-bound visual transcription preserves these rows in `data/raw/source_review.json`. These are baseline checks, not full electrical troubleshooting trees. FG100 explains warnings, load dumps and shutdown alarms, but supplies no comprehensive code dictionary.

SPN/FMI are mentioned as event-log fields on pages 42 and 49; numerical SPN/FMI meanings, diagnostic fault-code catalogs, pin-by-pin measurements, repair specifications and comprehensive service diagnostic procedures are not supplied. Numeric list items and warning category 3 must never be treated as fault-code definitions.

## Source defects and missing documents

Several internal references do not resolve correctly: 6.1.1 points to 5.3.10; fuel-fill location references and battery section 9.1 references are inconsistent. Priming text refers to repeat-prime troubleshooting not supplied as a complete procedure. The printed oil chemical-limit text on page 70 is retained without correction and quarantined pending dealer clarification. Some critical-failure table content is generic (including hydraulic oil) and cannot establish a fitted component. Example rating-plate values are not actual set specifications.

Required for deeper service: exact model/serial-specific set technical manual and wiring diagrams; engine operator/service/diagnostic and parts manuals for the installed engine and emissions system; matching PowerWizard/DeepSea/FG100 service/configuration references and fault/SPN/FMI catalogs; installed alternator/AVR manuals; CTI/ATI transfer-panel guide; service bulletins/current revisions; model ratings and approved consumable/torque/capacity data. Only explicitly approved FG Wilson sources may be authoritative; referenced component brands in this manual do not authorize unrelated manufacturer corpora.
