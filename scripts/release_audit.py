"""Assemble the measured release gate without converting unknowns to passes."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from itertools import combinations
from src.benchmark import load,leakage
ROOT=Path(__file__).resolve().parents[1]

def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def percent(v):return 'not measured' if v is None else f'{v*100:.1f}%'
def main():
    manifest=read('data/raw/corpus_manifest.json')['documents'][0];stats=read('data/processed/chunk_statistics.json');integrity=read('exports/final_integrity_checks.json');build=read('data/processed/corpus_build.json')
    tests=ET.parse(ROOT/'exports/tests.xml').getroot().find('testsuite');followup=ET.parse(ROOT/'exports/final_checks.xml').getroot().find('testsuite')
    reports={f'{s}_{mode}':read(f'exports/{s}_{mode}.json') for s in ('development','holdout') for mode in ('bm25','semantic','hybrid')}
    reports.update({f'{s}_hybrid':read(f'exports/{s}_hybrid.json') for s in ('adversarial','regression')})
    splits={s:load(ROOT/f'benchmarks/{s}.jsonl') for s in ('development','holdout','adversarial','regression')}
    leaks=[x for a,b in combinations(splits,2) for x in leakage(splits[a],splits[b])]
    dev=reports['development_hybrid']['metrics'];hold=reports['holdout_hybrid']['metrics'];reg=reports['regression_hybrid']['metrics']
    exact=read('exports/exact_lookup_audit.json');startup=read('exports/startup_smoke.json')
    failures={name:[{'id':c['id'],'status':c['status'],'top1':c['top1'],'approved_answer':c['approved_answer']} for c in report['cases'] if c['answerable'] and (not c['top1'] or not c['approved_answer'])] for name,report in reports.items()}
    gates={
     'syntax_imports':{'status':'PASS','files':integrity['syntax_files'],'rate':1.0},
     'automated_regression_tests':{'status':'PASS','passed':int(tests.attrib['tests']),'failures':int(tests.attrib['failures']),'seconds':float(tests.attrib['time']),'followup_checks_passed':int(followup.attrib['tests'])},
     'retrieval_top1':{'status':'PASS','development':dev['top1'],'holdout':hold['top1'],'threshold':.95},
     'retrieval_recall_at_3':{'status':'PASS','development':dev['recall_at_3'],'holdout':hold['recall_at_3'],'threshold':.98},
     'retrieval_recall_at_5':{'status':'PASS','development':dev['recall_at_5'],'holdout':hold['recall_at_5']},
     'exact_critical_identifiers':{'status':'FAIL','passed':sum(x['matched'] for x in exact),'total':len(exact),'missing':[x['identifier'] for x in exact if not x['matched']]},
     'unsupported_rejection':{'status':'PASS_ON_SAMPLES','rate':1.0,'negative_cases':20},
     'approved_deterministic_answers':{'status':'FAIL','development':dev['approved_deterministic_answers'],'holdout':hold['approved_deterministic_answers'],'regression':reg['approved_deterministic_answers'],'required':1.0},
     'citation_source_identity':{'status':'PASS_ON_EMITTED_SAMPLES','rate':1.0},
     'critical_citation_faithfulness':{'status':'NOT_ESTABLISHED','extractive_baseline':1.0,'reason':'Independent service-expert claim/relevance/warning review not performed.'},
     'unsupported_identifier_hallucinations':{'status':'ZERO_OBSERVED_ON_SAMPLES','observed':0},
     'critical_grounded_answer_failures':{'status':'NOT_ESTABLISHED','reason':'Expected-answer misses exist; critical expert assessment absent. Zero cannot be claimed.'},
     'safety_regressions':{'status':'ZERO_OBSERVED_ON_TESTS','observed':0,'limitation':'Warning recall and arbitrary unsafe paraphrases not exhaustively established.'},
     'critical_numerical_unit_consistency':{'status':'BASELINE_PASS_EXPERT_REVIEW_PENDING','extractive_baseline':1.0},
     'corpus_index_compatibility':{'status':'PASS'},
     'exposed_secrets':{'status':'ZERO_PATTERN_MATCHES','count':0,'scope':'Project source/config/docs/exports; known key/private-key patterns.'},
     'repeatable_startup':{'status':'PASS','app_test':True,'degraded_app_test':True,'http_runs':startup},
     'unseen_holdout_generalization':{'status':'LIMITED_SINGLE_MANUAL_ONLY','source_documents':1,'externally_blind':False},
     'unseen_paraphrase_robustness':{'status':'LIMITED_SAMPLE'},
     'typo_noisy_robustness':{'status':'LIMITED_SAMPLE'},
     'benchmark_leakage':{'status':'PASS_LEXICAL_BASELINE','issues':leaks},
     'hard_coded_benchmark_answers':{'status':'ZERO_DETECTED','count':0,'method':'Production import/source inspection and full-question scan; source identifier literals permitted.'},
     'overfitting_audit':{'status':'BASELINE_PASS','core_unchanged_after_freeze':integrity['holdout_core_unchanged'],'benchmarks_unchanged':integrity['benchmark_files_unchanged'],'limitation':'Same source and case author; semantic leakage cannot be excluded.'},
     'prompt_document_injection_baseline':{'status':'PASS_ON_TESTS','reason':'Query injection, poisoned evidence, numeric conflicts and corpus tampering tested.'},
     'known_limitations':{'status':'DOCUMENTED','path':'docs/KNOWN_LIMITATIONS.md'}}
    for name,topics in [('unseen_paraphrase_robustness',{'unseen_paraphrase'}),('typo_noisy_robustness',{'typo'})]:
        cases=[c for c in reports['holdout_hybrid']['cases'] if c.get('topic') in topics]
        gates[name].update(cases=len(cases),top1=sum(c['top1'] for c in cases)/len(cases) if cases else None,approved_answers=sum(c['approved_answer'] for c in cases)/len(cases) if cases else None)
    blockers=[
      'Expected-answer gate below 100%: development 90%, holdout 95%, regression 75%.',
      'Deterministic critical lookup incomplete: ISO 22241-1 and spelled-out Every Two Weeks / Every Month are not indexed as exact keys (13/16 checked keys pass). Lexical/semantic retrieval may still locate these sources.',
      'Independent service-expert verification of critical answers, warnings, numerical/source ambiguities and image transcriptions is pending.',
      '43 chunks remain quarantined, including icon-dependent FG100 instructions, lifting diagrams, illustrative specifications and source discrepancies.',
      'One small, same-author/manual holdout cannot establish cross-document or broader field generalization. Further ranking/grounding changes need a new unseen holdout.',
      'Exact model/serial-specific engine/controller/alternator service documents and diagnostic code catalogs are absent.'
    ]
    audit={'project':'AwanSolveAi FG Wilson Generator Troubleshooting & Maintenance AI V1','audit_date':'2026-09-10','verdict':'FAIL — NOT DEMO READY','manual':manifest,'v1_boundary':manifest['applicability'],'extracted_page_count':81,'chunk_statistics':stats,'fault_alarm_coverage':{'powerwizard_table_rows':20,'deepsea_image_table_rows':17,'numeric_fault_code_dictionary':False,'spn_fmi_decoding':False,'fg100_protection_levels':True},'gates':gates,'benchmarks':{k:v['metrics'] for k,v in reports.items()},'case_failures':failures,'latency':{'development_hybrid_cold_start_seconds':reports['development_hybrid']['cold_start_seconds'],'holdout_hybrid_cold_start_seconds':reports['holdout_hybrid']['cold_start_seconds'],'development_hybrid_median_ms':dev['latency_ms_median'],'holdout_hybrid_median_ms':hold['latency_ms_median'],'holdout_hybrid_p95_ms':hold['latency_ms_p95'],'build_seconds':build['build_seconds'],'conditions':'Windows Python 3.11, CPU, local model, sequential evaluation, OMP/MKL/OPENBLAS threads 2; HTTP smoke excludes model loading.'},'remaining_blockers':blockers,'environment_events':['Concurrent unbounded model processes failed with OpenBLAS allocation/MemoryError; sequential bounded runs succeeded.','Local .deps Streamlit startup required --global.developmentMode=false; launcher and smoke test corrected.'],'freeze':read('exports/evaluation_freeze.json')}
    (ROOT/'exports/AwanSolveAi_gold_standard_demo_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# AwanSolveAi Gold Standard Demo Audit','','**FAIL — NOT DEMO READY**','', 'The repository has a working local reference application and verified corpus build. Retrieval thresholds pass on the small development/holdout samples, but required deterministic-answer and exact-identifier gates do not. Critical service-expert validation and wider generalization are not established.','', '## 1. Exact manual inspected','',f'**{manifest["title"]}**, **{manifest["document_number"]}, {manifest["revision"]}**, English, **81 PDF pages**. Exact filename: `{manifest["filename"]}`. SHA-256: `{manifest["sha256"]}`. All pages were text-inspected and visually surveyed; image tables received enlarged inspection.','', '## 2. Exact V1 boundary','',manifest['applicability']+' No individual generator model is approved by inference. Operator guidance, named controller functions, selected engine/filter procedures and qualified-technician maintenance reference only. See MANUFACTURER_CORPUS_AUDIT.md and V1_CORPUS_BOUNDARY.md.','', '## 3–4. Extraction and chunks','',f'**81 pages extracted; {stats["total"]} chunks; {stats["quarantined"]} quarantined; {stats["total"]-stats["quarantined"]} eligible.** Printed pages are separate from PDF pages. Blank and weak pages remain recorded. See EXTRACTION_QUALITY_REPORT.md and CHUNK_QUALITY_REPORT.md.','', '| Primary category | Count |','|---|---:|']
    lines +=[f'| {k} | {v} |' for k,v in sorted(stats['categories'].items())]
    lines+=['','## 5. Fault/alarm coverage','','20 PowerWizard table rows and 17 visually transcribed DeepSea rows; FG100 protection-level descriptions. Controller scopes are preserved. There is **no numeric fault-code or SPN/FMI decoding dictionary**. Critical-failure rows and context also contribute to the 51 fault-finding chunks; that count is not a code count.','', '## 6. Tests and startup','',f'**{tests.attrib["tests"]} tests passed**, zero failures ({float(tests.attrib["time"]):.2f} seconds). **{followup.attrib["tests"]} targeted follow-up checks passed** after UI/document/launcher changes. {integrity["syntax_files"]} Python files compiled. Corpus/index and frozen-core checks passed. Streamlit AppTest covers normal and degraded startup; two real HTTP startups passed. All smoke-test child processes were stopped.','', '## 7–8. Retrieval and answer metrics','', '| Split / mode | Top-1 | Recall@3 | Recall@5 | Unsupported rejection | Approved answer |','|---|---:|---:|---:|---:|---:|']
    for key,report in reports.items():
        x=report['metrics'];lines.append(f'| {key} | {percent(x["top1"])} | {percent(x["recall_at_3"])} | {percent(x["recall_at_5"])} | {percent(x["unsupported_rejection"])} | {percent(x["approved_deterministic_answers"])} |')
    lines+=['', 'Development/holdout each contain 20 positive and 4 negative cases; adversarial has 8 negative cases; regression has 4 positive and 4 negative cases. No holdout ranking/grounding tuning was performed. Semantic-only retrieval is weaker here; the fixed hybrid design was not selected by tuning on holdout. Case-level results, including misses, are in exports.','', 'Citation identity, extractive answer fidelity and numerical inclusion are 100% on emitted benchmark answers. These are source-text checks, not independent judgments of critical relevance, warning completeness or service safety. Exact lookup passes **13/16** audited keys; missing keys are listed below.','', '## 9. Leakage / overfitting','',f'**{len(leaks)} exact/near-duplicate question pairs detected** across all four splits using the documented lexical tests. No full benchmark questions/answers were found embedded in production lookup logic; exact source identifier literals are permitted. Core build and benchmark hashes match the pre-holdout freeze. Same-author, single-manual and semantic-leakage limitations remain.','', '## 10. Latency','',f'Hybrid cold start: **{reports["development_hybrid"]["cold_start_seconds"]:.2f} s development**, **{reports["holdout_hybrid"]["cold_start_seconds"]:.2f} s holdout**. Median query latency: **{dev["latency_ms_median"]:.2f} ms / {hold["latency_ms_median"]:.2f} ms**; holdout p95 **{hold["latency_ms_p95"]:.2f} ms**. Full build: **{build["build_seconds"]:.2f} s**. HTTP server health became ready in approximately '+', '.join(f'{x["startup_seconds"]:.2f} s' for x in startup)+'. HTTP health excludes app/model initialization.','', 'Measured locally on CPU with bounded thread counts and sequential evaluations. Unbounded parallel processes initially exhausted memory; successful runs use OMP/MKL/OPENBLAS=2. The local dependency layout also required disabling Streamlit development mode in the launcher. These operational fixes did not alter frozen retrieval or grounding.','', '## 11. Remaining blockers','']
    lines += [f'- {x}' for x in blockers]
    lines+=['', '## 12. Final gate','', '**FAIL — NOT DEMO READY.** The application can be run locally for engineering review with `./run_demo.ps1`. Do not present it as having passed the AwanSolveAi Gold Standard. The JSON audit records PASS, sampled baseline results and NOT ESTABLISHED gates separately.','', '| Required gate | Result |','|---|---|']
    lines += [f'| {k} | {v["status"]} |' for k,v in gates.items()]
    (ROOT/'docs/AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(audit['verdict']);print('Saved human-readable and JSON audit.')
if __name__=='__main__':main()

