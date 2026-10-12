import json
import httpx
import pytest
from signalledger import llm

def test_ollama_transport_schema_and_response(monkeypatch):
    original=httpx.Client
    def handle(request):
        data=json.loads(request.content)
        assert data['stream'] is False
        assert data['format']=={'type':'object'}
        assert len(data['messages'])==2
        return httpx.Response(200,json={'message':{'content':'{"answer": "grounded"}'}})
    monkeypatch.setattr(llm.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handle),**kw))
    assert llm.generate('Task',{'note':'untrusted'},{'type':'object'})=={'answer':'grounded'}

@pytest.mark.parametrize('response',[httpx.Response(503),httpx.Response(200,json={'message':{'content':'not JSON'}}),httpx.Response(200,content=b'x'*128001)])
def test_bad_provider_response_fails_closed(monkeypatch,response):
    original=httpx.Client
    monkeypatch.setattr(llm.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(lambda request:response),**kw))
    with pytest.raises(llm.ProviderError):llm.generate('Task',{},{'type':'object'})
