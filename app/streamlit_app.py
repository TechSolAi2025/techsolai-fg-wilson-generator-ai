from pathlib import Path
import sys,time
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import streamlit as st
from src.answering import answer
from src.retrieval import HybridRetriever,SemanticIndex
from src.store import safe_load

st.set_page_config(page_title='TechSolAi | FG Wilson',page_icon='⚙️',layout='wide')
st.title('TechSolAi · FG Wilson')
st.caption('FG Wilson Generator Operations, Preventive Maintenance & Basic Fault-Finding AI')
state=safe_load(ROOT)
with st.sidebar:
    st.header('Manufacturer evidence')
    if state['ok']:
        d=state['manifest']['documents'][0]
        st.success('Corpus integrity verified')
        st.write(d['title']); st.caption(d['document_number']+' · '+d['revision'])
        st.write(d['applicability'])
        st.metric('Source pages',state['build']['page_count'])
        st.caption('Individual generator models are not established by this family manual.')
        with st.expander('Source identity'):
            st.json({k:d[k] for k in ('filename','sha256','language','approved','approval_basis')})
    else:
        st.error('Corpus unavailable')
        st.caption(state['error'])

@st.cache_resource
def retriever(build_identity,semantic):
    # Revalidate immediately before constructing indexes; startup never trusts cached chunk files.
    checked=safe_load(ROOT)
    if not checked['ok']: raise ValueError(checked['error'])
    vector=SemanticIndex(ROOT/'data/processed',ROOT/'data/models/all-MiniLM-L6-v2') if semantic else None
    return HybridRetriever(checked['chunks'],vector)

if not state['ok']:
    st.error('Technical answering is disabled until the corpus and build pass validation.')
    st.text_input('Search manufacturer guidance',disabled=True)
    st.button('Search evidence',disabled=True)
else:
    st.info('Operator guidance and qualified-technician maintenance reference. Confirm the fitted equipment; model-specific service diagnosis requires additional manuals.')
    st.caption('Supports safety, pre-start checks, operation, descriptive PowerWizard and DeepSea indications, routine maintenance, service intervals and cited basic symptom/remedy guidance. Numerical fault-code dictionaries, SPN/FMI diagnostics, controller internal service, wiring-level diagnosis, engine overhaul, component disassembly and unstated model-specific repair specifications require additional approved manuals.')
    left,right=st.columns([2,1])
    with left: query=st.text_input('Fault, symptom, inspection or maintenance question',placeholder='Describe the observed condition or the task')
    with right: controller=st.selectbox('Fitted controller',['Not specified / general guidance']+d['controllers'])
    if st.button('Search evidence',type='primary'):
        selected=None if controller.startswith('Not specified') else controller
        try:
            t=time.perf_counter()
            r=retriever(state['build']['code_fingerprint']+state['build']['artifacts']['chunks.json'],state['build']['semantic'])
            hits=r.search(query,5,controller=selected)
            grounded_query=query+(' '+selected if selected else '')
            result=answer(grounded_query,hits+(r.safety_evidence(hits[0]) if hits else []))
            st.subheader('Answer'); st.write(result['answer'])
            if result.get('reason'): st.caption(result['reason'])
            if result.get('qualified_service'): st.warning('This evidence includes work reserved for trained personnel or referral to the dealer. Check the cited scope before acting.')
            st.subheader('Manufacturer procedure')
            for step in result['steps']: st.text(step)
            if not result['steps']: st.caption('No supported procedural sequence returned.')
            st.subheader('Warnings / Cautions')
            for warning in result['warnings']: st.warning(warning)
            st.subheader('Source')
            for source in result['sources']:
                st.write(source['manual']+' · '+source['revision'])
                st.caption(f"{source['section']} | PDF {source['pdf_page']} | Printed {source['printed_page']} | {source['chunk_id']}")
                st.caption(source['applicability'])
                if source['warning_pdf_pages']: st.caption('Inherited safety context: PDF pages '+', '.join(map(str,source['warning_pdf_pages'])))
            with st.expander('Retrieved manufacturer evidence'):
                for hit in hits:
                    st.caption(hit.chunk.section+' · '+hit.chunk.chunk_id)
                    st.text(hit.chunk.text)
            st.caption(f'Response time: {time.perf_counter()-t:.2f} s')
        except Exception as exc:
            st.error('Technical answering disabled: corpus or retrieval could not be loaded.')
            st.caption(str(exc))
st.divider()
st.caption('Source-limited reference · FG Wilson P Series and PRO rental series · Consult the supplying dealer for equipment-specific service documents.')
