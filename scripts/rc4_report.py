"""Bind completed non-holdout diagnostics to an RC4 development freeze.

Never evaluates a holdout or authorizes release. Requires completed production
split reports, full pytest XML and two tagged HTTP startup results.
"""
from pathlib import Path
from datetime import datetime, timezone
from itertools import combinations
import hashlib
import json
import os
import platform
import sys
import zipfile
import xml.etree.ElementTree as ET
from src.store import validate_build, code_fingerprint
from src.retrieval import HybridRetriever
from src.benchmark import load, leakage
from src.answer_evaluation import summarize, schema_errors

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (ROOT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def main():
    manifest,build,chunks=validate_build(ROOT)
    byid={c.chunk_id:c for c in chunks}
    names=('development','regression','adversarial')
    reports={s:read(f'exports/gold_standard_answer_results_rc4_{s}.json') for s in names}
    for report in reports.values():
        assert report['production_code_fingerprint']==code_fingerprint(ROOT)
        assert report['files_unchanged_during_evaluation']
        assert all(sha(ROOT/p)==h for p,h in report['hashes'].items())
    rows=[c for r in reports.values() for c in r['cases']]
    summary=summarize(rows)
    splits={s:load(ROOT/f'benchmarks/{s}.jsonl') for s in (*names,'holdout')}
    errors=[{'id':c.get('id'),'errors':e} for cases in splits.values() for c in cases if (e:=schema_errors(c,byid))]
    leaks=[x for a,b in combinations(splits.values(),2) for x in leakage(a,b)]
    production='\n'.join(p.read_text(encoding='utf-8-sig').casefold() for d in ('src','app') for p in (ROOT/d).glob('*.py'))
    literals=[]
    historical=load(ROOT/'benchmarks/holdout_rc3.jsonl')
    for c in [c for v in splits.values() for c in v]+historical:
        for kind,value in [('query',c['query']),('id',c['id']),('answer',c.get('expected_quote',''))]+[('chunk_id',i) for i in c['expected_chunk_ids']]:
            if value and value.casefold() in production:literals.append({'id':c['id'],'kind':kind})
    old={c['id']:c for c in historical}
    promoted=[c for c in splits['regression'] if c.get('provenance')=='exposed_holdout_failure_rc3']
    unchanged=all({k:v for k,v in c.items() if k not in ('original_split','provenance','metadata')}=={k:v for k,v in old[c['id']].items() if k not in ('original_split','provenance','metadata')} for c in promoted)
    assert len(promoted)==5 and unchanged
    tests=ET.parse(ROOT/'exports/rc4_tests.xml').getroot().find('testsuite').attrib
    startups=read('exports/startup_smoke_rc4.json')
    compiled=[]
    for d in ('src','app','tests','scripts','benchmarks'):
        for p in (ROOT/d).glob('*.py'):
            compile(p.read_text(encoding='utf-8-sig'),str(p),'exec');compiled.append(str(p.relative_to(ROOT)))
    retriever=HybridRetriever(chunks)
    exact=[]
    for previous in read('exports/rc3_exact_lookup.json'):
        hits=retriever.exact_lookup(previous['identifier'])
        exact.append({'identifier':previous['identifier'],'matched':bool(hits),'all_eligible':all(not h.chunk.review_required for h in hits)})
    write('exports/rc4_exact_lookup.json',exact)
    bm=retriever.bm25
    write('exports/rc4_bm25_index.json',{'algorithm':'rank_bm25.BM25Okapi','chunk_ids':[chunks[i].chunk_id for i in retriever.active], 'doc_freqs':bm.doc_freqs,'doc_len':bm.doc_len,'idf':bm.idf,'avgdl':bm.avgdl,'k1':bm.k1,'b':bm.b,'epsilon':bm.epsilon,'vocabulary':retriever.vocab})
    old_freeze=read('exports/evaluation_freeze_rc3.json')
    with zipfile.ZipFile(ROOT/'exports/rc3_frozen_state_before_rc4.zip') as z:
        assert all(hashlib.sha256(z.read(p.replace('\\','/'))).hexdigest()==h for p,h in old_freeze['files'].items())
    assert sha(ROOT/'exports/evaluation_freeze_rc3.json')==(ROOT/'exports/evaluation_freeze_rc3.sha256').read_text().strip()
    assert sha(ROOT/'benchmarks/holdout_rc3.jsonl')==old_freeze['files']['benchmarks\\holdout_rc3.jsonl']
    gates={'compilation':True,'tests':int(tests['failures'])==0 and int(tests['errors'])==0,
           'development':reports['development']['summary']['failed']==0,
           'regression':reports['regression']['summary']['failed']==0,
           'adversarial':reports['adversarial']['summary']['failed']==0,
           'exact_identifiers':all(x['matched'] and x['all_eligible'] for x in exact),
           'schema':not errors,'leakage':not leaks,'production_literals':not literals,
           'two_streamlit_startups':len(startups)==2 and all(x['http_health'] for x in startups)}
    for key in ('unsupported_rejection','citation_document','citation_page_chunk','evidence_support','safety','qualifiers','negations','warnings','escalation','values','units'):
        gates[key]=summary['failures_by_check'].get(key,0)==0
    integrity={'schema_errors':errors,'leakage':leaks,'production_literals':literals,'promoted_assertions_unchanged':unchanged,'rc3_archive_verified':True,'rc3_holdout_bytes_unchanged':True,'compilation_files':compiled}
    write('exports/rc4_integrity.json',integrity)
    stamp=datetime.now(timezone.utc).isoformat()
    paths=[]
    for d in ('src','app','tests','scripts','benchmarks'):
        paths.extend(p for p in (ROOT/d).glob('*') if p.suffix in ('.py','.jsonl'))
    paths.extend(ROOT/p for p in ('data/raw/corpus_manifest.json','data/raw/source_review.json','data/processed/corpus_build.json','requirements-lock.txt','pyproject.toml','run_demo.ps1','exports/rc4_tests.xml','exports/startup_smoke_rc4.json','exports/rc4_integrity.json','exports/rc4_exact_lookup.json','exports/rc4_bm25_index.json'))
    paths.extend((ROOT/'data/processed'/p) for p in build['artifacts'])
    paths.extend((ROOT/'data/raw/manuals').glob('*.pdf'))
    paths.extend(ROOT/f'exports/gold_standard_answer_results_rc4_{s}.json' for s in names)
    commands=['python -m compileall -q src app tests scripts benchmarks','python -B -m pytest -q -p no:cacheprovider --junitxml=exports/rc4_tests.xml']+[reports[s]['command'] for s in names]+['python scripts/smoke_startup.py --report-tag rc4','python scripts/rc4_report.py']
    freeze={'release':'RC4','kind':'development diagnostic freeze; no new release or holdout evaluation','created_at':stamp,'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},'code_fingerprint':code_fingerprint(ROOT),'model_fingerprint':build['model_fingerprint'],'source_sha256':manifest['documents'][0]['sha256'],'commands':commands,'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'thread_limits':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')},'gates':gates,'independent_holdout':'NOT SATISFIED','technician_validation':'PENDING'}
    frozen=ROOT/'exports/evaluation_freeze_rc4.json'
    with frozen.open('x',encoding='utf-8') as f:json.dump(freeze,f,indent=2,ensure_ascii=False)
    (ROOT/'exports/evaluation_freeze_rc4.sha256').write_text(sha(frozen)+'\n',encoding='utf-8')
    blockers=['Independent holdout construction is NOT SATISFIED; no RC4 holdout was created or evaluated.','Independent qualified FG Wilson technician validation remains pending.','Broad critical-failure questions lack a reviewed multi-row/clarification answer contract.','Sound-level table header, applicability and measurement-context recovery remains unfinished; anonymous table answers now require review.']
    if not all(gates.values()):blockers.insert(0,'One or more mandatory diagnostic gates failed.')
    result={'release':'RC4','evaluation_kind':'production-pipeline development diagnostics, not unseen release evaluation','completed_at':stamp,'verdict':'FAIL â€” NOT DEMO READY','summary':summary,'splits':{s:r['summary'] for s,r in reports.items()},'tests':tests,'startup':startups,'gates':gates,'supported_exact_identifiers':{'passed':sum(x['matched'] and x['all_eligible'] for x in exact),'total':len(exact)},'integrity':integrity,'freeze_sha256':sha(frozen),'remaining_blockers':blockers,'holdout':{'evaluated':False,'historical_rc3_passed':25,'historical_rc3_total':32,'historical_rc3_positive_accuracy':17/24},'cases':rows}
    write('exports/gold_standard_answer_results_rc4.json',result)
    lines=['# RC4 remediation report','','FAIL â€” NOT DEMO READY','','Current-state verification initially found only RC4 intake files. All 50 RC3 frozen files and corpus/model compatibility verified. In-memory compilation and 154 tests passed; read-only production baselines reproduced 35/35 development, 10/10 regression and 8/8 adversarial. No Git repository was present. The only stated corpus-count discrepancy was 215 rather than 205 chunks (ten previously reviewed recoveries).','','## Implemented changes','','General retrieval normalization adds show, advise and observed to the bounded stop list. A leading directive plus guidance/instructions/precautions plus for/about/concerning is removed only from query terms; document terms remain unchanged. Unknown technical terms, negation, quantities and conditions remain. Subject ranking uses Fault cells for troubleshooting rows and rewards focused titles only when existing 0.55 evidence coverage is met. Answering refuses anonymous/incomplete table cells. An explicitly annotated warning can satisfy a required warning in the warning field; citation and claim checks still apply. No answer quotation route, benchmark-ID rule, chunk-ID rule, weaker refusal threshold or LLM judge was introduced.','','Five source-verified exposed cases were promoted with unchanged technical expectations. Two new source-defined development cases exercise oils safety and a different PowerWizard fault row. Two ambiguous table-row annotations remain diagnostics and are not counted as repaired. Full forensics and corpus decisions are in RC4_FAILURE_FORENSICS.md and RC4_CORPUS_COVERAGE_DECISION.md.','','## Completed production diagnostics','','| Split | Passed / total | Positive accuracy |','|---|---:|---:|']
    for s,r in reports.items():
        m=r['summary'];a=m['deterministic_answer_accuracy'];lines.append(f"| {s} | {m['passed']}/{m['cases']} | {'N/A' if a is None else f'{a:.2%}'} |")
    lines+=['',f"Tests: {tests['tests']} passed with {tests['failures']} failures and {tests['errors']} errors. Exact identifiers: {result['supported_exact_identifiers']['passed']}/{len(exact)}. Two Streamlit HTTP startups: {gates['two_streamlit_startups']}.",'','```json',json.dumps(summary,indent=2),'```','','These are real production retrieval and answering runs, not mocked verdicts. Latencies include retrieval/answering, exclude model cold start, and use nearest-rank p95. No RC3 holdout was rerun. Historical 25/32 and 17/24 positive accuracy remain historical, not RC4 accuracy. Diagnostic success does not satisfy independence or technician validation.','','## Gates','','```json',json.dumps(gates,indent=2),'```','','No new release evaluation is authorized by this development freeze. Corpus remains 81 pages, 215 chunks, 43 quarantined. Original RC2/RC3 reports and freezes remain; all 50 RC3 inputs are recoverable and hash-verified in rc3_frozen_state_before_rc4.zip. Current code intentionally differs from RC3. Original holdout bytes are unchanged. Intermediate RC4 diagnostic attempts are retained.','','## Remaining blockers','']+['- '+x for x in blockers]+['','## Commands','','Set PYTHONPATH=.deps;., PYTHONIOENCODING=utf-8, and OMP_NUM_THREADS/MKL_NUM_THREADS/OPENBLAS_NUM_THREADS=2.','','```powershell']+commands+['```','','Complete replacement files: exports/rc4_replacement_files.zip. Machine-readable results and immutable development freeze: exports/gold_standard_answer_results_rc4.json and exports/evaluation_freeze_rc4.json.','']
    report='\n'.join(lines)
    (ROOT/'docs/RC4_REMEDIATION_REPORT.md').write_text(report,encoding='utf-8')
    (ROOT/'docs/AwanSolveAi_GOLD_STANDARD_DEMO_AUDIT.md').write_text(report,encoding='utf-8')
    write('exports/AwanSolveAi_gold_standard_demo_audit.json',{k:v for k,v in result.items() if k!='cases'})
    with (ROOT/'docs/KNOWN_LIMITATIONS.md').open('a',encoding='utf-8') as f:
        f.write('\n\n## RC4 current status\n\nEarlier sections are historical. RC4 remains FAIL â€” NOT DEMO READY. See RC4_REMEDIATION_REPORT.md for current measured diagnostics. Five exposed source-supported cases are now regressions, not independent tests. Anonymous table cells are refused pending header/context recovery. Broad table topics still need a reviewed completeness/clarification contract. Independent holdout authorship and technician validation remain pending.\n')
    with zipfile.ZipFile(ROOT/'exports/rc4_replacement_files.zip','x',zipfile.ZIP_DEFLATED) as z:
        for d in ('src','app','tests','scripts','benchmarks','docs'):
            for p in (ROOT/d).glob('*'):
                if p.suffix in ('.py','.jsonl','.md'):z.write(p,str(p.relative_to(ROOT)))
        for p in (ROOT/'exports').glob('*rc4*'):
            if p.suffix in ('.json','.sha256','.xml'):z.write(p,str(p.relative_to(ROOT)))
    print(json.dumps({'verdict':result['verdict'],'summary':summary,'gates':gates},indent=2))


if __name__=='__main__':
    main()

