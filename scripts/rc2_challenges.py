"""Independent source-only robustness generator. It cannot import application retrieval or benchmark labels.
Each checkpoint consumes a disjoint source partition; outputs are evaluated only after changes are complete.
This is reproducible mechanical paraphrasing/noise, not a human-authored blind field test.
"""
import json,random,re,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    batch=int(sys.argv[1]);out=ROOT/'benchmarks/rc2_challenges';out.mkdir(exist_ok=True)
    target=out/f'checkpoint_{batch}.jsonl'
    if target.exists():raise SystemExit('Challenge batch already generated; use a fresh batch.')
    raw=(ROOT/'exports/rc2_baseline/chunks.json').read_bytes();chunks=json.loads(raw)
    pool=[c for c in chunks if not c['review_required'] and not c['controllers'] and '\n\n' in c['text'] and len(c['text'])>250 and not c['section'].startswith(('3.3','3.4'))]
    random.Random(91723).shuffle(pool);selected=pool[(batch-1)*6:batch*6]
    if len(selected)!=6:raise SystemExit('Independent source partitions exhausted')
    synonyms={'Maintenance':'Upkeep','Storage':'Storage','Inspections':'Checks','Description':'Overview','Preventative':'Preventive','General':'General','Protection':'Protection','Cold Weather':'Low Temperature'}
    cases=[]
    for i,c in enumerate(selected):
        title=re.sub(r'^\d+(?:\.\d+)*\.?\s*','',c['section'])
        paraphrase=title
        for old,new in synonyms.items():paraphrase=paraphrase.replace(old,new)
        words=title.split();j=max(range(len(words)),key=lambda k:len(words[k]));w=words[j]
        if len(w)>4:words[j]=w[:2]+w[3]+w[2]+w[4:]
        queries={'exact':f'Find guidance on {title}.','paraphrase':f'I need the manufacturer instructions concerning {paraphrase.lower()}.','noisy':'What about '+' '.join(words).lower()+'?'}
        for variant,q in queries.items():cases.append({'id':f'checkpoint-{batch}-{i}-{variant}','query':q,'variant':variant,'answerable':True,'controller':None,'expected_chunk_ids':[c['chunk_id']],'expected_quote':c['text'].split('\n\n')[1],'source_sha256':c['source_sha256']})
    target.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
    (out/f'checkpoint_{batch}_provenance.json').write_text(json.dumps({'process':'source-only script with fixed seed and disjoint source partitions','source_snapshot_sha256':hashlib.sha256(raw).hexdigest(),'batch':batch,'cases':len(cases),'production_or_benchmark_imports':False,'limitation':'mechanical paraphrases; no independent human generation'},indent=2),encoding='utf-8')
    print('Sealed challenge batch generated:',batch,len(cases))
if __name__=='__main__':main()
