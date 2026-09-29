from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ALLOWED_MANUFACTURERS = {'FG Wilson'}
REQUIRED = {'id','filename','sha256','title','manufacturer','models','applicability','controllers','document_number','revision','language','page_count','approved'}

def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def load_and_validate(path: Path, manuals_dir: Path, require_documents: bool=True) -> dict:
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('schema_version')!=2: raise ValueError('Unsupported manifest schema')
        docs=data.get('documents')
        if not isinstance(docs,list) or (require_documents and not docs): raise ValueError('No approved manufacturer documents registered')
        ids, hashes, files=set(),set(),set()
        for d in docs:
            if not isinstance(d,dict) or REQUIRED-set(d): raise ValueError('Malformed manifest document: required fields missing')
            for key in ('id','filename','title','manufacturer','applicability','document_number','revision','language'):
                if not isinstance(d[key],str) or not d[key].strip(): raise ValueError(f'Invalid {key}')
            if d['manufacturer'] not in ALLOWED_MANUFACTURERS: raise ValueError('Non-FG-Wilson source rejected')
            if d['approved'] is not True: raise ValueError('Unapproved document rejected')
            if not re.fullmatch(r'[a-z0-9_-]+',d['id']): raise ValueError('Invalid document id')
            for key in ('models','controllers'):
                if not isinstance(d[key],list) or any(not isinstance(x,str) or not x.strip() for x in d[key]): raise ValueError(f'Invalid {key}')
            if type(d['page_count']) is not int or d['page_count']<1: raise ValueError('Invalid page count')
            if not isinstance(d['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',d['sha256']): raise ValueError('Invalid SHA-256')
            source=(manuals_dir/d['filename']).resolve()
            if not source.is_relative_to(manuals_dir.resolve()) or source.suffix.lower()!='.pdf': raise ValueError('Invalid source path')
            if d['id'] in ids or d['sha256'] in hashes or str(source).lower() in files: raise ValueError('Duplicate document')
            ids.add(d['id']); hashes.add(d['sha256']); files.add(str(source).lower())
            if not source.is_file(): raise ValueError(f'Missing manual: {d["filename"]}')
            if file_sha256(source)!=d['sha256']: raise ValueError(f'SHA-256 mismatch: {d["filename"]}')
            import fitz
            try:
                with fitz.open(source) as pdf:
                    if not pdf.is_pdf or pdf.needs_pass or pdf.is_repaired or len(pdf)!=d['page_count']: raise ValueError('Corrupt, encrypted, repaired or page-count mismatch PDF')
                    cover=' '.join(pdf[0].get_text().split()).lower()
                    if 'fg wilson' not in cover or ' '.join(d['title'].split()).lower() not in cover: raise ValueError('Source cover does not match FG Wilson manual identity')
                    for page in pdf: page.get_text()
            except Exception as exc: raise ValueError(f'Corrupt or unreadable PDF: {source.name}: {exc}') from exc
        actual={str(p.resolve()).lower() for p in manuals_dir.rglob('*') if p.is_file() and p.suffix.lower()=='.pdf'}
        if actual!=files: raise ValueError('Unregistered PDF files in corpus')
        return data
    except (ValueError,TypeError,KeyError,OSError) as exc:
        raise ValueError(f'Invalid corpus manifest: {exc}') from exc
