from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    manual_title: str
    manufacturer: str
    models: tuple[str,...]
    section: str
    page_start: int
    page_end: int
    text: str
    category: str='general'
    fault_codes: tuple[str,...]=()
    hazards: tuple[str,...]=()
    revision: str=''
    source_sha256: str=''
    requires_qualified_service: bool=False
    printed_pages: tuple[str,...]=()
    controllers: tuple[str,...]=()
    applicability: str=''
    document_number: str=''
    identifiers: tuple[str,...]=()
    warnings: tuple[str,...]=()
    warning_pages: tuple[int,...]=()
    review_required: bool=False
    recovery_of: str=''
    extraction_method: str='native PDF text/table'
    table: dict=field(default_factory=dict)
    def to_dict(self)->dict[str,Any]: return asdict(self)
    @classmethod
    def from_dict(cls,value):
        value=dict(value)
        for k in ('models','fault_codes','hazards','printed_pages','controllers','identifiers','warnings','warning_pages'): value[k]=tuple(value.get(k,()))
        c=cls(**value)
        if c.manufacturer!='FG Wilson' or not c.text.strip() or c.page_start<1 or c.page_end<c.page_start: raise ValueError('Invalid chunk schema')
        return c

@dataclass
class SearchHit:
    chunk: Chunk
    score: float
    reasons: list[str]=field(default_factory=list)
