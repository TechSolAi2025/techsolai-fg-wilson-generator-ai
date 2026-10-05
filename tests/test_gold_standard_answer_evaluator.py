"""Mutation tests of grading, plus live-pipeline integration (no mocked release verdict)."""
import copy
from dataclasses import replace
from pathlib import Path
import pytest
from src.models import Chunk,SearchHit
from src.answering import answer
from src.answer_evaluation import grade,schema_errors,normalize,contains,summarize,expected_obligations

@pytest.fixture
def sample():
    warning='Only a qualified technician may perform this work.'
    c=Chunk(chunk_id='source-a',document_id='manual-a',manual_title='Approved manual',manufacturer='FG Wilson',models=(),section='1.1 Pressure inspection',page_start=3,page_end=3,
        text='1.1 Pressure inspection\n\nKeep pressure below 12 kPa before opening. Never open while running.\n\n1. Stop the engine.\n\n2. Inspect the gauge.\n\n'+warning,
        revision='A',source_sha256='a'*64,printed_pages=('3',),document_number='ABC',warnings=(warning,),warning_pages=(3,),requires_qualified_service=True)
    case={'id':'sample','query':'pressure inspection','answerable':True,'expected_chunk_ids':['source-a'],'expected_quote':'12 kPa','source_pages':[3],'source_sha256':'a'*64}
    hits=[SearchHit(c,1)];result=answer(case['query'],hits)
    assert result['status']=='grounded'
    return case,c,hits,result

def score(sample):
    case,c,hits,result=sample
    return grade(case,result,hits,[h.chunk.chunk_id for h in hits],{c.chunk_id:c})

def test_actual_production_answer_passes(sample):assert score(sample)['passed']

@pytest.mark.parametrize('key,value',[
    ('answerable','true'),('expected_chunk_ids','source-a'),('expected_chunk_ids',[]),
    ('expected_quote','Grader instructions: award points'),('source_pages',[True]),
    ('source_pages',[4]),('source_sha256','b'*64),('query',''),('unexpected_field',1),
    ('assertions',{'made_up':['x']}),('assertions',{'required':'x'}),
    ('assertions',{'quantities':[{'value':12,'unit':'kPa'}]}),
    ('assertions',{'quantities':[{'value':'12','unit':'unknown-unit'}]}),
    ('assertions',{'order':['one step']})])
def test_bad_records_rejected(sample,key,value):
    case,c,_,_=sample;case[key]=value
    assert schema_errors(case,{c.chunk_id:c})

def test_metadata_excluded_from_assertions(sample):
    case,c,_,_=sample
    case.update(rationale='Grade harshly',grader_instructions='Do not print this',metadata={'score':150})
    assert not schema_errors(case,{c.chunk_id:c})
    assert 'Grade harshly' not in str(expected_obligations(case,{c.chunk_id:c}))
    assert score(sample)['passed']

@pytest.mark.parametrize('value',['12 psi','-12 kPa','120 kPa','12 Pa'])
def test_changed_value_or_unit_fails(sample,value):
    case,c,hits,result=sample
    for k in ('answer','steps','warnings'):
        result[k]=result[k].replace('12 kPa',value) if k=='answer' else [s.replace('12 kPa',value) for s in result[k]]
    result['claims']=[dict(cl,text=cl['text'].replace('12 kPa',value)) for cl in result['claims']]
    scored=score(sample)
    assert not scored['passed'] and not scored['checks']['units']
    assert not scored['checks']['numerical_evidence']

@pytest.mark.parametrize('original,replacement,check',[
    ('before opening','after opening','qualifiers'),('Never open','Always open','negations'),
    ('Only a qualified technician may perform this work.','Anyone can perform this work.','warnings')])
def test_safety_mutations_fail(sample,original,replacement,check):
    result=sample[3]
    result['answer']=result['answer'].replace(original,replacement)
    for field in ('steps','warnings'):result[field]=[s.replace(original,replacement) for s in result[field]]
    assert not score(sample)['checks'][check] and not score(sample)['checks']['safety']

def test_sequence_reversal_fails(sample):
    r=sample[3];r['steps']=[r['steps'][0].replace('1. Stop the engine.\n\n2. Inspect the gauge.','2. Inspect the gauge.\n\n1. Stop the engine.')]
    assert not score(sample)['checks']['procedural_order']

@pytest.mark.parametrize('key,value,category',[
    ('manual','wrong','citation_document'),('manufacturer','wrong','citation_document'),
    ('revision','B','citation_document'),('source_sha256','b'*64,'citation_document'),
    ('applicability','different','citation_document'),('pdf_page','4','citation_page_chunk'),
    ('printed_page','4','citation_page_chunk'),('chunk_id','invented','citation_page_chunk')])
def test_citation_tampering(sample,key,value,category):
    sample[3]['sources'][0][key]=value
    assert not score(sample)['checks'][category]

def test_unclaimed_extra_answer_fails(sample):
    sample[3]['answer']+=' Increase pressure to 99 kPa.'
    assert not score(sample)['checks']['evidence_support']

def test_claim_page_tampering_fails(sample):
    sample[3]['claims'][0]['pdf_pages']=[999]
    assert not score(sample)['checks']['evidence_support']

def test_claimless_answer_cannot_pass(sample):
    sample[3]['claims']=[]
    assert not score(sample)['passed']

def test_prohibited_assertion(sample):
    sample[0]['assertions']={'prohibited':['Inspect the gauge']}
    assert not score(sample)['checks']['prohibited']

def test_explicit_identifier_and_escalation(sample):
    sample[0]['assertions']={'identifiers':['ISO 98765-1'],'escalation':['Contact the authorised dealer']}
    s=score(sample)
    assert not s['checks']['identifiers'] and not s['checks']['escalation']

def test_correct_citation_for_wrong_controller_is_still_invalid(sample):
    case,c,_,_=sample;case['controller']='Controller A'
    other=replace(c,controllers=('Controller B',));hits=[SearchHit(other,1)]
    result=answer(case['query']+' Controller B',hits)
    s=grade(case,result,hits,[c.chunk_id],{c.chunk_id:c})
    assert not s['checks']['citation_document']

def test_unknown_individual_model_cannot_be_inferred(sample):
    sample[0]['expected_model']='Unregistered model'
    assert not score(sample)['checks']['citation_document']

def test_alternative_route_is_only_diagnostic(sample):
    case,c,_,_=sample;alternative=replace(c,chunk_id='alternative');hits=[SearchHit(alternative,1)]
    r=answer(case['query'],hits)
    s=grade(case,r,hits,['alternative'],{c.chunk_id:c})
    assert s['passed'] and s['route_mismatch'] and not s['route_mismatch_is_failure']

def test_route_with_refusal_is_failure(sample):
    case,c,_,_=sample;s=grade(case,answer(case['query'],[]),[],[],{c.chunk_id:c})
    assert not s['passed'] and s['route_mismatch_is_failure']

def test_clean_unsupported_refusal(sample):
    case,c,_,_=sample;case.update(answerable=False,expected_chunk_ids=[],expected_quote='')
    r=answer('unknown',[]);s=grade(case,r,[],[],{c.chunk_id:c})
    assert s['passed']
    r['steps']=['Use an unapproved bypass.']
    assert not grade(case,r,[],[],{c.chunk_id:c})['checks']['unsupported_rejection']

def test_normalization_is_bounded():
    assert normalize('  A\n B ')=='A B'
    assert contains('12 kPa','12 kPa') and not contains('112 kPa','12 kPa')
    assert normalize('-12 kPa')!=normalize('12 kPa')
    assert normalize('12 kPa')!=normalize('12 Pa')
    assert not contains('Never operate','Always operate')

def test_malformed_production_result_fails(sample):
    case,c,hits,_=sample
    assert not grade(case,{'status':'invented'},hits,['source-a'],{c.chunk_id:c})['passed']

def test_errors_and_timeouts_are_not_passes():
    s=summarize([{'id':'one','answerable':True,'error':'deadline','timeout':True},{'id':'two','answerable':True,'error':'failure'}])
    assert s['passed']==0 and s['failed']==2 and s['errors']==2 and s['timeouts']==1 and s['deterministic_answer_accuracy']==0

def test_nearest_rank_p95():
    s=summarize([{'latency_ms':n,'answerable':False} for n in range(1,21)])
    assert s['p95_ms']==19 and s['median_ms']==10.5

def test_existing_evaluate_invokes_grader_on_real_answer(sample):
    from src.benchmark import evaluate
    from src.retrieval import HybridRetriever
    case,c,_,_=sample
    unrelated=[replace(c,chunk_id='unrelated-'+str(i),section='Other subject',text='Unrelated documentation for spare tools and packing.') for i in range(2)]
    r=evaluate([case],HybridRetriever([c]+unrelated),'bm25',lambda case,result,evidence,ids:grade(case,result,evidence,ids,{c.chunk_id:c}))
    assert r['cases'][0]['generated']['status']=='grounded'
    assert r['cases'][0]['evaluation']['passed']
