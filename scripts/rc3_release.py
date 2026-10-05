"""RC3 preflight, immutable freeze, one-shot sealed evaluation and evidence report."""
import hashlib,json,sys,platform,os,shutil,zipfile,py_compile
from pathlib import Path
from datetime import datetime,timezone
from itertools import combinations
from importlib import metadata
from collections import Counter
import xml.etree.ElementTree as ET
from src.store import validate_build,code_fingerprint
from src.retrieval import HybridRetriever
from src.benchmark import load,leakage
from src.answer_evaluation import schema_errors,summarize,run
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):
    (ROOT/p).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()

def prepare():
    manifest,build,chunks=validate_build(ROOT);byid={c.chunk_id:c for c in chunks}
    names=('development','regression','adversarial','holdout','holdout_rc3')
    splits={s:load(ROOT/f'benchmarks/{s}.jsonl') for s in names}
    errors=[{'id':c.get('id'),'errors':e} for rows in splits.values() for c in rows if (e:=schema_errors(c,byid))]
    leaks=[x for a,b in combinations(splits.values(),2) for x in leakage(a,b)]
    production='\n'.join(p.read_text(encoding='utf-8-sig').casefold() for directory in ('src','app') for p in (ROOT/directory).glob('*.py'))
    literals=[]
    for rows in splits.values():
        for c in rows:
            for kind,value in [('query',c['query']),('id',c['id']),('answer',c.get('expected_quote',''))]+[('chunk_id',x) for x in c['expected_chunk_ids']]:
                if value and value.casefold() in production:literals.append({'id':c['id'],'kind':kind})
    original={c['id']:c for s in ('development','regression','adversarial','holdout') for c in load(ROOT/f'exports/historical_pre_rc3/benchmarks/{s}.jsonl')}
    current={c['id']:c for rows in splits.values() for c in rows}
    preserved=all(all(c[k]==current[i][k] for k in ('query','answerable','expected_chunk_ids')) and c.get('expected_quote')==current[i].get('expected_quote') for i,c in original.items())
    compiled=[]
    for directory in ('src','app','tests','scripts'):
        for p in (ROOT/directory).glob('*.py'):py_compile.compile(str(p),doraise=True);compiled.append(str(p.relative_to(ROOT)))
    retriever=HybridRetriever(chunks)
    keys=read('exports/rc2_exact_lookup.json')
    exact=[{'identifier':k['identifier'],'matched':bool(retriever.exact_lookup(k['identifier'])),'all_eligible':all(not h.chunk.review_required for h in retriever.exact_lookup(k['identifier']))} for k in keys]
    write('exports/rc3_exact_lookup.json',exact)
    bm=retriever.bm25
    write('exports/rc3_bm25_index.json',{'description':'Serializable snapshot of actual in-memory BM25 state; runtime constructs this from chunks','chunk_ids':[chunks[i].chunk_id for i in retriever.active],'doc_freqs':bm.doc_freqs,'doc_len':bm.doc_len,'idf':bm.idf,'avgdl':bm.avgdl,'k1':bm.k1,'b':bm.b,'epsilon':bm.epsilon,'vocabulary':retriever.vocab,'code_fingerprint':code_fingerprint(ROOT),'chunks_sha256':sha(ROOT/'data/processed/chunks.json')})
    fields=['required_assertions','prohibited_assertions','required_identifiers','required_values','required_units','required_qualifiers','required_negations','required_warnings','required_escalation','expected_source_document','expected_pages','expected_chunk_ids','expected_route']
    coverage={field:sum(bool(current[i].get(field)) for i in original) for field in fields}
    result={'timestamp':now(),'schema_errors':errors,'leakage':leaks,'production_literals':literals,'original_64_queries_expectations_preserved':preserved,'corpus_index_compatible':True,'syntax_files':compiled,'original_64_field_coverage':coverage,'source_sha256':manifest['documents'][0]['sha256'],'holdout_creation':read('exports/rc3_holdout_provenance.json'),'historical_failed_results_unchanged':sha(ROOT/'exports/gold_standard_answer_results.json')==sha(ROOT/'exports/historical_pre_rc3/gold_standard_answer_results.json')}
    write('exports/rc3_integrity.json',result)
    print('Preflight:',len(errors),'schema errors;',len(leaks),'leaks;',len(literals),'production literals; original expectations preserved:',preserved)
    if errors or leaks or literals or not preserved:raise SystemExit(1)

def verify():
    path=ROOT/'exports/evaluation_freeze_rc3.json';f=read('exports/evaluation_freeze_rc3.json')
    assert sha(path)==(ROOT/'exports/evaluation_freeze_rc3.sha256').read_text().strip(),'Freeze content changed'
    changed=[p for p,h in f['files'].items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
    assert not changed,'Frozen files changed: '+str(changed)
    validate_build(ROOT)
    return f

def freeze():
    prepare();historical=ROOT/'exports/evaluation_freeze_rc1_historical.json'
    if not historical.exists():shutil.copy2(ROOT/'exports/evaluation_freeze.json',historical)
    paths=[]
    for directory in ('src','app','tests','scripts'):paths+=list((ROOT/directory).glob('*.py'))
    paths+=list((ROOT/'benchmarks').glob('*.jsonl'))
    paths += [ROOT/p for p in ('data/raw/corpus_manifest.json','data/raw/source_review.json','data/processed/corpus_build.json','exports/rc3_bm25_index.json','requirements-lock.txt','pyproject.toml','run_demo.ps1')]
    build=read('data/processed/corpus_build.json');paths += [ROOT/'data/processed'/p for p in build['artifacts']]
    paths+=list((ROOT/'data/raw/manuals').glob('*.pdf'))
    commands=['python -m compileall -q src app tests scripts','python -m pytest -q --junitxml=exports/rc3_final_tests.xml']+[f'python -m src.benchmark --split {s} --mode hybrid --live-answers --report-tag rc3_{s}' for s in ('development','regression','adversarial')]+['python scripts/rc3_release.py holdout','python scripts/smoke_startup.py','python -m pytest -q tests/test_benchmarks.py::test_secret_scan','python scripts/rc3_release.py verify']
    result={'created_at':now(),'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},'code_fingerprint':code_fingerprint(ROOT),'model_fingerprint':build['model_fingerprint'],'source_sha256':read('data/raw/corpus_manifest.json')['documents'][0]['sha256'],'commands':commands,'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'dependencies':{d.metadata['Name']:d.version for d in metadata.distributions(path=[str(ROOT/'.deps')]) if d.metadata.get('Name')},'thread_limits':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},'holdout_provenance':read('exports/rc3_holdout_provenance.json'),'independent_generalization_gate':'NOT SATISFIED'}
    path=ROOT/'exports/evaluation_freeze_rc3.json'
    with path.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,ensure_ascii=False)
    with (ROOT/'exports/evaluation_freeze_rc3.sha256').open('x') as f:f.write(sha(path)+'\n')
    verify();print('Immutable RC3 freeze created and immediately verified.')

def holdout():
    verify()
    with (ROOT/'exports/rc3_holdout_attempt.json').open('x',encoding='utf-8') as f:json.dump({'started_at':now(),'attempts':1,'freeze_sha256':sha(ROOT/'exports/evaluation_freeze_rc3.json')},f)
    status=run(ROOT,'holdout_rc3','hybrid',30.,'rc3_holdout')
    verify();print('Single sealed evaluation finished; freeze verified; no tuning or rerun permitted.')
    return status

def report():
    freeze_data=verify();reports={s:read(f'exports/gold_standard_answer_results_rc3_{s}.json') for s in ('development','regression','adversarial','holdout')}
    rows=[c for r in reports.values() for c in r['cases']];summary=summarize(rows)
    tests=ET.parse(ROOT/'exports/rc3_final_tests.xml').getroot().find('testsuite').attrib
    startup=read('exports/startup_smoke.json');integrity=read('exports/rc3_integrity.json');exact=read('exports/rc3_exact_lookup.json')
    hs=reports['holdout']['cases'];positive=[c for c in hs if c['answerable']]
    retrieval={k:sum(c[k] for c in positive)/len(positive) if positive else None for k in ('top1','recall_at_3','recall_at_5')}
    verdict='FAIL â€” NOT DEMO READY'
    result={'release':'RC3','completed_at':now(),'verdict':verdict,'summary':summary,'splits':{s:r.get('summary',{}) for s,r in reports.items()},'holdout_retrieval':retrieval,'tests':tests,'startup':startup,'supported_exact_identifiers':{'passed':sum(c['matched'] and c['all_eligible'] for c in exact),'total':len(exact)},'integrity':integrity,'freeze_verified':True,'freeze_sha256':sha(ROOT/'exports/evaluation_freeze_rc3.json'),'generalization_gate':'NOT SATISFIED','independent_technician_validation':'PENDING','cold_start_seconds':{s:r.get('cold_start_seconds') for s,r in reports.items()},'cases':rows,'remaining_blockers':['Independent construction of a new holdout is not demonstrated; same-assistant source-only construction is explicitly insufficient.','Independent FG Wilson service-technician verification remains pending.']+(['One-time sealed RC3 live evaluation contains failures; no tuning or second unseen evaluation was performed.'] if summary['failed'] else [])}
    write('exports/gold_standard_answer_results_rc3.json',result)
    write('exports/AwanSolveAi_gold_standard_demo_audit.json',{k:v for k,v in result.items() if k!='cases'})
    lines=['# RC3 remediation report','',verdict,'','## Root cause and general correction','','Ordinary query words matched controller UI identifiers, causing +0.04 exact-match contributions without controller context. Controller-specific descriptions displaced applicable general evidence and correctly triggered applicability refusal. Exact-match contributions now require explicit controller context for scoped chunks. Direct exact lookup and all grounding/refusal thresholds remain unchanged. No answer-generation change was needed.','','Three new development questions reproduced this defect on different manufacturer passages before the change. All original queries, quotations and expected chunk IDs were retained. The two exposed cases moved from holdout to regression with exposed_holdout_failure_rc2 provenance; archived failed results remain unchanged.','','A separate annotation defect was corrected: invert only the first complete manufacturer prohibition sentence, and distinguish a safe negative from its prohibited affirmative clause. This does not remove substantive source warnings. Eleven new development cases exercise routing, active-event reset negation, pressure/PPE conditions and unsupported code, SPN/FMI, interval, controller, bypass and internal-repair requests through production.','','## Final measured results','',f"Tests: {tests['tests']}; failures {tests['failures']}; errors {tests['errors']}. Live cases: {summary['passed']}/{summary['cases']} passed. Positive deterministic answer accuracy: {summary['deterministic_answer_accuracy']:.2%}.",'','| Split | Passed / total | Positive accuracy |','|---|---:|---:|']
    for s,r in reports.items():
        m=r['summary'];lines.append(f"| {s} | {m['passed']}/{m['cases']} | {m['deterministic_answer_accuracy']} |")
    lines+=['',f'RC3 holdout retrieval: {retrieval}.',f"Supported exact identifiers: {result['supported_exact_identifiers']}. Two clean Streamlit startups: {all(s['http_health'] for s in startup)}.",'','```json',json.dumps(summary,indent=2),'```','','Failure categories overlap; a refusal may cause missing warning/qualifier requirements without emitting unsafe instructions. Zero failures with zero applicable fields do not certify coverage.','', '## One-time holdout and independence','','The 32-case replacement was generated from source passages not used to design the remediation, with exact/paraphrase/noisy/symptom and unsupported/adversarial cases. Structured source annotations cover maintenance/procedure/safety/negation/qualifiers/warnings/escalation where present. An initial unevaluated draft lacked symptom coverage and was archived before a category-corrected draft was sealed. No RC3 results were read during implementation. The final holdout was run once after freeze. Its same-assistant construction is not genuinely independent; the generalization gate is NOT SATISFIED regardless of measured accuracy.','','## Freeze and preservation','','The new immutable evaluation_freeze_rc3.json and SHA-256 sidecar were verified immediately, before/after holdout, and at reporting. The freeze binds source code, evaluator, source PDF/manifest/review, processed chunks, actual in-memory BM25 state snapshot, FAISS artifacts, benchmark files, dependency versions, thread settings and exact commands. BM25 is reconstructed at runtime; its JSON snapshot records the real fitted state. Model fingerprint is bound to the corpus build. The stale freeze is retained as evaluation_freeze_rc1_historical.json and in the historical archive.','','Compilation, full tests, corpus compatibility, source-literal scan, cross-split leakage checks, exact lookup and citation/safety tests ran. Original 64 queries/expected quotations/IDs were verified unchanged. Archived original holdout lineage is not counted as a duplicate current split; moved cases exist only in regression.','','## Remaining blockers','']
    lines += ['- '+b for b in result['remaining_blockers']]
    lines += ['','## Commands','', '```powershell']+freeze_data['commands']+['```','','Complete replacement code and current benchmark files are packaged in exports/rc3_replacement_files.zip. Source-specific evidence and all Top-5 scores are in RC3_FAILURE_ROOT_CAUSE.md and rc3_root_cause_evidence.json. Annotation coverage is in BENCHMARK_ANNOTATION_AUDIT.md and rc3_integrity.json.','']
    text='\n'.join(lines)
    for p in ('docs/RC3_REMEDIATION_REPORT.md','docs/GOLD_STANDARD_ANSWER_EVALUATION.md','docs/AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md'):(ROOT/p).write_text(text,encoding='utf-8')
    with (ROOT/'docs/KNOWN_LIMITATIONS.md').open('a',encoding='utf-8') as f:f.write('\n\n## RC3 current status\n\nThe earlier live-answer figures above are historical. See RC3_REMEDIATION_REPORT.md for current results. Generic controller-identifier scope was corrected without changing answer thresholds. A replacement source-only sealed holdout is not independently constructed; its generalization gate is NOT SATISFIED. It was evaluated once after freeze. Independent FG Wilson technician validation remains pending.\n')
    with (ROOT/'docs/BENCHMARK_ANNOTATION_AUDIT.md').open('a',encoding='utf-8') as f:
        f.write('\n\nFinal original-64 coverage after correction:\n\n```json\n'+json.dumps(integrity['original_64_field_coverage'],indent=2)+'\n```\n\nThe four image-table expectations were visually checked against original PDF pages 55 and 56. A uniform pre-freeze annotation correction limited prohibited alternatives to the first complete source prohibition sentence; no required warnings or original quotations were relaxed.\n')
    with zipfile.ZipFile(ROOT/'exports/rc3_replacement_files.zip','w',zipfile.ZIP_DEFLATED) as z:
        for directory in ('src','app','tests','scripts','benchmarks'):
            for p in (ROOT/directory).glob('*'):
                if p.suffix in ('.py','.jsonl'):z.write(p,str(p.relative_to(ROOT)))
        for p in (ROOT/'docs').glob('*.md'):z.write(p,str(p.relative_to(ROOT)))
        for name in ('exports/gold_standard_answer_results_rc3.json','exports/evaluation_freeze_rc3.json','exports/evaluation_freeze_rc3.sha256','exports/AwanSolveAi_gold_standard_demo_audit.json'):z.write(ROOT/name,name)
    print(verdict);print(json.dumps({'summary':summary,'holdout_retrieval':retrieval,'tests':tests},indent=2))

if __name__=='__main__':
    action=sys.argv[1]
    value={'prepare':prepare,'freeze':freeze,'verify':verify,'holdout':holdout,'report':report}[action]()
    if action=='holdout':raise SystemExit(value)

