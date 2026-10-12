import copy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from signalledger.models import Investigation
from signalledger.engine import investigate, anomaly
from signalledger import llm

def fixture(name='01-source-delay'):
    return json.loads((Path(__file__).parents[1]/'examples'/f'{name}.json').read_text())

@pytest.mark.parametrize('scenario,root',[('01-source-delay','partner_api'),('02-schema-drift','raw_events'),('03-healthy',None)])
def test_known_incidents(scenario,root):
    result=investigate(Investigation(**fixture(scenario)))
    assert result['hypothesis_asset']==root
    if root is None:
        assert result['status']=='insufficient_evidence'
    else:
        assert result['evidence_ids']
        assert 'billing_feed' not in result['blast_radius']

def test_off_lineage_anomaly_does_not_become_root():
    body=fixture();body['signals'][-1]['observed']=100000
    r=investigate(Investigation(**body))
    assert r['hypothesis_asset']=='partner_api'
    assert 'billing_feed' not in [c['asset_id'] for c in r['candidates']]

def test_healthy_warehouse_challenges_symptom():
    r=investigate(Investigation(**fixture()))
    assert 'sig-warehouse' in [s['id'] for s in r['controls']]
    assert 'runbook-rate' in [n['id'] for n in r['runbooks']]

@pytest.mark.parametrize('fault',['cycle','missing_parent','duplicate_evidence','missing_asset','naive_time','invalid_fraction','nonfinite'])
def test_bad_input_rejected(fault):
    body=fixture()
    if fault=='cycle':body['assets'][0]['parents']=['executive_dashboard']
    if fault=='missing_parent':body['assets'][0]['parents']=['absent']
    if fault=='duplicate_evidence':body['signals'][1]['id']=body['signals'][0]['id']
    if fault=='missing_asset':body['signals'][0]['asset_id']='missing'
    if fault=='naive_time':body['signals'][0]['timestamp']='2026-10-11T10:00:00'
    if fault=='invalid_fraction':body['signals'][0].update(metric='null_fraction',observed=1.1)
    if fault=='nonfinite':body['signals'][0]['observed']=float('inf')
    with pytest.raises(ValidationError):Investigation(**body)

def test_zero_baseline_and_input_immutability():
    body=fixture();body['signals'][0].update(metric='errors',baseline=[0]*5,observed=5)
    original=copy.deepcopy(body)
    r=investigate(Investigation(**body))
    assert r['signals'][0]['robust_z']==5
    assert body==original

def test_ai_accepts_known_candidate_and_citations(monkeypatch):
    body=fixture();body['analyst']='ollama'
    monkeypatch.setattr(llm,'generate',lambda *args:dict(hypothesis_asset='partner_api',summary='The source reports elevated delivery lag.',evidence_ids=['sig-source'],checks=['Inspect rate limit logs.'],caveat='This is a hypothesis.'))
    r=investigate(Investigation(**body))
    assert r['analyst']=='ollama'
    assert r['ai_status']=='validated'

@pytest.mark.parametrize('root,ids',[('imaginary',['sig-source']),('partner_api',['made-up']),('partner_api',['sig-mart'])])
def test_ai_cannot_invent_or_misassign_evidence(monkeypatch,root,ids):
    body=fixture();body['analyst']='ollama'
    monkeypatch.setattr(llm,'generate',lambda *args:dict(hypothesis_asset=root,summary='An unsupported invented explanation.',evidence_ids=ids,checks=['Check logs.'],caveat='Uncertain.'))
    r=investigate(Investigation(**body))
    assert r['analyst']=='evidence_engine'
    assert r['ai_status']=='rejected_or_unavailable'

def test_provider_timeout_falls_back(monkeypatch):
    body=fixture();body['analyst']='ollama'
    def fail(*args):raise llm.ProviderError('Unavailable')
    monkeypatch.setattr(llm,'generate',fail)
    assert investigate(Investigation(**body))['hypothesis_asset']=='partner_api'

def test_no_ai_call_on_abstention(monkeypatch):
    body=fixture('03-healthy');body['analyst']='ollama'
    def fail(*args):raise AssertionError('AI should not run without evidence')
    monkeypatch.setattr(llm,'generate',fail)
    assert investigate(Investigation(**body))['ai_status']=='skipped_insufficient_evidence'
