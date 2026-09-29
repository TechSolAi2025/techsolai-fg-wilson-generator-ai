from __future__ import annotations
import hashlib,re
from dataclasses import replace
from src.models import Chunk
from src.identifiers import extract_identifiers

HEAD=re.compile(r'^(\d+(?:\.\d+)*)(?:\.|\s)\s*([A-Za-z].*)$',re.S)
FAULT_RE=re.compile(r'\b(?:fault|alarm)\s+code\s*[:#]?\s*([A-Z0-9-]+)\b',re.I)
HAZARDS={'automatic-start':('automatic','remote start'),'electrical-shock':('electrical','voltage','electrocution'),'fuel':('fuel','diesel'),'exhaust':('exhaust',),'hot-surface':('hot','burn','coolant'),'rotating-component':('rotating','moving parts','belts'),'battery':('battery','batteries','electrolyte'),'lifting':('lift','crush'),'qualified-service':('qualified','trained','dealer')}

def clean(text):
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',text).strip()

def classify(text,section=''):
    t=(section+' '+text).lower(); s=section.lower()
    for name,terms in [('pre-start-inspections',('pre-start checks',)),('fault-finding',('trouble shooting','fault finding','critical failures')),('service-intervals',('interval schedule',)),('battery-charging',('battery',)),('storage',('storage',)),('lubrication',('lubrication oil',' oils')),('cooling-system',('coolant','cooling')),('fuel-system',('fuel','priming','water separator')),('exhaust',('exhaust',)),('air-intake',('air intake','air filter')),('alternator',('alternator',)),('electrical-checks',('electrical','isolating','circuit breaker')),('qualified-service-escalation',('speed / voltage',)),('alarms-shutdowns',('alarm','protections')),('control-panel-operation',('control module','control system','security','programming','display','led lamps','functionality')),('starting-stopping',('basic operation','operation of the unit','engine operation','jump start')),('specifications',('power factor','sound level')),('generator-identification',('description','rating plate','pin plate')),('preventive-maintenance',('maintenance',)),('safety',('hazard','protective','fire','noise','mechanical','chemical','burn','first aid')),('operating-procedures',('operation',)),('installation-handling',('installation','foundation','lifting','moving','plinth'))]:
        if any(x in s for x in terms): return name
    if s.startswith('2.'): return 'safety'
    return 'general'

def chunk_pages(pages,meta,max_chars=2600,review=None):
    # Size is advisory: a section/procedure is never split merely to fit a token budget.
    review=review or {}; units=[]; current=None
    excluded=set(review.get('non_content_pages',[])); controllers=review.get('controller_sections',{})
    def flush():
        nonlocal current
        if current and (current['parts'] or current['tables']): units.append(current)
        current=None
    for p in pages:
        if p['page'] in excluded: continue
        image_table=review.get('image_tables',{}).get(str(p['page']))
        tables=p.get('tables',[])
        blocks=p.get('blocks') or [{'text':p['text'],'font_size':0,'bbox':[0,0,0,0],'bold':False}]
        events=[(b['bbox'][1],0,b) for b in blocks]+[(t['bbox'][1],1,t) for t in tables]
        for _,kind,b in sorted(events,key=lambda e:(e[0],e[1])):
            if kind==1:
                if current: current['tables'].append((p['page'],b['rows']))
                continue
            text=clean(b['text'])
            if not text or (b['bbox'][1]>p.get('height',99999)*.95): continue
            if any(t['bbox'][0]-2<=b['bbox'][0] and b['bbox'][1]>=t['bbox'][1]-2 and b['bbox'][3]<=t['bbox'][3]+2 for t in tables): continue
            match=HEAD.match(text)
            if match and b.get('bold') and b.get('font_size',0)>=10.8 and len(text)<150:
                flush(); current={'section':re.sub(r'\s+',' ',text),'number':match[1],'parts':[],'pages':[],'warnings':[],'warning_pages':[],'tables':[]}
            if current is None: current={'section':'Cover and applicability' if p['page']==1 else 'Unspecified section','number':'0','parts':[],'pages':[],'warnings':[],'warning_pages':[],'tables':[]}
            current['parts'].append(text); current['pages'].append(p['page'])
            if (b.get('bold') and re.match(r'^I\s',text)) or re.match(r'(?i)^(?:warning|caution)\s*:',text):
                current['warnings'].append(text); current['warning_pages'].append(p['page'])
        if current:
            if image_table:
                if not image_table.get('approved'): raise ValueError('Unapproved image transcription')
                current['tables'].append((p['page'],[image_table['headers']]+image_table['rows']))
                current['parts'].append(image_table['context'])
                current['pages'].append(p['page'])
    flush()
    chunks=[]; ancestor_warnings={}
    for u in units:
        number=u['number']; parts=number.split('.')
        inherited=[]
        for depth in range(1,len(parts)):
            inherited.extend(ancestor_warnings.get('.'.join(parts[:depth]),[]))
        own=list(zip(u['warnings'],u['warning_pages']))
        ancestor_warnings[number]=inherited+own
        warnings=inherited+own
        scope=next((controllers[k] for k in sorted(controllers,key=len,reverse=True) if number==k or number.startswith(k+'.')),[])
        reason=next((v for k,v in review.get('quarantined_sections',{}).items() if number==k or number.startswith(k+'.')),None)
        def emit(text,ns,category=None):
            if not text.strip() or re.sub(r'\s+',' ',text.strip())==u['section']: return
            ctl=list(scope); low=text.lower()
            # Explicit applicability qualifiers in source cells override section inheritance.
            if 'under-voltage' in low and 'powerwizard 2.1 only' in low: ctl=['PowerWizard 2.1']
            if 'over-voltage' in low and 'optional on' in low: ctl=['PowerWizard 2.1','PowerWizard 1.1+']
            identifiers=list(extract_identifiers(text))+list(meta.get('models',()))+ctl
            hazard_text=' '.join(low.split())
            hazards=tuple(k for k,terms in HAZARDS.items() if any(x in hazard_text for x in terms))
            if any(x in hazard_text for x in ('auto start','cannot be started','starting circuit')) and 'automatic-start' not in hazards:
                hazards+=('automatic-start',)
            start,end=min(ns),max(ns)
            digest=hashlib.sha256(f'{meta["sha256"]}|{start}|{end}|{text}'.encode()).hexdigest()[:24]
            chunks.append(Chunk(chunk_id=meta['id']+':'+digest,document_id=meta['id'],manual_title=meta['title'],manufacturer=meta['manufacturer'],models=tuple(meta['models']),section=u['section'],page_start=start,page_end=end,text=text,category=category or classify(text,u['section']),fault_codes=tuple(FAULT_RE.findall(text)),hazards=hazards,revision=meta['revision'],source_sha256=meta['sha256'],requires_qualified_service=number.startswith(('8','5.4.5')) or any(x in low for x in ('qualified','trained','dealer')),printed_pages=tuple(str(pages[n-1].get('printed_page') or 'unnumbered') for n in sorted(set(ns))),controllers=tuple(ctl),applicability=meta['applicability'],document_number=meta['document_number'],identifiers=tuple(dict.fromkeys(identifiers)),warnings=tuple(w for w,n in warnings),warning_pages=tuple(n for w,n in warnings),review_required=bool(reason)))
        body='\n\n'.join(u['parts'])
        if u['pages']: emit(body,u['pages'])
        for n,rows in u['tables']:
            if not rows: continue
            headers=rows[0]
            # Continuation tables without a header retain the previous table schema.
            continuation=review.get('table_continuation_headers',{}).get(str(n))
            if continuation:
                headers=continuation; data=rows
            else: data=rows[1:]
            for row in data:
                if not any(row): continue
                if len(row)!=len(headers): raise ValueError('Malformed table row')
                text=u['section']+'\n'+'\n'.join(f'{clean(str(h or "Column"))}: {clean(str(cell or "[empty cell]"))}' for h,cell in zip(headers,row))
                emit(text,[n],'fault-finding' if any('remedy' in str(h).lower() for h in headers) else classify(text,u['section']))
    originals={c.chunk_id:c for c in chunks}
    for recovery in review.get('recoveries',[]):
        original=originals.get(recovery['original_chunk_id'])
        if review.get('source_sha256')!=meta['sha256'] or not original or not original.review_required or recovery.get('approved') is not True:
            raise ValueError('Invalid source recovery approval or identity')
        text=recovery['text']
        if not text.strip() or '[empty cell]' in text: raise ValueError('Incomplete source recovery')
        digest=hashlib.sha256(f'{meta["sha256"]}|{original.page_start}|{original.page_end}|{text}'.encode()).hexdigest()[:24]
        chunks.append(replace(original,chunk_id=meta['id']+':'+digest,text=text,review_required=False,
            recovery_of=original.chunk_id,extraction_method=recovery['method'],
            identifiers=tuple(dict.fromkeys(list(extract_identifiers(text))+list(original.models)+list(original.controllers)))))
    from src.table_context import attach_tables
    return attach_tables(chunks,pages,meta,review)
