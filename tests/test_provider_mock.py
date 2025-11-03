import pytest
from app.providers.granite_provider import GraniteProvider

class DummyIBMClient:
    def embed_query(self, text): return [0.42, 0.69]
    def embed_documents(self, texts): return [[0.1, 0.2], [0.3, 0.4]]

@pytest.fixture
def provider(monkeypatch):
    p = GraniteProvider("k", "proj", "https://dummy.endpoint", "model")
    p._sdk_ok = True
    p._client = DummyIBMClient()
    return p

def test_provider_single(provider):
    vec = provider.embed("hi")
    assert isinstance(vec, list)
    assert len(vec) == 2

def test_provider_batch(provider):
    vecs = provider.embed_batch(["x", "y"])
    assert len(vecs) == 2
    assert all(isinstance(v, list) for v in vecs)
