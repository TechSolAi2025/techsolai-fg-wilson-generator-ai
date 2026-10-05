"""Architectural regression tests; release results require the live corpus."""
from dataclasses import replace
import pytest
from src.models import Chunk, SearchHit
from src.retrieval import HybridRetriever, tokens, query_tokens
from src.answering import answer
from src.answer_evaluation import grade


def chunk(text, section='Pressure', ident='a'):
    return Chunk(chunk_id=ident, document_id='manual', manual_title='Manual',
                 manufacturer='FG Wilson', models=(), section=section,
                 page_start=1, page_end=1, printed_pages=('1',), text=text)


@pytest.mark.parametrize('prefix', ['Show', 'Please describe', 'Explain', 'Show precautions for'])
def test_conversational_verbs_do_not_dilute_coverage(prefix):
    c=chunk('Pressure\n\nInspect the pressure gauge before operation.')
    assert answer(prefix+' pressure', [SearchHit(c, 1)])['status']=='grounded'


def test_unknown_technical_terms_and_negation_are_retained():
    assert set(tokens('Show not xenoflux pressure 125 psi')) >= {'not','xenoflux','pressure','125','psi'}
    c=chunk('Pressure\n\nInspect the pressure gauge before operation.')
    assert answer('Show xenoflux calibration pressure', [SearchHit(c,1)])['status']=='insufficient'
    assert 'precautions' in tokens('precautions before welding')
    assert query_tokens('List the instructions for xenoflux not 125 psi')==['xenoflux','not','125','psi']


def test_focused_title_beats_broader_title_with_identical_body():
    c=chunk('Check the bearings and insulation.', 'Bearings')
    broad=replace(c,chunk_id='b',section='Bearings and Insulation')
    other=replace(c,chunk_id='c',section='Transport',text='Secure the load.')
    corpus=[broad,c,other,replace(other,chunk_id='d'),replace(other,chunk_id='e')]
    assert HybridRetriever(corpus).search('bearings',mode='bm25')[0].chunk.chunk_id=='a'


@pytest.mark.parametrize('text',['Pressure\nColumn: 40', 'Pressure: [empty cell]\nValue: 40'])
def test_anonymous_table_cells_require_review(text):
    assert answer('pressure',[SearchHit(chunk(text),1)])['status']=='review_required'


def test_annotated_warning_can_be_delivered_as_cited_warning():
    warning='Only trained personnel may inspect this equipment.'
    c=replace(chunk('Pressure\n\nInspect the gauge.'),warnings=(warning,),warning_pages=(1,))
    case={'answerable':True,'expected_quote':warning,'expected_chunk_ids':['a'],
          'required_warnings':[warning]}
    result=answer('pressure',[SearchHit(c,1)])
    assert grade(case,result,[SearchHit(c,1)],['a'],{'a':c})['passed']
    result['claims']=[x for x in result['claims'] if x['field']!='warnings']
    assert not grade(case,result,[SearchHit(c,1)],['a'],{'a':c})['passed']


def test_ordinary_required_assertion_cannot_hide_in_warnings():
    c=chunk('Pressure\n\nInspect the gauge.')
    result=answer('pressure',[SearchHit(c,1)])
    result['warnings'].append('Replace the seal.')
    case={'answerable':True,'expected_quote':'Replace the seal.','expected_chunk_ids':['a']}
    assert not grade(case,result,[SearchHit(c,1)],['a'],{'a':c})['checks']['required']
