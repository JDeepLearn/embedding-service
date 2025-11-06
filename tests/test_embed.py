import pytest
from fastapi.testclient import TestClient

from embedding_service.main import create_app
from embedding_service.providers.registry import get_provider
from embedding_service.core.config import settings


@pytest.fixture(scope="session")
def client():
    """Reusable test client with shared app instance."""
    app = create_app()
    return TestClient(app)


def test_health_ok(client):
    """✅ /health endpoint should return model info and status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in {"ok", "not_ready"}
    assert "model" in data
    assert "provider" in data


def test_single_text_embedding(client):
    """✅ /embed should generate single text embedding."""
    res = client.post("/embed", json={"text": "Test embedding"})
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "hf-local"
    assert isinstance(data["embedding"], list)
    assert data["dim"] == len(data["embedding"])
    assert all(isinstance(x, float) for x in data["embedding"])


def test_batch_embedding(client):
    """✅ /embed handles batch embedding requests."""
    texts = ["hello", "world"]
    res = client.post("/embed", json={"texts": texts})
    assert res.status_code == 200
    data = res.json()
    assert "embeddings" in data
    assert data["count"] == len(texts)
    assert all(isinstance(vec, list) for vec in data["embeddings"])


def test_validation_too_long(client):
    """❌ Input text longer than max limit returns 400."""
    too_long_text = "x" * 5000
    res = client.post("/embed", json={"text": too_long_text})
    assert res.status_code == 400
    assert "exceeds" in res.text


def test_validation_too_many_texts(client):
    """❌ Batch size too large returns 400."""
    too_many = ["x"] * 999
    res = client.post("/embed", json={"texts": too_many})
    assert res.status_code == 400
    assert "Too many texts" in res.text


def test_empty_payload(client):
    """❌ Missing both 'text' and 'texts' should fail."""
    res = client.post("/embed", json={})
    assert res.status_code == 400
    assert "must be provided" in res.text


def test_error_envelope_consistency(client, monkeypatch):
    """❌ Simulate provider error and ensure JSON error envelope shape."""
    provider = get_provider()

    def fail(_):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(provider, "embed", fail)

    res = client.post("/embed", json={"text": "trigger"})
    assert res.status_code == 500
    body = res.json()
    assert body["error"] == "Internal Server Error"
    assert "detail" in body


def test_metrics_toggle(client):
    """✅ Metrics middleware and /metrics route obey config flag."""
    # Metrics enabled by default
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "embedding_service_requests_total" in res.text

    # Simulate metrics disabled
    settings.metrics_enabled = False
    app = create_app()
    test_client = TestClient(app)
    res = test_client.get("/metrics")
    assert res.status_code == 404  # not mounted