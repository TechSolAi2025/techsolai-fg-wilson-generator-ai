from __future__ import annotations
import hashlib, json
from pathlib import Path
from src.models import Chunk
from src.manifest import load_and_validate, file_sha256
SCHEMA_VERSION=3

def code_fingerprint(root:Path)->str:
    h=hashlib.sha256()
    for name in ('models.py','identifiers.py','manifest.py','ingestion.py','chunking.py','table_context.py','retrieval.py','store.py','pipeline.py','safety.py','answering.py'):
        h.update(name.encode()); h.update((root/'src'/name).read_bytes())
    return h.hexdigest()

def manifest_fingerprint(manifest):
    return hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def save_chunks(chunks:list[Chunk],path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps([c.to_dict() for c in chunks],ensure_ascii=False,indent=2),encoding='utf-8')

def load_chunks(path:Path)->list[Chunk]:
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,list) or not data: raise ValueError('Empty or malformed chunks')
    chunks=[Chunk.from_dict(x) for x in data]
    if len({c.chunk_id for c in chunks})!=len(chunks): raise ValueError('Duplicate chunk IDs')
    return chunks

def validate_build(root:Path):
    manifest=load_and_validate(root/'data/raw/corpus_manifest.json',root/'data/raw/manuals')
    processed=root/'data/processed'
    build=json.loads((processed/'corpus_build.json').read_text(encoding='utf-8'))
    if build.get('schema_version')!=SCHEMA_VERSION or build.get('manifest_fingerprint')!=manifest_fingerprint(manifest) or build.get('code_fingerprint')!=code_fingerprint(root): raise ValueError('Stale/incompatible corpus build; rebuild required')
    artifacts=build.get('artifacts',{})
    if 'chunks.json' not in artifacts: raise ValueError('Missing chunk integrity metadata')
    for name,digest in artifacts.items():
        p=(processed/name).resolve()
        if not p.is_relative_to(processed.resolve()) or not p.is_file() or file_sha256(p)!=digest: raise ValueError(f'Stale/missing artifact: {name}')
    if build.get('source_review_sha256')!=file_sha256(root/'data/raw/source_review.json'): raise ValueError('Stale source review')
    if build.get('semantic'):
        from src.retrieval import model_fingerprint
        if build.get('model_fingerprint')!=model_fingerprint(root/'data/models/all-MiniLM-L6-v2'): raise ValueError('Stale embedding model')
    chunks=load_chunks(processed/'chunks.json')
    if len(chunks)!=build.get('chunk_count'): raise ValueError('Chunk count mismatch')
    docs={d['id']:d for d in manifest['documents']}
    for c in chunks:
        d=docs.get(c.document_id)
        if not d or c.source_sha256!=d['sha256'] or c.manual_title!=d['title'] or c.revision!=d['revision'] or c.page_end>d['page_count'] or c.applicability!=d['applicability'] or tuple(c.models)!=tuple(d['models']): raise ValueError('Chunk source identity mismatch')
    if build.get('semantic'):
        mapping=json.loads((processed/'vector_mapping.json').read_text(encoding='utf-8'))
        from src.safety import document_block_reason
        if any(type(i) is not int or i<0 or i>=len(chunks) or chunks[i].review_required or document_block_reason(chunks[i].text) for i in mapping): raise ValueError('Excluded or invalid FAISS mapping')
    return manifest,build,chunks

def safe_load(root:Path):
    try:
        manifest,build,chunks=validate_build(root)
        return {'ok':True,'manifest':manifest,'build':build,'chunks':chunks,'error':None}
    except Exception as exc:
        return {'ok':False,'manifest':None,'build':None,'chunks':[],'error':str(exc)}
