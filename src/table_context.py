"""Source-bound table structure. No query answers or inferred cells are stored here."""
from dataclasses import replace
import hashlib
import re


def compact(text):
    return ' '.join(text.split())


def render(section,headers,cells):
    from src.chunking import clean
    return section+'\n'+'\n'.join(f'{clean(str(h or "Column"))}: {clean(str(c or "[empty cell]"))}' for h,c in zip(headers,cells))


def attach_tables(chunks,pages,meta,review):
    """Attach explicit reviewed membership, never infer continuation from proximity.

    Existing row text/IDs remain intact. A reviewed merged-header correction adds
    source-derived rows and marks obsolete extraction rows unusable as tables.
    Existing quarantined rows are never promoted by this mechanism.
    """
    if not review.get('table_groups'):return chunks
    if review.get('source_sha256')!=meta['sha256']:raise ValueError('Table review source mismatch')
    result=list(chunks)
    for spec in review['table_groups']:
        if spec.get('approved') is not True:raise ValueError('Unapproved table boundary')
        section=spec['section']; members=[]; headers=None; issues=[]; positions=[]
        candidates=[c for c in result if c.section==section]
        if not candidates:raise ValueError('Reviewed table section missing')
        table_id=hashlib.sha256((meta['sha256']+'|'+section+'|'+str(spec['parts'])).encode()).hexdigest()
        for part in spec['parts']:
            page=part['page']; p=pages[page-1]
            if part.get('image'):
                image=review['image_tables'][str(page)]
                if not image.get('approved'):raise ValueError('Unapproved image table')
                raw=[image['headers']]+image['rows']
            else:raw=p['tables'][part.get('table',0)]['rows']
            if part.get('continuation'):
                if headers is None:raise ValueError('Orphan continuation')
                local=review['table_continuation_headers'].get(str(page),headers)
                if list(map(compact,local))!=list(map(compact,headers)):raise ValueError('Continuation header mismatch')
                data_start=0
            else:
                index=part.get('header_row',0);local=raw[index];data_start=index+1
                if headers is not None and list(map(compact,local))!=list(map(compact,headers)):
                    raise ValueError('Connected table schemas differ')
                headers=local
            if any(not h or compact(h).casefold()=='column' for h in local):issues.append('incomplete headers')
            for row_index in range(data_start,len(raw)):
                cells=list(raw[row_index])
                # Only a visually verified merged rectangle may supply shared text.
                for span in part.get('merged_cells',[]):
                    if span['start']<=row_index<=span['end']:
                        original=raw[span['start']][span['column']]
                        if not original:raise ValueError('Merged cell has no source text')
                        if cells[span['column']] not in (None,'',original):raise ValueError('Conflicting merged cell')
                        cells[span['column']]=original
                if len(cells)!=len(local) or any(c is None or not str(c).strip() for c in cells):issues.append('missing cells or icon labels')
                text=render(section,local,cells)
                found=next((c for c in candidates if c.page_start==page and compact(c.text)==compact(text)),None)
                if spec.get('correct_headers'):
                    # Canonical rows derive only from this reviewed source rectangle.
                    base=next(c for c in candidates if c.page_start<=page<=c.page_end)
                    if base.review_required:raise ValueError('Cannot promote quarantined table')
                    digest=hashlib.sha256(f'{meta["sha256"]}|{page}|{page}|{text}'.encode()).hexdigest()[:24]
                    from src.identifiers import extract_identifiers
                    found=replace(base,chunk_id=meta['id']+':'+digest,text=text,page_start=page,page_end=page,
                                  printed_pages=(str(p.get('printed_page') or 'unnumbered'),),table={},
                                  identifiers=tuple(extract_identifiers(text)),extraction_method='native cells with source-reviewed title, headers and merged spans')
                    result.append(found)
                elif found and found.review_required:
                    recovery=next((c for c in candidates if c.recovery_of==found.chunk_id),None)
                    if recovery:found=recovery
                if found is None:issues.append('source row missing from chunks')
                else:members.append(found)
                positions.append({'page':page,'table':part.get('table',0),'row':row_index})
        if len(members)!=spec['expected_rows']:issues.append('row count mismatch')
        if any(c.review_required for c in members):issues.append('quarantined member')
        if len({c.chunk_id for c in members})!=len(members):issues.append('duplicate member')
        ids=[c.chunk_id for c in members]
        # Table rows are single-newline labelled records. Prose context retains
        # original paragraph boundaries, conditions, footnotes and source pages.
        context=[c for c in candidates if c.chunk_id not in ids and '\n\n' in c.text and not c.recovery_of]
        if any(c.review_required for c in context):issues.append('quarantined context')
        common={'id':table_id,'title':section,'headers':[compact(h or '') for h in headers],
                'row_ids':ids,'context_ids':[c.chunk_id for c in context],
                'expected_rows':spec['expected_rows'],'complete':not issues,'issues':sorted(set(issues)),
                'positions':positions,'source_sha256':meta['sha256'],'role':spec['role']}
        updates={c.chunk_id:replace(c,table={**common,'kind':'row','ordinal':n}) for n,c in enumerate(members)}
        updates.update({c.chunk_id:replace(c,table={**common,'kind':'context'}) for c in context})
        if spec.get('correct_headers'):
            for c in candidates:
                if c.chunk_id not in updates:
                    updates[c.chunk_id]=replace(c,table={**common,'kind':'obsolete','complete':False,'issues':['superseded anonymous header extraction']})
        result=[updates.get(c.chunk_id,c) for c in result]
    return result


def table_selection(query,top,byid,controller=None):
    """Return a complete source group plus a broad/specific selection contract."""
    from src.retrieval import query_tokens,tokens
    table=top.table
    if not table:return None
    required={'id','title','headers','row_ids','context_ids','expected_rows','complete','kind','role','source_sha256'}
    if not isinstance(table,dict) or not required<=table.keys():return {'error':'Malformed table metadata'}
    if table.get('complete') is not True or table.get('kind') not in ('row','context'):return {'error':'Incomplete or quarantined table; source review required'}
    if not isinstance(table['headers'],list) or not table['headers'] or any(not isinstance(h,str) or not h.strip() for h in table['headers']):return {'error':'Incomplete header inheritance'}
    if any(not isinstance(table[k],list) or any(not isinstance(i,str) for i in table[k]) for k in ('row_ids','context_ids')):return {'error':'Malformed table membership'}
    if type(table['expected_rows']) is not int or table['expected_rows']<1:return {'error':'Invalid table boundary'}
    ids=table['row_ids']+table['context_ids']
    if len(set(ids))!=len(ids):return {'error':'Duplicate table membership'}
    if any(i not in byid for i in ids):return {'error':'Orphan table member or context'}
    members=[byid[i] for i in ids]
    identity=lambda c:(c.document_id,c.revision,c.source_sha256,c.section,c.models,c.applicability)
    if any(identity(c)!=identity(top) or c.review_required or c.table.get('id')!=table['id'] for c in members):
        return {'error':'Table source identity or quarantine mismatch'}
    if any(any(c.table.get(k)!=table[k] for k in ('headers','row_ids','context_ids','expected_rows','source_sha256','complete','role')) for c in members):return {'error':'Inconsistent table header or boundary inheritance'}
    if table['source_sha256']!=top.source_sha256:return {'error':'Table source hash mismatch'}
    rows=[byid[i] for i in table['row_ids']]
    if len(rows)!=table['expected_rows'] or [c.table.get('ordinal') for c in rows]!=list(range(len(rows))):
        return {'error':'Truncated or reordered table'}
    if any(c.controllers for c in rows) and not controller:return {'error':'Select the fitted controller before interpreting this table'}
    applicable=[c for c in rows if not c.controllers or controller in c.controllers]
    if not applicable:return {'error':'No applicable rows for fitted controller'}
    q=set(query_tokens(query))
    if controller:q-=set(tokens(controller))
    heading=set(tokens(table['title']))
    request={'all','table','rows','list','complete','overview','summary','summarize'}
    broad=bool(q) and not (q-heading-request)
    if not broad and re.search(r'\b(?:all|every|each|complete)\b',query,re.I):
        return {'error':'Ambiguous multi-row request; specify the table subject and applicability'}
    if not broad:
        selectors=q-heading-request
        matches=[]
        for row in applicable:
            subject=re.split(r'\n(?:Remedy|Possible Remedy|Required Action|Function):',row.text,maxsplit=1)[0]
            if selectors and selectors<=set(tokens(subject)):matches.append(row)
        if len(matches)>1:return {'error':'Multiple applicable table subjects; specify the symptom or component'}
    # A prose heading cannot stand in for an unselected row. Ask for context
    # instead of silently presenting only one member of a broad request.
    if top.table.get('kind')=='context' and not broad:return {'error':'Specify the table row, symptom or component'}
    selected=applicable if broad else [top]
    if any(c not in applicable for c in selected):return {'error':'Row is outside fitted applicability'}
    return {'broad':broad,'rows':selected,'context':[byid[i] for i in table['context_ids']], 'members':members}
