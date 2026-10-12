import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from signalledger.api import create_app
from signalledger.store import Store, Conflict

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(str(tmp_path/'test.db'))) as client:
        yield client

@pytest.fixture
def body():
    return json.loads((Path(__file__).parents[1]/'examples/01-source-delay.json').read_text())

def test_api_roundtrip_and_idempotency(client,body):
    a=client.post('/api/investigations',json=body,headers={'Idempotency-Key':'once'})
    assert a.status_code==200
    b=client.post('/api/investigations',json=body,headers={'Idempotency-Key':'once'})
    assert a.json()==b.json()
    assert client.get('/api/investigations/'+a.json()['id']).json()==a.json()
    assert len(client.get('/api/investigations').json())==1
    body['title']='Changed'
    assert client.post('/api/investigations',json=body,headers={'Idempotency-Key':'once'}).status_code==409

def test_static_assets_and_openapi(client):
    assert client.get('/').status_code==200
    assert 'text/css' in client.get('/style.css').headers['content-type']
    assert client.get('/api/health').json()['status']=='ok'
    assert len(client.get('/api/scenarios').json())==3
    assert '/api/investigations' in client.get('/openapi.json').json()['paths']
    assert client.get('/api/investigations/missing').status_code==404
    assert client.get('/api/scenarios/missing').status_code==404

def test_token_boundary(client,body,monkeypatch):
    monkeypatch.setenv('APP_TOKEN','unit-test-token')
    assert client.get('/api/scenarios').status_code==401
    assert client.get('/api/scenarios',headers={'Authorization':'Bearer unit-test-token'}).status_code==200
    assert client.get('/api/health').status_code==200

def test_request_size_limit(client):
    r=client.post('/api/investigations',content=b'x'*2097153)
    assert r.status_code==413

def test_invalid_schema(client):
    assert client.post('/api/investigations',json={}).status_code==422

def test_concurrent_idempotent_writes(tmp_path):
    store=Store(str(tmp_path/'race.db'))
    with ThreadPoolExecutor(max_workers=6) as pool:
        reports=list(pool.map(lambda _:store.save('same',{'request':1},{'ok':True}),range(12)))
    assert len({r['id'] for r in reports})==1
    assert len(store.recent())==1
    with pytest.raises(Conflict):store.save('same',{'request':2},{'ok':True})
