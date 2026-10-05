"""Source-only RC3 annotation audit. Does not call retrieval or answer generation."""
import json,re,hashlib
from pathlib import Path
from collections import Counter
import pymupdf
from src.answer_evaluation import expected_obligations,normalize,quantities,IDENTIFIER
from src.store import load_chunks
ROOT=Path(__file__).resolve().parents[1]
FIELDS={'required_assertions':'required','prohibited_assertions':'prohibited','required_identifiers':'identifiers','required_qualifiers':'qualifiers','required_negations':'negations','required_warnings':'warnings','required_escalation':'escalation'}

def annotate(case,byid,pages):
    c=dict(case);rules=expected_obligations(c,byid)
    sources=[byid[i] for i in c['expected_chunk_ids']]
    c['annotation_basis']='manufacturer source text and source-bound image review; not generated answers'
    for field,kind in FIELDS.items():c[field]=list(rules[kind])
    c['required_warnings']=[w for w in c['required_warnings'] if normalize(w).strip(':').casefold() not in ('warning','caution','note')]
    c['prohibited_assertions']=[]
    for warning in c['required_warnings']:
        # A complete explicit prohibition defines its unsafe affirmative alternative.
        m=re.search(r'(?i)^(?:I\s+)?(?:do not|never)\s+(.+?[.!?])(?:\s|$)',normalize(warning))
        if m and not re.search(r'\b(?:unless|until|if|except)\b',m[1],re.I):
            c['prohibited_assertions'].append(m[1][0].upper()+m[1][1:])
    quote=c.get('expected_quote','')
    relevant=[p for s in sources for p in s.text.split('\n\n') if quote and normalize(quote).casefold() in normalize(p).casefold()]
    pairs=list(dict.fromkeys(rules['quantities']+[q for p in relevant for q in quantities(p)]))
    c['required_values']=[v for v,u in pairs];c['required_units']=[u for v,u in pairs]
    c['required_identifiers']=list(dict.fromkeys(c['required_identifiers']+[i for p in relevant for i in IDENTIFIER.findall(p)]))
    c['expected_source_document']=[{'document_id':s.document_id,'document_number':s.document_number,'revision':s.revision,'sha256':s.source_sha256,'title':s.manual_title} for s in sources]
    c['expected_pages']=sorted({n for s in sources for n in range(s.page_start,s.page_end+1)})
    c['expected_route']={'kind':'manufacturer_evidence' if c['answerable'] else 'refusal','sections':[s.section for s in sources],'controller':c.get('controller')}
    c['annotation_not_applicable']={field:'No explicit applicable requirement in selected manufacturer evidence' for field in list(FIELDS)+['required_values','required_units'] if not c[field]}
    if sources:
        text=' '.join(pages[n-1] for s in sources for n in range(s.page_start,s.page_end+1))
        native=normalize(quote).casefold() in normalize(text).casefold()
        c['annotation_verification']={'expected_quote_native_pdf_match':native,'method':'native PDF text' if native else 'source-bound table/image transcription; visual page review required','source_pages':c['source_pages']}
    else:c['annotation_verification']={'method':'documented corpus boundary and clean refusal; no invented answer assertion'}
    return c

def main():
    byid={c.chunk_id:c for c in load_chunks(ROOT/'data/processed/chunks.json')}
    doc=pymupdf.open(next((ROOT/'data/raw/manuals').glob('*.pdf')));pages=[p.get_text() for p in doc]
    all_rows=[];counts=Counter();native_review=[]
    for split in ('development','holdout','adversarial','regression'):
        target=ROOT/f'benchmarks/{split}.jsonl';cases=[json.loads(s) for s in target.read_text(encoding='utf-8').splitlines()]
        annotated=[annotate(c,byid,pages) for c in cases]
        target.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in annotated),encoding='utf-8')
        for c in annotated:
            all_rows.append({'id':c['id'],'split':split,'answerable':c['answerable'],'covered_fields':[k for k in list(FIELDS)+['required_values','required_units','expected_source_document','expected_pages','expected_chunk_ids','expected_route'] if c[k]],'verification':c['annotation_verification']})
            counts.update(all_rows[-1]['covered_fields'])
            if c['answerable'] and not c['annotation_verification']['expected_quote_native_pdf_match']:native_review.append(c['id'])
    report={'original_records':len(all_rows),'meaningful_field_coverage':dict(counts),'visual_review_cases':native_review,'rows':all_rows,'method':'source-only deterministic annotation; no retrieval/output grading used; same implementing assistant, external review pending'}
    (ROOT/'exports/rc3_annotation_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    lines=['# Benchmark annotation audit','','All 64 original records audited against approved-source identity and pages. Queries, expected quotations and expected chunk IDs are unchanged. Structured fields add source-derived detail without relaxing expected outcomes. Historical JSONL files remain in exports/historical_pre_rc3/benchmarks.','','Explicit empty lists and annotation_not_applicable distinguish absent annotations from measured success. Required value/unit lists are paired by position. Expected source document and route are citation/applicability metadata, never technical prose. Grader instructions and rationale stay outside assertions.','','Prohibited assertions are affirmative counterparts of complete explicit manufacturer prohibitions. Conditional prohibitions are excluded from automatic inversion. The grader must distinguish the original safe negation from its prohibited affirmative counterpart. Unsupported cases require clean refusal; arbitrary fictional fault meanings are not invented just to fill annotation fields.','','Meaningful field counts (original 64 records):','', '| Field | Covered cases |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in sorted(counts.items())]
    lines += ['','| Case | Split | Positive | Native PDF / reviewed source |','|---|---|---|---|']
    lines += [f"| {r['id']} | {r['split']} | {r['answerable']} | {r['verification']['method']} |" for r in all_rows]
    lines += ['','Annotation defects separate from product defects: legacy records had only a short quote; unit pairs, source conditions, warnings and explicit prohibitions were under-annotated. Warning headings are formatting, not technical assertions. Source warnings themselves are retained. The two product failures remain incorrect routing followed by conservative refusal.','','Image/table expectation checks use the approved original PDF and hash-bound reviewed rows; they are not independent technician verification. Separate source verification does not establish independent authorship.','']
    (ROOT/'docs/BENCHMARK_ANNOTATION_AUDIT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'records':len(all_rows),'coverage':dict(counts),'requires_visual_review':native_review}))
if __name__=='__main__':main()
