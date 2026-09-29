from __future__ import annotations
import re
from src.models import SearchHit
from src.safety import query_block_reason,document_block_reason
from src.retrieval import tokens,query_tokens
REFUSAL='Not enough manufacturer-grounded information found to answer safely.'

def refusal(status='insufficient',reason=None,sources=None):
    return {'status':status,'answer':REFUSAL,'reason':reason,'steps':[],'warnings':[],'sources':sources or [],'claims':[]}

def citation(c):
    return {'manual':c.manual_title,'manufacturer':c.manufacturer,'document_number':c.document_number,'revision':c.revision,'applicability':c.applicability,'models':list(c.models),'controllers':list(c.controllers),'section':c.section,'pdf_page':f'{c.page_start}' if c.page_start==c.page_end else f'{c.page_start}–{c.page_end}','printed_page':', '.join(c.printed_pages),'chunk_id':c.chunk_id,'source_sha256':c.source_sha256,'warning_pdf_pages':sorted(set(c.warning_pages))}

def compact(text):return ' '.join(text.split())

def answer(query:str,hits:list[SearchHit],min_score:float=0)->dict:
    blocked=query_block_reason(query)
    if blocked:return refusal('blocked',blocked)
    if not hits:return refusal()
    # Validate every supplied hit before conflict handling, fallback, warnings or citation construction.
    if any(document_block_reason(h.chunk.text+' '+' '.join(h.chunk.warnings)) for h in hits):return refusal('blocked','Document instruction injection detected')
    if any(h.chunk.review_required or h.chunk.manufacturer!='FG Wilson' for h in hits):return refusal('review_required','Evidence excluded from answer generation')
    top=hits[0].chunk
    # Unresolved table headers cannot establish what a value measures. Preserve
    # the source for review instead of presenting an anonymous cell as guidance.
    if re.search(r'(?m)^Column:',top.text) or '[empty cell]' in top.text:
        return refusal('review_required','Table headers or applicability require source review')
    eligible=[h for h in hits[:3] if h.score>=hits[0].score*.9]
    if len({(h.chunk.document_id,h.chunk.revision) for h in eligible})>1 and len({h.chunk.text for h in eligible})>1:
        return refusal('conflict','Conflicting or revision-specific evidence; verify source and applicability',[citation(h.chunk) for h in eligible])
    for other in eligible[1:]:
        c=other.chunk
        if top.table.get('complete') and c.table.get('id')==top.table.get('id') and c.table.get('ordinal')!=top.table.get('ordinal'):
            continue  # Distinct labelled rows are alternatives, not contradictory copies.
        if c.section==top.section and c.controllers==top.controllers and c.text!=top.text:
            shape=lambda t:re.sub(r'\d+(?:\.\d+)?','#',compact(t).lower())
            polarity=lambda t:re.sub(r'\b(?:not|never)\s+','',compact(t).lower())
            if shape(c.text)==shape(top.text) or polarity(c.text)==polarity(top.text):
                return refusal('conflict','Conflicting numerical or negative evidence',[citation(top),citation(c)])
    if top.controllers and not any(re.search(r'(?<![\w.])'+re.escape(x.lower())+r'(?![\w.+])',query.lower()) for x in top.controllers):
        return refusal('ambiguous','Select the fitted controller to resolve applicability')
    q=set(query_tokens(query));evidence=set(tokens(top.text+' '+top.section+' '+' '.join(top.controllers)))
    coverage=len(q&evidence)/max(1,len(q))
    recorded=[float(r.split('=')[1]) for r in hits[0].reasons if r.startswith('coverage=')]
    if max([coverage]+recorded)<.55:return refusal()
    nums=set(re.findall(r'(?<!\w)\d+(?:\.\d+)?',query))
    if not nums.issubset(set(re.findall(r'(?<!\w)\d+(?:\.\d+)?',top.text+' '+' '.join(top.controllers)))):return refusal()
    if top.table:
        from src.table_context import table_selection
        controllers={ctl for h in hits for ctl in h.chunk.controllers if re.search(r'(?<![\w.])'+re.escape(ctl.lower())+r'(?![\w.+])',query.lower())}
        if len(controllers)>1:return refusal('ambiguous','Select one fitted controller')
        selected=table_selection(query,top,{h.chunk.chunk_id:h.chunk for h in hits},next(iter(controllers),None))
        if selected.get('error'):return refusal('review_required',selected['error'])
        return table_answer(selected,hits)
    paragraphs=[p.strip() for p in top.text.split('\n\n') if len(p.strip())>12 and compact(p)!=compact(top.section) and not re.fullmatch(r'(?:Warning|Caution|Note):?',p.strip(),re.I)]
    if not paragraphs:return refusal()
    table=re.search(r'(?m)^(?:Possible )?Remedy:\s*',top.text)
    procedure=bool(re.search(r'(?m)^\d+[.\t]|^•',top.text))
    if table:
        summary=top.text
        steps=[top.text[table.end():].strip()]
    elif procedure:
        summary=max(paragraphs,key=lambda p:len(q&set(tokens(p))))
        steps=[top.text]
    else:
        # Declarative sections keep their conditions, exceptions and warnings as a contiguous source excerpt.
        first=top.text.split('\n\n',1)
        summary=first[1] if len(first)>1 and compact(first[0])==compact(top.section) else top.text
        steps=[]
    warnings=[];sources=[citation(top)];claims=[]
    def claim(field,text,c,pages=None):
        claims.append({'field':field,'text':text,'chunk_id':c.chunk_id,'source_sha256':c.source_sha256,'pdf_pages':pages or list(range(c.page_start,c.page_end+1))})
    claim('answer',summary,top)
    for step in steps:claim('steps',step,top)
    for w,n in zip(top.warnings,top.warning_pages):
        if w not in warnings:warnings.append(w);claim('warnings',w,top,[n])
    for h in hits[1:]:
        c=h.chunk
        if c.section.startswith('2.') and set(c.hazards)&set(top.hazards):
            if c.chunk_id not in {s['chunk_id'] for s in sources}:sources.append(citation(c))
            # Retain the complete safety context, including qualifications outside bold warning blocks.
            if c.text not in warnings:warnings.append(c.text);claim('warnings',c.text,c)
    return {'status':'grounded','answer':summary,'steps':steps,'warnings':warnings,'sources':sources,'claims':claims,'qualified_service':top.requires_qualified_service}


def table_answer(selected,hits):
    """Emit separate, fully cited source rows and their shared context."""
    rows=selected['rows'];context=selected['context'];sources={};claims=[];warnings=[]
    def claim(field,text,c,pages=None):
        sources[c.chunk_id]=citation(c)
        claims.append({'field':field,'text':text,'chunk_id':c.chunk_id,'source_sha256':c.source_sha256,'pdf_pages':pages or list(range(c.page_start,c.page_end+1))})
    lead=context[0] if selected['broad'] and context else rows[0]
    summary=lead.text;claim('answer',summary,lead)
    steps=[]
    for c in rows:
        steps.append(c.text);claim('steps',c.text,c)
    for c in rows+context:
        for w,page in zip(c.warnings,c.warning_pages):
            if w not in warnings:warnings.append(w);claim('warnings',w,c,[page])
    for c in context:
        if c!=lead and c.text not in warnings:warnings.append(c.text);claim('warnings',c.text,c)
    hazards={h for c in rows for h in c.hazards}
    for hit in hits:
        c=hit.chunk
        if not c.table and c.section.startswith('2.') and hazards&set(c.hazards) and c.text not in warnings:
            warnings.append(c.text);claim('warnings',c.text,c)
    return {'status':'grounded','answer':summary,'steps':steps,'warnings':warnings,'sources':list(sources.values()),'claims':claims,
            'qualified_service':any(c.requires_qualified_service for c in rows+context),
            'table_rows':[c.chunk_id for c in rows],'table_complete':True}
