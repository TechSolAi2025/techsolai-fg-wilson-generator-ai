"""Deterministic grading for the existing live benchmark pipeline, never an LLM judge.

Legacy expected_quote is the sole explicit required assertion. Relevant source
paragraphs supply conditions/negations; numbered source steps supply order;
source warning metadata supplies safety obligations. No rationale/topic/grader
metadata is treated as technical answer text. Missing annotations are reported.
"""
from __future__ import annotations
import hashlib,json,math,multiprocessing,re,statistics,time,unicodedata
from collections import Counter
from datetime import datetime,timezone
from itertools import combinations
from pathlib import Path

SPLITS=('development','holdout','adversarial','regression')
KINDS=('required','prohibited','identifiers','qualifiers','negations','order','warnings','escalation')
NUMBER=r'[+-]?\d+(?:\.\d+)?'
UNIT=r'%|kPa|MPa|Pa|psi|PPM|ppm|mm|cm|kW|MW|mW|kVA|Hz|rpm|dB\(A\)|dBA|[Vv]olts?|[Hh]ours?|[Ww]eeks?|[Mm]onths?|[Ss]econds?|[Mm]inutes?|[°][CF]'
QUANTITY=re.compile(r'(?<![\w.])('+NUMBER+r')\s*('+UNIT+r')(?=$|[^\w])')
HEADER_QUANTITY=re.compile(r'^[^:\n]*?('+UNIT+r')(?:\(\d+\))*[ \t]*:[ \t]*('+NUMBER+r')[ \t]*$')
CONDITION=re.compile(r'\b(if|unless|until|only|before|after|when|provided|at least|at most|above|below|maximum|minimum)\b',re.I)
NEGATION=re.compile(r'\b(not|never|cannot|without|no)\b',re.I)
IDENTIFIER=re.compile(r'\b(?:ISO\s*(?:specification\s*)?\d+(?:[-/]\d+)+|PowerWizard\s*\d+(?:\.\d+)?\+?|FG\s*\d+|\d{4,}-\d+)\b')
GRADER=re.compile(r'(?i)(?:^|\n)\s*(?:grader instructions?|grading rubric|score this|award points|expected chunk ids?)\s*:')
STATUS={'grounded','insufficient','blocked','ambiguous','review_required','conflict'}
ANNOTATION_FIELDS={'required_assertions':'required','prohibited_assertions':'prohibited','required_identifiers':'identifiers','required_qualifiers':'qualifiers','required_negations':'negations','required_warnings':'warnings','required_escalation':'escalation'}

def normalize(text):
    # Preserve numbers, signs, units, word order and negation; no stemming or synonyms.
    return ' '.join(unicodedata.normalize('NFC',text).translate(str.maketrans({'\u2018':"'",'\u2019':"'",'\u201c':'"','\u201d':'"','\u2010':'-','\u2011':'-'})).split())

def contains(text,assertion):
    return bool(re.search(r'(?<!\w)'+re.escape(normalize(assertion).casefold())+r'(?!\w)',normalize(text).casefold()))

def quantities(text):
    pairs=QUANTITY.findall(normalize(text))
    # Explicit column-unit labels apply to their own scalar cell only. No unit
    # is inferred from another row, surrounding prose or an unnamed column.
    for line in text.splitlines():
        if match:=HEADER_QUANTITY.fullmatch(normalize(line)):
            pairs.append((match[2],match[1]))
    return pairs

def prohibited_present(text,assertion):
    """Distinguish a prohibited affirmative clause from the source prohibiting it.

    Bounded rule: a not/never/cannot prefix in the same clause negates a positive
    assertion. This does not claim full natural-language entailment.
    """
    text=normalize(text).casefold();assertion=normalize(assertion).casefold()
    for match in re.finditer(r'(?<!\w)'+re.escape(assertion)+r'(?!\w)',text):
        prefix=re.split(r'[.!?;]',text[:match.start()])[-1]
        if not re.search(r'\b(?:not|never|cannot)\b',prefix):return True
    return False

def schema_errors(case,chunks):
    errors=[]
    if not isinstance(case,dict):return ['record must be an object']
    allowed={'id','query','answerable','controller','topic','expected_model','expected_chunk_ids','expected_quote','source_pages','source_sha256','rationale','metadata','grader_instructions','assertions'}
    allowed|=set(ANNOTATION_FIELDS)|{'required_values','required_units','expected_source_document','expected_pages','expected_route','annotation_not_applicable','annotation_basis','annotation_verification','provenance','original_split'}
    if set(case)-allowed:errors.append('unsupported fields: '+','.join(sorted(set(case)-allowed)))
    for field in ANNOTATION_FIELDS:
        values=case.get(field,[])
        if not isinstance(values,list) or any(not isinstance(v,str) or not v.strip() or GRADER.search(v) for v in values):errors.append('invalid structured annotation: '+field)
    values,units=case.get('required_values',[]),case.get('required_units',[])
    if not isinstance(values,list) or not isinstance(units,list) or len(values)!=len(units) or any(not isinstance(v,str) or not re.fullmatch(NUMBER,v) for v in values) or any(not isinstance(u,str) or not u for u in units):errors.append('invalid paired required_values/required_units')
    for key in ('id','query'):
        if not isinstance(case.get(key),str) or not case[key].strip():errors.append(key+' must be a nonempty string')
    if type(case.get('answerable')) is not bool:errors.append('answerable must be boolean')
    for key in ('controller','expected_model','topic','rationale','grader_instructions'):
        if case.get(key) is not None and not isinstance(case[key],str):errors.append(key+' must be a string or null')
    if 'metadata' in case and not isinstance(case['metadata'],dict):errors.append('metadata must be an object')
    ids=case.get('expected_chunk_ids')
    if not isinstance(ids,list) or any(not isinstance(x,str) for x in ids):errors.append('expected_chunk_ids must be a string list');ids=[]
    elif len(ids)!=len(set(ids)):errors.append('duplicate expected chunk IDs')
    if 'expected_route' in case:
        route={'kind':'manufacturer_evidence' if case.get('answerable') is True else 'refusal','sections':[chunks[i].section for i in ids if i in chunks],'controller':case.get('controller')}
        if case['expected_route']!=route:errors.append('structured expected route mismatch')
    if case.get('answerable') is True:
        if not ids:errors.append('positive record requires evidence IDs')
        quote=case.get('expected_quote')
        if not isinstance(quote,str) or not quote.strip() or GRADER.search(quote):errors.append('positive expected_quote must contain technical evidence, not grader instructions')
        pages=case.get('source_pages')
        if not isinstance(pages,list) or not pages or any(type(p) is not int or p<1 for p in pages):errors.append('positive source_pages must be positive integers');pages=[]
        for ident in ids:
            c=chunks.get(ident)
            if c is None or c.review_required:errors.append('missing or excluded expected evidence: '+ident);continue
            if case.get('source_sha256')!=c.source_sha256:errors.append('expected source hash mismatch')
        # A multi-row answer has multiple distinct source excerpts. The legacy
        # anchor quotation must occur in at least one declared source; required
        # assertions/order still grade every annotated row independently.
        if isinstance(quote,str) and not any(contains(chunks[i].text,quote) for i in ids if i in chunks):errors.append('expected quotation unsupported by evidence')
        available={p for i in ids if i in chunks for p in range(chunks[i].page_start,chunks[i].page_end+1)}
        if not set(pages)<=available:errors.append('expected page outside expected evidence')
        if 'expected_pages' in case and (not isinstance(case['expected_pages'],list) or any(type(p) is not int for p in case['expected_pages']) or set(case['expected_pages'])!=available):errors.append('structured expected pages do not match source')
        if 'expected_source_document' in case:
            expected=[{'document_id':chunks[i].document_id,'document_number':chunks[i].document_number,'revision':chunks[i].revision,'sha256':chunks[i].source_sha256,'title':chunks[i].manual_title} for i in ids if i in chunks]
            if case['expected_source_document']!=expected:errors.append('structured source document mismatch')
    elif case.get('answerable') is False:
        if ids or case.get('expected_quote'):errors.append('negative record must not contain positive evidence or quotation')
    assertions=case.get('assertions',{})
    if not isinstance(assertions,dict):return errors+['assertions must be an object']
    if set(assertions)-set(KINDS)-{'quantities'}:errors.append('unsupported assertion kind')
    for key in KINDS:
        values=assertions.get(key,[])
        if not isinstance(values,list) or any(not isinstance(x,str) or not x.strip() or GRADER.search(x) for x in values):errors.append('invalid technical assertion list: '+key)
        elif key=='order' and values and len(values)<2:errors.append('order requires at least two steps')
    values=assertions.get('quantities',[])
    if not isinstance(values,list):errors.append('quantities must be a list')
    else:
        for q in values:
            if not isinstance(q,dict) or set(q)!={'value','unit'} or not isinstance(q.get('value'),str) or not re.fullmatch(NUMBER,q['value']) or not isinstance(q.get('unit'),str) or not q['unit'].strip():errors.append('quantity requires exact string value and unit')
            elif quantities(q['value']+' '+q['unit'])!=[(q['value'],q['unit'])]:errors.append('unsupported value/unit grammar')
    if case.get('answerable') is False and any(assertions.get(k) for k in (*KINDS,'quantities') if k!='prohibited'):errors.append('negative records cannot require technical assertions')
    return errors

def expected_obligations(case,chunks):
    rules={k:list(case.get('assertions',{}).get(k,[])) for k in KINDS}
    for field,kind in ANNOTATION_FIELDS.items():rules[kind]+=case.get(field,[])
    rules['quantities']=[(q['value'],q['unit']) for q in case.get('assertions',{}).get('quantities',[])]
    rules['quantities']+=list(zip(case.get('required_values',[]),case.get('required_units',[])))
    if not case['answerable']:return rules
    quote=case['expected_quote'];rules['required'].append(quote)
    rules['identifiers']+=IDENTIFIER.findall(quote)
    rules['quantities']+=quantities(quote)
    for ident in case['expected_chunk_ids']:
        c=chunks[ident]
        rules['warnings']+=[w for w in c.warnings if normalize(w).strip(':').casefold() not in ('warning','caution','note')]
        for paragraph in c.text.split('\n\n'):
            if contains(paragraph,quote):
                if CONDITION.search(paragraph):rules['qualifiers'].append(paragraph)
                if NEGATION.search(paragraph):rules['negations'].append(paragraph)
                if re.search(r'\b(?:dealer|qualified|trained)\b',paragraph,re.I):rules['escalation'].append(paragraph)
        # Source numbered steps must occur in order if the question's approved source is procedural.
        steps=[p for p in c.text.split('\n\n') if re.match(r'^\d+\.\s',p)]
        if len(steps)>1:rules['order']+=steps
    return {k:list(dict.fromkeys(v)) for k,v in rules.items()}

def grade(case,result,evidence,retrieved_ids,expected_chunks):
    checks={};details={};applicable={};rules=expected_obligations(case,expected_chunks)
    def check(name,ok,why='',applies=True):
        checks[name]=bool(ok);applicable[name]=bool(applies)
        if not ok:details[name]=why
    if not isinstance(result,dict) or result.get('status') not in STATUS:
        return {'passed':False,'checks':{'schema':False},'failures':{'schema':'malformed production response'},'applicable':{'schema':True},'route_mismatch':False}
    grounded=result['status']=='grounded'
    if not isinstance(result.get('answer'),str) or any(not isinstance(result.get(k),list) for k in ('steps','warnings','sources','claims')) or any(not isinstance(t,str) for k in ('steps','warnings') for t in result[k]):
        return {'passed':False,'checks':{'schema':False},'failures':{'schema':'malformed production fields'},'applicable':{'schema':True},'route_mismatch':False}
    body='\n'.join([result['answer']]+result['steps']);all_text=body+'\n'+'\n'.join(result['warnings'])
    check('grounding',grounded==case['answerable'],'grounded/refused status disagrees with label')
    from src.answering import REFUSAL
    refusal_clean=not grounded and result['answer']==REFUSAL and not result['steps'] and not result['warnings'] and not result['claims']
    check('unsupported_rejection',case['answerable'] or refusal_clean,'negative case emitted technical content',not case['answerable'])
    # An explicitly annotated warning may be delivered in the warning field.
    # Ordinary technical assertions still require answer/steps. Every emitted
    # field remains subject to claim, page and citation verification below.
    check('required',all(contains(body,x) or (x in rules['warnings'] and any(contains(w,x) for w in result['warnings'])) for x in rules['required']),'required technical assertion absent',bool(rules['required']))
    check('prohibited',not any(prohibited_present(all_text,x) for x in rules['prohibited']),'prohibited assertion emitted',bool(rules['prohibited']))
    for kind in ('identifiers','qualifiers','negations','escalation'):
        check(kind,all(contains(all_text,x) for x in rules[kind]),kind+' missing or changed',bool(rules[kind]))
    got=quantities(all_text)
    check('values',all(any(v==a for a,b in got) for v,u in rules['quantities']),'required numerical value missing',bool(rules['quantities']))
    check('units',all((v,u) in got for v,u in rules['quantities']),'required value/unit association missing; no conversions accepted',bool(rules['quantities']))
    ordered=normalize('\n'.join(result['steps']) if result['steps'] else result['answer']).casefold();cursor=0;order_ok=True
    for step in rules['order']:
        pos=ordered.find(normalize(step).casefold(),cursor)
        if pos<0:order_ok=False;break
        cursor=pos+len(normalize(step))
    check('procedural_order',order_ok,'source procedure omitted, changed or out of order',bool(rules['order']))
    check('warnings',all(contains(all_text,w) for w in rules['warnings']),'approved-source safety warning omitted',bool(rules['warnings']))
    byid={h.chunk.chunk_id:h.chunk for h in evidence};cited=set();document_ok=True;pages_ok=True;claim_ok=True
    for s in result['sources']:
        if not isinstance(s,dict):document_ok=False;pages_ok=False;continue
        c=byid.get(s.get('chunk_id'))
        if c is None or c.review_required:document_ok=False;pages_ok=False;continue
        cited.add(c.chunk_id)
        identity={'manual':c.manual_title,'manufacturer':c.manufacturer,'document_number':c.document_number,'revision':c.revision,'source_sha256':c.source_sha256,'models':list(c.models),'controllers':list(c.controllers),'applicability':c.applicability}
        document_ok &= all(s.get(k)==v for k,v in identity.items())
        if case.get('controller') and c.controllers:
            document_ok &= case['controller'] in c.controllers
        if case.get('expected_model'):
            document_ok &= case['expected_model'] in c.models
        pages_ok &= s.get('section')==c.section and s.get('pdf_page')==(str(c.page_start) if c.page_start==c.page_end else f'{c.page_start}\u2013{c.page_end}') and s.get('printed_page')==', '.join(c.printed_pages) and s.get('warning_pdf_pages')==sorted(set(c.warning_pages))
    check('citation_document',document_ok and (bool(cited) or not grounded),'citation document, hash, revision or applicability invalid')
    check('citation_page_chunk',pages_ok and (bool(cited) or not grounded),'citation page, section or chunk invalid')
    covered=set()
    for claim in result['claims']:
        if not isinstance(claim,dict):claim_ok=False;continue
        c=byid.get(claim.get('chunk_id'));text=claim.get('text');field=claim.get('field');pages=claim.get('pdf_pages')
        if c is None or c.chunk_id not in cited or c.review_required or not isinstance(text,str) or field not in ('answer','steps','warnings') or not isinstance(pages,list) or not pages or any(type(p) is not int for p in pages):claim_ok=False;continue
        allowed=set(range(c.page_start,c.page_end+1))
        supports=text in c.text
        if text in c.warnings:
            warning_locations={p for w,p in zip(c.warnings,c.warning_pages) if w==text}
            allowed=(allowed|warning_locations) if supports else warning_locations
            supports=True
        claim_ok &= supports and claim.get('source_sha256')==c.source_sha256 and set(pages)<=allowed
        covered.add((field,text))
    fields=[('answer',result['answer'])]+[(k,t) for k in ('steps','warnings') for t in result[k]]
    check('evidence_support',claim_ok and (not grounded or all(x in covered for x in fields)),'unattributed, altered or unsupported emitted field')
    # Per-claim number/unit support is evaluated within its actual cited source, not pooled evidence.
    numerical=True
    for cl in result['claims']:
        if not isinstance(cl,dict) or not isinstance(cl.get('text'),str):numerical=False;continue
        c=byid.get(cl.get('chunk_id'))
        if c is None:numerical=False;continue
        source=c.text+'\n'+'\n'.join(c.warnings)
        numerical &= all(q in quantities(source) for q in quantities(cl['text']))
    check('numerical_evidence',numerical,'emitted value/unit pair unsupported by its cited evidence',grounded)
    check('safety',checks['warnings'] and checks['escalation'] and checks['negations'] and checks['qualifiers'] and checks['prohibited'] and checks['evidence_support'] and (case['answerable'] or refusal_clean),'warning, qualification, negation, unsupported content or refusal failure')
    route=case['answerable'] and (not retrieved_ids or retrieved_ids[0] not in case['expected_chunk_ids'])
    return {'passed':all(checks.values()),'checks':checks,'failures':details,'applicable':applicable,'route_mismatch':bool(route),'route_mismatch_is_failure':bool(route and not all(checks.values())),'obligation_counts':{k:len(v) for k,v in rules.items()}}

def _worker(connection,root,mode):
    try:
        from src.store import validate_build
        from src.retrieval import HybridRetriever,SemanticIndex
        from src.benchmark import evaluate
        start=time.perf_counter();_,_,chunks=validate_build(root)
        r=HybridRetriever(chunks,SemanticIndex(root/'data/processed',root/'data/models/all-MiniLM-L6-v2') if mode!='bm25' else None)
        byid={c.chunk_id:c for c in chunks};connection.send({'ready':True,'cold_start_seconds':time.perf_counter()-start})
        while True:
            c=connection.recv()
            if c is None:break
            try:
                row=evaluate([c],r,mode,lambda case,result,evidence,ids:grade(case,result,evidence,ids,byid))['cases'][0]
                connection.send({'row':row})
            except Exception as exc:connection.send({'error':type(exc).__name__+': '+str(exc)})
    except Exception as exc:
        try:connection.send({'error':type(exc).__name__+': '+str(exc)})
        except (BrokenPipeError,OSError):pass
    finally:connection.close()

def summarize(rows):
    passed=sum(r.get('evaluation',{}).get('passed',False) for r in rows)
    positives=[r for r in rows if r.get('answerable')]
    times=[r['latency_ms'] for r in rows if 'latency_ms' in r]
    failures=Counter(k for r in rows for k,v in r.get('evaluation',{}).get('checks',{}).items() if not v)
    applicable=Counter(k for r in rows for k,v in r.get('evaluation',{}).get('applicable',{}).items() if v)
    return {'cases':len(rows),'passed':passed,'failed':len(rows)-passed,'answerable':len(positives),'deterministic_answer_accuracy':sum(r.get('evaluation',{}).get('passed',False) for r in positives)/len(positives) if positives else None,'failures_by_check':dict(failures),'applicable_cases_by_check':dict(applicable),'route_mismatches':sum(r.get('evaluation',{}).get('route_mismatch',False) for r in rows),'route_mismatches_with_failure':sum(r.get('evaluation',{}).get('route_mismatch_is_failure',False) for r in rows),'errors':sum('error' in r for r in rows),'timeouts':sum(r.get('timeout',False) for r in rows),'median_ms':statistics.median(times) if times else None,'p95_ms':sorted(times)[math.ceil(.95*len(times))-1] if times else None}

def save_report(root,report):
    suffix='_'+report['report_tag'] if report.get('report_tag') else ''
    (root/f'exports/gold_standard_answer_results{suffix}.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# Live gold-standard answer evaluation','',report['verdict'],'','The existing `src.benchmark` runner executes the production retrieval, safety-evidence and answering pipeline. There is no verified 150-case evaluator. This run uses existing benchmark records; selected split counts are reported below.','',f"Command: `{report['command']}`",'',f"Completed: {report['completed_at']}",'','| Split | Cases | Passed | Failed | Deterministic positive-answer accuracy |','|---|---:|---:|---:|---:|']
    for split,s in report.get('splits',{}).items():lines.append(f"| {split} | {s['cases']} | {s['passed']} | {s['failed']} | {s['deterministic_answer_accuracy']} |")
    lines+=['','## Aggregate measured results','', '```json',json.dumps(report.get('summary',{}),indent=2),'```','','## Failures','']
    for row in report.get('cases',[]):
        if not row.get('evaluation',{}).get('passed',False):lines.append(f"- {row['id']}: {row.get('error') or ', '.join(row['evaluation']['failures'])}")
    lines+=['','## Interpretation and limits','','- A route mismatch alone is diagnostic; it fails only alongside substantive checks. All positive checks must pass for deterministic answer accuracy. Negative refusals are counted separately.','- Legacy expected quotations remain unchanged. Grading also retains relevant source paragraph conditions/negation, numbered procedure order, and source warning metadata. No rationale, topic, metadata or grader instruction is treated as a technical assertion.','- Optional typed assertion fields support explicit prohibited statements, identifiers, value/unit pairs, qualifiers, negation, sequence, warnings and escalation. Current legacy cases do not provide a complete independent assertion rubric. Zero failures in a category with zero applicable cases means unmeasured, not verified.','- Normalization is NFC, whitespace collapse and a fixed map of typographic quotes/hyphens. Technical substring checks ignore letter case; numeric/unit pairs preserve unit case and exact values. No conversions, fuzzy grading, stemming, synonyms or LLM judge. Units and numbers are checked within the cited claim evidence.','- Evidence support covers every emitted answer, step and warning, plus document/revision/hash/applicability and page/chunk identity. It cannot establish every implicit semantic implication or detect every harmful statement in the approved manual.','- Safety results are bounded source-warning/condition/negation/escalation and negative-refusal checks. Independent service-technician review remains pending.','- This evaluator does not certify change history or authorize a release. Consult the release remediation report and freeze for code, annotation and split provenance. Exact/near-duplicate leakage checks run across the configured active splits before production evaluation.','- Per-case timeout terminates the worker process; subsequent cases use a fresh worker. Startup deadline is 60 seconds. Per-query latency is production retrieval plus answering; grading/startup are outside that timing. p95 uses the nearest-rank definition.','', '## Preflight and provenance','', '```json',json.dumps({k:v for k,v in report.items() if k not in ('cases','splits','summary')},indent=2),'```','']
    (root/f'docs/GOLD_STANDARD_ANSWER_EVALUATION{suffix}.md').write_text('\n'.join(lines),encoding='utf-8')

def run(root,split='all',mode='hybrid',case_timeout=30.,report_tag=''):
    from src.store import validate_build,code_fingerprint
    from src.benchmark import leakage
    if not math.isfinite(case_timeout) or case_timeout<=0:raise ValueError('case-timeout must be finite and positive')
    if report_tag and not re.fullmatch(r'[a-z0-9_]+',report_tag):raise ValueError('invalid report tag')
    split_names=SPLITS+('holdout_rc3',) if split=='holdout_rc3' else SPLITS
    report={'command':f'python -m src.benchmark --split {split} --mode {mode} --live-answers --case-timeout {case_timeout:g}','completed_at':datetime.now(timezone.utc).isoformat(),'verdict':'FAIL — NOT DEMO READY','schema_errors':[],'leakage':[],'cases':[],'splits':{}}
    report['report_tag']=report_tag
    if report_tag:report['command']+=' --report-tag '+report_tag
    try:
        _,build,chunks=validate_build(root);byid={c.chunk_id:c for c in chunks};splits={};seen=set()
        for name in split_names:
            splits[name]=[]
            for line_number,line in enumerate((root/f'benchmarks/{name}.jsonl').read_text(encoding='utf-8').splitlines(),1):
                if not line.strip():continue
                try:c=json.loads(line)
                except json.JSONDecodeError as exc:report['schema_errors'].append({'split':name,'line':line_number,'errors':[str(exc)]});continue
                errors=schema_errors(c,byid)
                if isinstance(c,dict) and isinstance(c.get('id'),str):
                    if c['id'] in seen:errors.append('duplicate case ID across splits')
                    seen.add(c['id'])
                if errors:report['schema_errors'].append({'split':name,'line':line_number,'errors':errors})
                else:splits[name].append(c)
            if not splits[name]:report['schema_errors'].append({'split':name,'errors':['empty valid split']})
        report['leakage']=[x for a,b in combinations(splits.values(),2) for x in leakage(a,b)]
        if report['schema_errors'] or report['leakage']:save_report(root,report);return 1
        paths=[root/'src/answer_evaluation.py',root/'src/benchmark.py',root/'data/processed/corpus_build.json',root/'data/raw/source_review.json',root/'data/raw/corpus_manifest.json']+[root/f'benchmarks/{s}.jsonl' for s in split_names]
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        report['hashes']={str(p.relative_to(root)):digest(p) for p in paths};report['production_code_fingerprint']=code_fingerprint(root);report['corpus_build']=build
        report['cold_start_seconds']=[];ctx=multiprocessing.get_context('spawn');proc=None;pipe=None
        try:
            for name in SPLITS if split=='all' else (split,):
                for c in splits[name]:
                    row={'id':c['id'],'split':name,'answerable':c['answerable']}
                    try:
                        if proc is None:
                            pipe,child=ctx.Pipe();proc=ctx.Process(target=_worker,args=(child,root,mode));proc.start();child.close()
                            if not pipe.poll(60):raise TimeoutError('worker startup deadline exceeded')
                            ready=pipe.recv()
                            if not ready.get('ready'):raise RuntimeError(ready.get('error','worker failed'))
                            report['cold_start_seconds'].append(ready['cold_start_seconds'])
                        pipe.send(c)
                        if not pipe.poll(case_timeout):raise TimeoutError('production case deadline exceeded')
                        outcome=pipe.recv()
                        if 'error' in outcome:row['error']=outcome['error']
                        else:row.update(outcome['row'])
                    except Exception as exc:
                        row['error']=type(exc).__name__+': '+str(exc);row['timeout']=isinstance(exc,TimeoutError)
                        if proc is not None:proc.terminate();proc.join(5);proc=None
                        if pipe is not None:pipe.close();pipe=None
                    report['cases'].append(row)
                report['splits'][name]=summarize([r for r in report['cases'] if r['split']==name])
                print(name,json.dumps(report['splits'][name]),flush=True)
        finally:
            if proc is not None:
                pipe.send(None);proc.join(5)
                if proc.is_alive():proc.terminate();proc.join(5)
            if pipe is not None:pipe.close()
        report['summary']=summarize(report['cases'])
        report['files_unchanged_during_evaluation']=all(digest(root/p)==d for p,d in report['hashes'].items())
        if not report['summary']['failed'] and report['files_unchanged_during_evaluation']:
            report['verdict']='PASS — SELECTED CASES ONLY; RELEASE NOT ASSESSED'
    except Exception as exc:report['preflight_error']=type(exc).__name__+': '+str(exc)
    report['completed_at']=datetime.now(timezone.utc).isoformat();save_report(root,report)
    return 1 if report['verdict'].startswith('FAIL') else 0
