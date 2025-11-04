from fastapi.testclient import TestClient
from embedding_service.main import create_app

app = create_app()
client = TestClient(app)


def test_health_check_ok():
    """✅ /health returns service metadata and model info."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "model" in data


def test_single_text_embedding():
    """✅ /embed returns a valid single embedding."""
    res = client.post("/embed", json={"text": "Enterprise embedding test"})
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "hf-local"
    assert data["dim"] == len(data["embedding"])
    assert isinstance(data["embedding"], list)
    assert len(data["embedding"]) > 0


def test_batch_embeddings():
    """✅ /embed handles multiple texts."""
    texts = ["first test", "second test"]
    res = client.post("/embed", json={"texts": texts})
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == len(texts)
    assert isinstance(data["embeddings"], list)
    assert len(data["embeddings"][0]) == data["dim"]


def test_missing_fields_returns_400():
    """❌ /embed with no input should return 400."""
    res = client.post("/embed", json={})
    assert res.status_code == 400
    data = res.json()
    assert "detail" in data
    assert "must be provided" in data["detail"]


def test_invalid_type_returns_422():
    """❌ /embed with wrong data type triggers 422 validation error."""
    res = client.post("/embed", json={"text": 12345})
    assert res.status_code == 422


def test_internal_exception_json_format(monkeypatch):
    """❌ Simulate internal error and confirm JSON error envelope."""
    from embedding_service.api import routes_embed

    def fail(*args, **kwargs):
        raise RuntimeError("Simulated failure")

    monkeypatch.setattr(routes_embed._provider, "embed", fail)
    res = client.post("/embed", json={"text": "failure test"})
    assert res.status_code == 500
    body = res.json()
    assert body["error"] == "Internal Server Error"
    assert "path" in body


def test_metrics_endpoint_exposed():
    """✅ /metrics exposes Prometheus-compatible metrics."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "embedding_service_requests_total" in res.text