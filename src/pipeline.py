from __future__ import annotations
import argparse,json,time
from collections import Counter
from pathlib import Path
from src.manifest import load_and_validate,file_sha256
from src.ingestion import extract_pdf
from src.chunking import chunk_pages
from src.store import save_chunks,SCHEMA_VERSION,code_fingerprint,manifest_fingerprint
ROOT=Path(__file__).resolve().parents[1]

def build(root=ROOT,semantic=True):
    initial_code=code_fingerprint(root)
    start=time.perf_counter(); raw=root/'data/raw'; processed=root/'data/processed'; processed.mkdir(parents=True,exist_ok=True)
    # Remove only the completion marker before building; incomplete builds cannot start the app.
    (processed/'corpus_build.json').unlink(missing_ok=True)
    manifest=load_and_validate(raw/'corpus_manifest.json',raw/'manuals')
    review=json.loads((raw/'source_review.json').read_text(encoding='utf-8'))
    chunks=[]; reports=[]; artifacts=[]
    for meta in manifest['documents']:
        if review['source_sha256']!=meta['sha256']: raise ValueError('Source review SHA-256 mismatch')
        filename=f'{meta["id"]}_pages.json'
        pages=extract_pdf(raw/'manuals'/meta['filename'],processed/filename,meta)
        for p in pages:
            # Footer contains duplicate text glyphs; printed page is independently preserved.
            if p['page']>1:
                for b in p['blocks']:
                    if b['bbox'][1]>p['height']*.95:
                        lines=b['text'].splitlines()
                        if str(p['page'])*2 in lines: p['printed_page']=str(p['page'])
            image_areas=[]
            # Visually audited image-only tables are explicitly recorded even when text length exceeds threshold.
            if str(p['page']) in review.get('image_tables',{}):
                p['quality_issues'].append('image_table_missing_from_text_layer')
                p['review_resolution']='hash-bound visual transcription'; p['reviewed_tables']=review['image_tables'][str(p['page'])]
            elif p['page'] in review['non_content_pages']: p['review_resolution']='visually inspected non-answer content'
            else: p['review_resolution']='text and page layout inspected; see section exclusions'
            p['needs_ocr_review']=bool(p['quality_issues'])
        (processed/filename).write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        artifacts.append(filename); chunks.extend(chunk_pages(pages,meta,review=review))
        reports.extend({'page':p['page'],'printed_page':p['printed_page'],'characters':len(p['text']),'images':p['image_count'],'tables':len(p['tables']),'issues':p['quality_issues'],'resolution':p['review_resolution']} for p in pages)
    save_chunks(chunks,processed/'chunks.json'); artifacts.append('chunks.json')
    (processed/'extraction_quality.json').write_text(json.dumps(reports,indent=2),encoding='utf-8'); artifacts.append('extraction_quality.json')
    stats={'total':len(chunks),'categories':dict(Counter(c.category for c in chunks)),'quarantined':sum(c.review_required for c in chunks),'over_2600_characters':sum(len(c.text)>2600 for c in chunks),'max_characters':max(map(lambda c:len(c.text),chunks)),'unique_ids':len({c.chunk_id for c in chunks})}
    (processed/'chunk_statistics.json').write_text(json.dumps(stats,indent=2),encoding='utf-8'); artifacts.append('chunk_statistics.json')
    model_hash=None
    if semantic:
        from src.retrieval import SemanticIndex,model_fingerprint
        SemanticIndex(processed,root/'data/models/all-MiniLM-L6-v2',build=True,chunks=chunks)
        artifacts+=['vectors.faiss','vector_mapping.json']; model_hash=model_fingerprint(root/'data/models/all-MiniLM-L6-v2')
    build={'schema_version':SCHEMA_VERSION,'manifest_fingerprint':manifest_fingerprint(manifest),'code_fingerprint':initial_code,'source_review_sha256':file_sha256(raw/'source_review.json'),'chunk_count':len(chunks),'page_count':len(reports),'semantic':semantic,'embedding_model':'sentence-transformers/all-MiniLM-L6-v2' if semantic else None,'model_fingerprint':model_hash,'fusion':'Reciprocal rank fusion k=60; +0.04 per exact identifier; eligible candidates only','artifacts':{f:file_sha256(processed/f) for f in artifacts},'build_seconds':time.perf_counter()-start}
    if code_fingerprint(root)!=initial_code: raise ValueError('Source code changed during build; rebuild required')
    (processed/'corpus_build.json').write_text(json.dumps(build,indent=2),encoding='utf-8')
    print(json.dumps({'pages':len(reports),'chunks':stats,'build_seconds':build['build_seconds']}))
    return build

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['validate-manifest','build']); p.add_argument('--lexical-only',action='store_true'); a=p.parse_args()
    if a.command=='validate-manifest': load_and_validate(ROOT/'data/raw/corpus_manifest.json',ROOT/'data/raw/manuals'); print('Manifest PASS')
    else: build(semantic=not a.lexical_only)
if __name__=='__main__': main()
