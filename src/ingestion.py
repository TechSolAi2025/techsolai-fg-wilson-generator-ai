from __future__ import annotations
import json, re
from pathlib import Path
from src.manifest import file_sha256

def extract_pdf(pdf_path: Path, output_path: Path, meta: dict|None=None) -> list[dict]:
    import fitz
    pages=[]; digest=file_sha256(pdf_path)
    try:
        with fitz.open(pdf_path) as doc:
            if not doc.is_pdf or doc.needs_pass or doc.is_repaired or not len(doc): raise ValueError('Invalid PDF')
            for number,page in enumerate(doc,1):
                raw=page.get_text('text').replace('\x00','').strip()
                blocks=[]
                for b in page.get_text('dict')['blocks']:
                    if b['type']!=0: continue
                    lines=[]; sizes=[]; bold=False
                    for line in b['lines']:
                        lines.append(''.join(s['text'] for s in line['spans']))
                        sizes.extend(s['size'] for s in line['spans']); bold |= any(s['flags']&16 for s in line['spans'])
                    blocks.append({'bbox':list(b['bbox']),'text':'\n'.join(lines).strip(),'font_size':max(sizes,default=0),'bold':bool(bold)})
                tables=[]; table_error=None
                try:
                    for table in page.find_tables().tables:
                        tables.append({'bbox':list(table.bbox),'rows':table.extract()})
                except Exception as exc: table_error=type(exc).__name__
                footer=[b['text'] for b in blocks if b['bbox'][1]>page.rect.height*.90]
                printed=next((m.group(1) for s in footer if (m:=re.fullmatch(r'\s*(\d+)\s*',s))),None)
                issues=[]
                if len(raw)<80: issues.append('weak_text')
                if '\ufffd' in raw: issues.append('replacement_characters')
                if table_error: issues.append('table_detection_error')
                if page.get_images(): issues.append('image_content_requires_visual_review')
                pages.append({'page':number,'printed_page':printed,'text':raw,'blocks':blocks,'tables':tables,'needs_ocr_review':bool(issues),'quality_issues':issues,'image_count':len(page.get_images()),'width':page.rect.width,'height':page.rect.height,'document_id':(meta or {}).get('id',pdf_path.stem),'source_sha256':digest,'filename':pdf_path.name})
    except Exception as exc: raise ValueError(f'Malformed/corrupt PDF: {pdf_path.name}: {exc}') from exc
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
    return pages
