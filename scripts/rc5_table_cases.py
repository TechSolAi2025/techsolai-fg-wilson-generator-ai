"""Author internal structure tests from source groups, before their live run.

These are developer-authored cases, never an independent holdout. Existing
records are preserved byte-for-byte; this script refuses duplicate IDs.
"""
from pathlib import Path
import json
from src.store import validate_build
from src.answer_evaluation import quantities,schema_errors

ROOT=Path(__file__).resolve().parents[1]


def main():
    _,_,chunks=validate_build(ROOT);byid={c.chunk_id:c for c in chunks}
    groups={c.table['id']:c.table for c in chunks if c.table and c.table['kind']!='obsolete'}
    plans=[('development','measurement',13,None),('development','diagnostic',45,'PowerWizard 1.1'),
           ('development','control',57,'FG100'),('regression','diagnostic',34,None),
           ('regression','diagnostic',55,'DeepSea (model unspecified)')]
    for n,(split,role,page,controller) in enumerate(plans,1):
        t=next(t for t in groups.values() if t['role']==role and t['positions'][0]['page']==page)
        title=t['title'].split(' ',1)[1]
        query=('List all '+title+' table rows.') if split=='development' else ('Summarize the complete '+title+' table.')
        ids=[i for i in t['row_ids'] if not byid[i].controllers or controller in byid[i].controllers]
        expected=[byid[i] for i in ids];context=[byid[i] for i in t['context_ids']]
        c={'id':f'rc5-structure-{n:03d}','query':query,'controller':controller,'topic':'table-structure',
           'answerable':t['complete'],'expected_chunk_ids':ids+t['context_ids'] if t['complete'] else [],
           'provenance':'source-authored internal table structure challenge; not independent',
           'metadata':{'table_id':t['id'],'source_parts':t['positions'],'authoring':'source schema and manual context, not retrieval output'}}
        if c['answerable']:
            pairs=list(dict.fromkeys(q for s in expected for q in quantities(s.text)))
            c.update(expected_quote=expected[0].text,source_pages=sorted({p for s in expected+context for p in range(s.page_start,s.page_end+1)}),
                     source_sha256=expected[0].source_sha256,
                     assertions={'required':[s.text for s in expected+context],
                                 'order':[s.text for s in expected],
                                 'qualifiers':[s.text for s in context],
                                 'quantities':[{'value':v,'unit':u} for v,u in pairs]})
        errors=schema_errors(c,byid)
        if errors:raise ValueError(errors)
        path=ROOT/f'benchmarks/{split}.jsonl'
        existing=path.read_text(encoding='utf-8')
        if any(json.loads(line)['id']==c['id'] for line in existing.splitlines()):raise ValueError('Case already authored')
        with path.open('a',encoding='utf-8') as f:f.write(json.dumps(c,ensure_ascii=False)+'\n')
        print(c['id'],split,len(c['expected_chunk_ids']),'source chunks')


if __name__=='__main__':main()
