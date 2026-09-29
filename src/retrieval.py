from __future__ import annotations
import json, re, unicodedata, math
from collections import Counter
from src.identifiers import normalize_identifier
from collections import defaultdict
from difflib import get_close_matches
from pathlib import Path
from src.models import Chunk,SearchHit
from src.safety import query_block_reason,document_block_reason

STOP=set('a an the is are was were be been it its to of for from in on with and or my i me you your please what how when where why can do does did should would could will this that as at about tell explain generator set fg wilson find guidance manufacturer describe information need know instructions according manual concerning show advise observed'.split())
TOKEN=re.compile(r'[a-z0-9]+(?:[.+/-][a-z0-9]+)*\+?',re.I)
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).lower()).strip()
def tokens(s): return [x for x in TOKEN.findall(norm(s)) if x not in STOP]

def query_tokens(s):
    # A bounded leading request frame is not technical evidence. Keep the
    # subject, conditions, numbers and all unmatched words. Document tokens
    # remain unchanged, including substantive uses of "precautions".
    s=re.sub(r'^\s*(?:please\s+)?(?:show|list|explain|describe)\s+(?:the\s+)?(?:precautions|guidance|instructions)\s+(?:for|about|concerning)\s+', '', s, flags=re.I)
    if re.match(r'^\s*(?:please\s+)?(?:list|summarize)\s+',s,re.I):
        s=re.sub(r'^\s*(?:please\s+)?(?:list|summarize)\s+(?:(?:the|all|complete)\s+)*','',s,flags=re.I)
        s=re.sub(r'\s+table(?:\s+rows)?[.!?]?\s*(?=$)','',s,flags=re.I)
    return tokens(s)
def model_fingerprint(path):
    from src.manifest import file_sha256
    import hashlib
    files=sorted(p for p in path.rglob('*') if p.is_file())
    if not files: raise ValueError('Missing embedding model')
    return hashlib.sha256(''.join(str(p.relative_to(path))+file_sha256(p) for p in files).encode()).hexdigest()

class SemanticIndex:
    def __init__(self,folder:Path,model_dir:Path,build=False,chunks=None):
        import faiss,torch
        torch.set_num_threads(2)
        from sentence_transformers import SentenceTransformer
        self.model=SentenceTransformer(str(model_dir.resolve()),local_files_only=True,device='cpu')
        self.model.max_seq_length=256
        if build:
            texts=[]; self.mapping=[]
            for i,c in enumerate(chunks):
                if c.review_required or c.table.get('kind')=='obsolete' or document_block_reason(c.text+' '+' '.join(c.warnings)): continue
                words=c.text.split()
                for start in range(0,len(words),120):
                    texts.append(c.section+'\n'+' '.join(words[start:start+160])); self.mapping.append(i)
            vectors=self.model.encode(texts,normalize_embeddings=True,show_progress_bar=False,convert_to_numpy=True).astype('float32')
            self.index=faiss.IndexFlatIP(vectors.shape[1]); self.index.add(vectors)
            faiss.write_index(self.index,str(folder/'vectors.faiss'))
            (folder/'vector_mapping.json').write_text(json.dumps(self.mapping),encoding='utf-8')
        else:
            self.mapping=json.loads((folder/'vector_mapping.json').read_text(encoding='utf-8'))
            self.index=faiss.read_index(str(folder/'vectors.faiss'))
            if self.index.ntotal!=len(self.mapping) or self.index.d!=384: raise ValueError('Incompatible FAISS index')
    def scores(self,query,n):
        v=self.model.encode([query],normalize_embeddings=True,convert_to_numpy=True).astype('float32')
        scores,indices=self.index.search(v,self.index.ntotal)
        result=[-1.]*n
        for score,index in zip(scores[0],indices[0]):
            if index>=0: result[self.mapping[index]]=max(result[self.mapping[index]],float(score))
        return result

class HybridRetriever:
    def __init__(self,chunks:list[Chunk],semantic:SemanticIndex|None=None):
        from rank_bm25 import BM25Okapi
        self.chunks=chunks; self.semantic=semantic
        self.byid={c.chunk_id:c for c in chunks}
        self.docs=[tokens(c.section+' '+c.text) for c in chunks]
        self.active=[i for i,c in enumerate(chunks) if self._eligible(c,None,None)]
        self.bm25=BM25Okapi([self.docs[i] for i in self.active]) if self.active else None
        self.vocab=sorted({x for i in self.active for x in self.docs[i]})
        self.df=Counter(t for i in self.active for t in set(self.docs[i]))
        self.exact=defaultdict(set)
        for i,c in enumerate(chunks):
            if i not in self.active: continue
            for value in (*c.identifiers,*c.fault_codes,*c.controllers,*c.models): self.exact[normalize_identifier(value)].add(i)
        self.controllers=sorted({x for c in chunks for x in c.controllers},key=len,reverse=True)
    def _lexical_scores(self,terms):
        scores=[0.]*len(self.chunks)
        if self.bm25:
            for i,value in zip(self.active,self.bm25.get_scores(terms)):scores[i]=float(value)
        return scores
    def _bm25(self,query):return self._lexical_scores(tokens(query))
    def _coverage(self,terms,document):
        terms=set(terms);present=set(document)
        weights={t:math.log(1+(len(self.active)+1)/(1+self.df[t])) for t in terms}
        return sum(v for t,v in weights.items() if t in present)/max(1e-12,sum(weights.values()))
    def exact_lookup(self,identifier,model=None,controller=None):
        return [SearchHit(self.chunks[i],1000.,['deterministic exact identifier']) for i in sorted(self.exact.get(normalize_identifier(identifier),())) if self._eligible(self.chunks[i],model,controller)]
    def _eligible(self,c,model,controller):
        return not c.review_required and c.table.get('kind')!='obsolete' and not document_block_reason(c.text+' '+' '.join(c.warnings)) and (not model or norm(model) in {norm(m) for m in c.models}) and (not controller or not c.controllers or norm(controller) in {norm(x) for x in c.controllers})
    def search(self,query,k=5,model=None,controller=None,mode='hybrid'):
        if query_block_reason(query) or not self.chunks or not tokens(query): return []
        if mode not in ('bm25','semantic','hybrid'): raise ValueError('Unknown retrieval mode')
        if mode=='semantic' and self.semantic is None: raise ValueError('Semantic index unavailable')
        q=norm(query)
        mentioned=[x for x in self.controllers if re.search(r'(?<![\w.])'+re.escape(norm(x))+r'(?![\w.+])',q)]
        if controller and mentioned and norm(controller) not in {norm(x) for x in mentioned}: return []
        if len(mentioned)>1: return []
        controller=controller or (mentioned[0] if mentioned else None)
        if controller and norm(controller) not in {norm(x) for x in self.controllers}: return []
        # Unregistered individual product/controller IDs are never inferred from a family manual.
        for ident in re.findall(r'\b(?:p\d+[a-z0-9-]*|dse\s*\d+|fg\s*\d+|powerwizard\s*\d+(?:\.\d+)?\+?)\b',q):
            if normalize_identifier(ident) not in self.exact: return []
        code=re.search(r'\b(?:fault\s*(?:code)?|alarm\s+code|spn|fmi)\s*[:#]?\s*(\d+)\b',q)
        if code and norm(code[1]) not in self.exact: return []
        qt=query_tokens(query); corrected=[]
        for t in qt:
            if t not in self.vocab and t.isalpha() and len(t)>4:
                matches=get_close_matches(t,self.vocab,n=1,cutoff=.84); corrected.append(matches[0] if matches else t)
            else: corrected.append(t)
        lexical=self._lexical_scores(corrected); vector=self.semantic.scores(query,len(self.chunks)) if self.semantic and mode!='bm25' else None
        eligible=[i for i,c in enumerate(self.chunks) if self._eligible(c,model,controller)]
        lexrank={i:r+1 for r,i in enumerate(sorted(eligible,key=lambda i:(-lexical[i],self.chunks[i].chunk_id)))}
        vecrank={i:r+1 for r,i in enumerate(sorted(eligible,key=lambda i:(-vector[i],self.chunks[i].chunk_id)))} if vector else {}
        requested=[key for key in self.exact if key and re.search(r'(?<![\w.])'+re.escape(key)+r'(?![\w.+])',normalize_identifier(query))]
        hits=[]
        for i in eligible:
            overlap=self._coverage(corrected,self.docs[i])
            if lexical[i]<=0 and (not vector or vector[i]<.5): continue
            score=(1/(60+lexrank[i]) if mode!='semantic' else 0)+(1/(60+vecrank[i]) if vector else 0)
            # A controller label can also be an ordinary word. Its exact-match
            # contribution is meaningful only with explicit controller context.
            # Keep direct exact_lookup available; do not infer a fitted controller.
            exact_count=sum(i in self.exact[key] for key in requested) if controller or not self.chunks[i].controllers else 0
            if self.chunks[i].table.get('role')=='control' and not set(qt)&{'button','buttons','key','keys','press','pushbutton','pushbuttons'}:
                exact_count=0
            if exact_count: score+=.04*exact_count
            # Universal section specificity: no query-specific or benchmark-specific routing.
            subject=self.chunks[i].section
            fault=re.search(r'(?ms)^Fault:\s*(.+?)\nSymptom:',self.chunks[i].text)
            if fault:subject=fault[1]
            title_coverage=self._coverage(corrected,tokens(subject))
            score+=.008*title_coverage
            # Prefer a focused section over a broader heading containing the same
            # topic words. Strip numbering, never technical words or identifiers.
            title_terms={t for t in tokens(subject) if not re.fullmatch(r'[\d.]+',t)}
            title_precision=len(title_terms & set(corrected))/max(1,len(title_terms))
            if overlap>=.55:score+=.008*title_coverage*title_precision
            reasons=[f'BM25={lexical[i]:.5f}',f'coverage={overlap:.5f}']
            if vector: reasons.append(f'cosine={vector[i]:.5f}')
            if exact_count: reasons.append('deterministic exact identifier')
            hits.append(SearchHit(self.chunks[i],score,reasons))
        selected=sorted(hits,key=lambda h:(-h.score,h.chunk.chunk_id))[:k]
        if selected and selected[0].chunk.table:
            from src.table_context import table_selection
            selection=table_selection(query,selected[0].chunk,self.byid,controller)
            if selection and not selection.get('error'):
                selected[0].reasons.append('table hazards='+','.join(sorted({h for c in selection['rows'] for h in c.hazards})))
                seen={h.chunk.chunk_id for h in selected}
                for c in selection['members']:
                    if c.chunk_id not in seen:
                        selected.append(SearchHit(c,0.,['connected source table context']))
                        seen.add(c.chunk_id)
        return selected

    def safety_evidence(self,hit):
        if not hit: return []
        scores=self._bm25(hit.chunk.section+' '+hit.chunk.text[:500])
        hazards=set(hit.chunk.hazards)
        for reason in hit.reasons:
            if reason.startswith('table hazards='):hazards.update(filter(None,reason.split('=',1)[1].split(',')))
        candidates=[i for i,c in enumerate(self.chunks) if c.section.startswith('2.') and self._eligible(c,None,None) and set(c.hazards)&hazards]
        selected=[]; uncovered=hazards
        for i in sorted(candidates,key=lambda i:(-scores[i],self.chunks[i].chunk_id)):
            covered=uncovered&set(self.chunks[i].hazards)
            if covered:
                selected.append(SearchHit(self.chunks[i],0.,['applicable safety context']))
                uncovered-=covered
        return selected
