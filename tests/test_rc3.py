import json
from pathlib import Path
from dataclasses import replace
import pytest
from src.models import Chunk
from src.retrieval import HybridRetriever
from src.answer_evaluation import prohibited_present,schema_errors

@pytest.mark.parametrize('label',['LEFT','RIGHT','STOP','DOWN'])
def test_controller_word_does_not_create_generic_exact_boost(label):
    controller=Chunk(chunk_id='panel',document_id='manual',manual_title='Manual',manufacturer='FG Wilson',models=(),section='Panel',page_start=1,page_end=1,text=f'The {label} control selects a panel function.',controllers=('Control 7',),identifiers=(label,))
    general=replace(controller,chunk_id='general',section='Battery handling',text=f'Battery {label.lower()} disconnected during cleaning.',controllers=(),identifiers=())
    unrelated=replace(general,chunk_id='other',section='Other',text='Covers and packaging.')
    r=HybridRetriever([controller,general,unrelated])
    generic=r.search(f'Battery {label.lower()} disconnected cleaning',mode='bm25')
    assert generic and generic[0].chunk.chunk_id=='general'
    assert all('deterministic exact identifier' not in h.reasons for h in generic if h.chunk.controllers)
    assert r.exact_lookup(label,controller='Control 7')
    explicit=r.search(label,controller='Control 7',mode='bm25')
    assert any('deterministic exact identifier' in h.reasons for h in explicit if h.chunk.chunk_id=='panel')

@pytest.mark.parametrize('prefix',['Do not ','Never '])
def test_safe_prohibition_is_not_its_unsafe_affirmative(prefix):
    assert not prohibited_present(prefix+'charge a frozen battery.','Charge a frozen battery.')
    assert prohibited_present('Charge a frozen battery.','Charge a frozen battery.')
    assert prohibited_present(prefix+'charge a frozen battery. Charge a frozen battery.','Charge a frozen battery.')

def test_negation_inside_a_later_clause_does_not_reverse_leading_prohibition():
    clause='Open the lid while the liquid is not cold.'
    assert not prohibited_present('Do not '+clause,clause)
    assert prohibited_present(clause,clause)

def test_structured_annotation_value_pair_validation():
    c={'id':'negative','query':'unavailable service','answerable':False,'expected_chunk_ids':[],'required_values':['1'],'required_units':[]}
    assert schema_errors(c,{})

def test_original_failed_results_preserved():
    root=Path(__file__).resolve().parents[1]
    original=root/'exports/historical_pre_rc3/gold_standard_answer_results.json'
    assert original.read_bytes()==(root/'exports/gold_standard_answer_results.json').read_bytes()
    result=json.loads(original.read_text(encoding='utf-8'))
    assert result['summary']['passed']==62 and result['summary']['failed']==2

def test_exposed_cases_are_regressions():
    root=Path(__file__).resolve().parents[1]
    rows=[json.loads(s) for s in (root/'benchmarks/regression.jsonl').read_text(encoding='utf-8').splitlines()]
    exposed=[c for c in rows if c.get('provenance')=='exposed_holdout_failure_rc2']
    assert len(exposed)==2 and all(c['original_split']=='holdout' for c in exposed)
    old=[json.loads(s) for s in (root/'benchmarks/holdout.jsonl').read_text(encoding='utf-8').splitlines()]
    assert not {c['id'] for c in exposed}&{c['id'] for c in old}
