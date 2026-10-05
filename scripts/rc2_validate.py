"""Freeze RC2, then perform one sealed hybrid holdout evaluation. Never tune here."""
import hashlib,json,time,sys,py_compile
from pathlib import Path
from itertools import combinations
from datetime import datetime,timezone
from src.store import validate_build,code_fingerprint
from src.retrieval import HybridRetriever,SemanticIndex
from src.benchmark import load,evaluate,leakage

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):
    (ROOT/path).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def production():return sorted(p for folder in ('src','app') for p in (ROOT/folder).glob('*.py'))
def freeze():
    target=ROOT/'exports/rc2_freeze.json'
    if target.exists():raise SystemExit('RC2 is already frozen; refusing to overwrite.')
    _,build,_=validate_build(ROOT)
    assert digest(ROOT/'benchmarks/holdout.jsonl')==read('exports/rc2_baseline/baseline_results.json')['holdout_sha256']
    files=production()+sorted((ROOT/'tests').glob('*.py'))+[ROOT/'scripts/rc2_validate.py',ROOT/'scripts/rc2_challenges.py',ROOT/'data/raw/source_review.json',ROOT/'data/raw/corpus_manifest.json']+sorted((ROOT/'benchmarks').glob('*.jsonl'))
    write('exports/rc2_freeze.json',{'frozen_at':datetime.now(timezone.utc).isoformat(),'code_fingerprint':code_fingerprint(ROOT),'files':{str(p.relative_to(ROOT)):digest(p) for p in files},'build':build,'holdout_policy':'Baseline reproduced before modifications. No RC2 holdout labels inspected during development. One final hybrid holdout evaluation; no tuning after freeze.'})
    print('RC2 frozen; holdout labels remain unread by this command.')
def final():
    frozen=read('exports/rc2_freeze.json')
    assert all(digest(ROOT/p)==d for p,d in frozen['files'].items()),'Frozen file changed'
    marker=ROOT/'exports/rc2_holdout_execution.json'
    if marker.exists():raise SystemExit('Final sealed holdout already attempted; refusing another evaluation.')
    start=time.perf_counter();manifest,build,chunks=validate_build(ROOT)
    r=HybridRetriever(chunks,SemanticIndex(ROOT/'data/processed',ROOT/'data/models/all-MiniLM-L6-v2'))
    cold=time.perf_counter()-start
    reports={}
    dev=load(ROOT/'benchmarks/development.jsonl')
    for mode in ('hybrid','bm25','semantic'):
        reports['development_'+mode]=evaluate(dev,r,mode)
    for split in ('regression','adversarial'):
        reports[split+'_hybrid']=evaluate(load(ROOT/f'benchmarks/{split}.jsonl'),r)
    # Persist attempt before loading/evaluating the sealed labels. Even interrupted attempts cannot be repeated.
    write('exports/rc2_holdout_execution.json',{'started_at':datetime.now(timezone.utc).isoformat(),'attempts':1,'mode':'hybrid','freeze_sha256':digest(ROOT/'exports/rc2_freeze.json')})
    holdout=load(ROOT/'benchmarks/holdout.jsonl')
    reports['holdout_hybrid']=evaluate(holdout,r)
    write('exports/rc2_final_benchmarks.json',{'cold_start_seconds':cold,'reports':reports})
    for name,report in reports.items():print(name,json.dumps(report['metrics']))
    splits={s:load(ROOT/f'benchmarks/{s}.jsonl') for s in ('development','holdout','regression','adversarial')}
    leaks=[x for a,b in combinations(splits.values(),2) for x in leakage(a,b)]
    source='\n'.join(p.read_text(encoding='utf-8-sig').casefold() for p in production() if p.name!='benchmark.py')
    embedded=[];inaccessible=[];byid={c.chunk_id:c for c in chunks}
    for cases in splits.values():
        for c in cases:
            for kind,value in [('query',c['query']),('case_id',c['id']),('expected_quote',c.get('expected_quote',''))]+[('expected_chunk_id',x) for x in c['expected_chunk_ids']]:
                if value and value.casefold() in source:embedded.append({'id':c['id'],'kind':kind})
            for ident in c['expected_chunk_ids']:
                if ident not in byid or byid[ident].review_required:inaccessible.append({'id':c['id'],'chunk_id':ident})
    syntax=[]
    for p in production()+sorted((ROOT/'scripts').glob('*.py'))+sorted((ROOT/'tests').glob('*.py')):
        py_compile.compile(str(p),doraise=True);syntax.append(str(p.relative_to(ROOT)))
    # Failure investigation is deliberately after the freeze and single evaluation.
    failures=[]
    for c in holdout:
        row=next(x for x in reports['holdout_hybrid']['cases'] if x['id']==c['id'])
        if c['answerable'] and not row['approved_answer']:
            hits=r.search(c['query'],5,c.get('expected_model'),c.get('controller'))
            # Do not run answering again: preserve the measured result and evidence, then inspect source.
            failures.append({'id':c['id'],'query':c['query'],'expected_quote':c.get('expected_quote'),'expected_chunk_ids':c['expected_chunk_ids'],'measured_result':row,'top_evidence':[h.chunk.to_dict() for h in hits[:3]]})
    write('exports/rc2_postfreeze_holdout_analysis.json',failures)
    write('exports/rc2_integrity.json',{'syntax_files':syntax,'corpus_index_compatible':True,'frozen_files_unchanged':all(digest(ROOT/p)==d for p,d in frozen['files'].items()),'holdout_unchanged_since_baseline':digest(ROOT/'benchmarks/holdout.jsonl')==read('exports/rc2_baseline/baseline_results.json')['holdout_sha256'],'question_leakage':leaks,'production_benchmark_literals':embedded,'inaccessible_expected_evidence':inaccessible,'semantic_holdout_and_bm25_holdout':'Not rerun: final sealed holdout policy permits one canonical hybrid evaluation. Baseline includes all modes.','manual':manifest['documents'][0]})
    print('Integrity',len(leaks),'leaks;',len(embedded),'embedded benchmark literals;',len(inaccessible),'inaccessible expected sources')
if __name__=='__main__':
    {'freeze':freeze,'final':final}[sys.argv[1]]()
