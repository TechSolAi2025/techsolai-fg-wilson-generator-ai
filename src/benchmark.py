from __future__ import annotations
import argparse,json,re,time,statistics
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from dataclasses import replace
from src.retrieval import HybridRetriever,SemanticIndex
from src.models import SearchHit
from src.store import validate_build
from src.answering import answer

def norm(s): return ' '.join(re.findall(r'[a-z0-9]+',s.lower()))
def load(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def leakage(a,b):
    issues=[]
    for x in a:
        for y in b:
            one,two=norm(x['query']),norm(y['query']); ratio=SequenceMatcher(None,one,two).ratio()
            sa,sb=set(one.split()),set(two.split()); jac=len(sa&sb)/max(1,len(sa|sb))
            if ratio>=.85 or jac>=.8: issues.append({'left':x['id'],'right':y['id'],'sequence_similarity':round(ratio,3),'token_jaccard':round(jac,3)})
    return issues

def evaluate(cases,retriever,mode='hybrid',grader=None):
    rows=[]; latencies=[]
    for c in cases:
        start=time.perf_counter(); hits=retriever.search(c['query'],5,c.get('expected_model'),c.get('controller'),mode)
        ids=[h.chunk.chunk_id for h in hits]
        q=c['query']+(' '+c['controller'] if c.get('controller') else '')
        evidence=hits+(retriever.safety_evidence(hits[0]) if hits else [])
        result=answer(q,evidence)
        elapsed=(time.perf_counter()-start)*1000;latencies.append(elapsed)
        expected=set(c['expected_chunk_ids']);grounded=result['status']=='grounded'
        source_ids={s['chunk_id'] for s in result['sources']}
        source_map={h.chunk.chunk_id:h.chunk for h in evidence}
        source_identity=all(s['chunk_id'] in source_map and s['source_sha256']==source_map[s['chunk_id']].source_sha256 and s['manual']==source_map[s['chunk_id']].manual_title for s in result['sources'])
        faithful=not grounded or any(result['answer'] in h.chunk.text for h in evidence)
        claims=result.get('claims',[])
        claim_fidelity=not grounded or bool(claims) and all(
            cl['chunk_id'] in source_map and cl['chunk_id'] in source_ids
            and cl['source_sha256']==source_map[cl['chunk_id']].source_sha256
            and (cl['text'] in source_map[cl['chunk_id']].text or cl['text'] in source_map[cl['chunk_id']].warnings)
            and set(cl['pdf_pages'])<=set(range(source_map[cl['chunk_id']].page_start,source_map[cl['chunk_id']].page_end+1))|set(source_map[cl['chunk_id']].warning_pages)
            for cl in claims)
        # Extractive fidelity is a baseline, not an independent service-expert judgment of relevance/safety.
        numeric=not grounded or set(re.findall(r'\d+(?:\.\d+)?',result['answer']))<=set(re.findall(r'\d+(?:\.\d+)?',' '.join(h.chunk.text for h in evidence)))
        approved=grounded and bool(expected&source_ids) and c.get('expected_quote','').lower() in (' '.join([result['answer']]+result['steps'])).lower()
        rows.append({'id':c['id'],'answerable':c['answerable'],'topic':c.get('topic'),'retrieved_ids':ids,'top1':bool(ids and ids[0] in expected),'recall_at_3':bool(expected&set(ids[:3])),'recall_at_5':bool(expected&set(ids[:5])),'status':result['status'],'rejected':not grounded,'approved_answer':approved,'source_identity':source_identity,'extractive_faithfulness':faithful,'claim_fidelity':claim_fidelity,'numerical_consistency':numeric,'latency_ms':elapsed})
        rows[-1]['generated']=result
        if grader is not None:
            rows[-1]['evaluation']=grader(c,result,evidence,ids)
    positives=[r for r in rows if r['answerable']];negative=[r for r in rows if not r['answerable']];grounded=[r for r in rows if r['status']=='grounded']
    rate=lambda seq,key:sum(r[key] for r in seq)/len(seq) if seq else None
    metrics={'cases':len(rows),'answerable':len(positives),'top1':rate(positives,'top1'),'recall_at_3':rate(positives,'recall_at_3'),'recall_at_5':rate(positives,'recall_at_5'),'unsupported_rejection':rate(negative,'rejected'),'approved_deterministic_answers':rate(positives,'approved_answer'),'source_identity':rate(grounded,'source_identity'),'extractive_faithfulness':rate(grounded,'extractive_faithfulness'),'numerical_consistency':rate(grounded,'numerical_consistency'),'latency_ms_median':statistics.median(latencies) if latencies else None,'latency_ms_p95':sorted(latencies)[max(0,int(len(latencies)*.95)-1)] if latencies else None}
    metrics['all_field_claim_fidelity']=rate(grounded,'claim_fidelity')
    return {'metrics':metrics,'cases':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['all','development','holdout','holdout_rc3','adversarial','regression'],required=True);p.add_argument('--mode',choices=['bm25','semantic','hybrid'],default='hybrid')
    p.add_argument('--live-answers',action='store_true',help='Strict live answer grading with schema, evidence and safety checks')
    p.add_argument('--case-timeout',type=float,default=30.,help='Strict live mode: per-case production deadline in seconds')
    p.add_argument('--report-tag',default='',help='Separate result artifacts; never overwrite historical runs')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    if a.live_answers:
        from src.answer_evaluation import run
        raise SystemExit(run(root,a.split,a.mode,a.case_timeout,a.report_tag))
    if a.split=='all':p.error('--split all requires --live-answers')
    splits={s:load(root/f'benchmarks/{s}.jsonl') for s in ['development','holdout','adversarial','regression']}
    leaks=[x for one,two in combinations(splits,2) for x in leakage(splits[one],splits[two])]
    if leaks: raise SystemExit('Benchmark leakage detected: '+json.dumps(leaks))
    start=time.perf_counter();_,build,chunks=validate_build(root)
    semantic=SemanticIndex(root/'data/processed',root/'data/models/all-MiniLM-L6-v2') if a.mode!='bm25' else None
    retriever=HybridRetriever(chunks,semantic);cold=time.perf_counter()-start
    report=evaluate(splits[a.split],retriever,a.mode);report.update(split=a.split,mode=a.mode,cold_start_seconds=cold,leakage=leaks)
    (root/f'exports/{a.split}_{a.mode}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report['metrics'],indent=2));print('Cold start seconds:',cold)
if __name__=='__main__':main()
