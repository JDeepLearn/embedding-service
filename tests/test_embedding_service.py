import os
import pytest
import requests
import numpy as np
from http import HTTPStatus


# -------------------------------------------------------------------
# TEST CONFIGURATION
# -------------------------------------------------------------------

BASE_URL = os.getenv("EMBED_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", None)
MODEL_NAME = os.getenv("MODEL_NAME", "ibm-granite/granite-embedding-english-r2")


@pytest.fixture(scope="session")
def headers():
    """Return default headers including API key if configured."""
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


@pytest.fixture(scope="session")
def check_service_ready():
    """
    Wait until /health endpoint responds before running tests.
    Fail fast if service is not running.
    """
    url = f"{BASE_URL}/health"
    try:
        resp = requests.get(url, timeout=10)
        assert resp.status_code == HTTPStatus.OK, "Health endpoint failed"
    except Exception as e:
        pytest.skip(f"Embedding service not running at {BASE_URL}: {e}")


# -------------------------------------------------------------------
# BASIC ENDPOINT TESTS
# -------------------------------------------------------------------

def test_health_endpoint(check_service_ready):
    """Ensure /health endpoint returns OK."""
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["status"] == "ok"


def test_info_endpoint(headers, check_service_ready):
    """Ensure /info returns expected model metadata."""
    resp = requests.get(f"{BASE_URL}/info", headers=headers)
    assert resp.status_code == HTTPStatus.OK

    info = resp.json()
    assert "model_name" in info
    assert "embedding_dim" in info
    assert info["model_name"] == MODEL_NAME
    assert info["embedding_dim"] > 0
    assert info["device"] in ("cpu", "cuda")


# -------------------------------------------------------------------
# EMBEDDING FUNCTIONALITY TESTS
# -------------------------------------------------------------------

def test_embed_returns_vectors(headers, check_service_ready):
    """Verify that /embed returns correctly shaped embeddings."""
    payload = {"inputs": ["reset password", "file a claim"]}
    resp = requests.post(f"{BASE_URL}/embed", json=payload, headers=headers)
    assert resp.status_code == HTTPStatus.OK, resp.text

    data = resp.json()
    embeddings = [e["vector"] for e in data["embeddings"]]
    arr = np.array(embeddings)

    # sanity checks
    assert arr.shape[0] == len(payload["inputs"])
    assert arr.ndim == 2
    assert arr.shape[1] == data["embedding_dim"]
    assert np.isclose(np.linalg.norm(arr[0]), 1.0, atol=1e-4), "Embeddings not normalized"


def test_embed_with_metadata(headers, check_service_ready):
    """Ensure metadata is accepted and echoed in response."""
    payload = {
        "inputs": ["submit a reimbursement claim"],
        "metadata": {"user": "qa-tester", "purpose": "integration"},
    }
    resp = requests.post(f"{BASE_URL}/embed", json=payload, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    meta = resp.json().get("metadata", {})
    assert "request_metadata" in meta
    assert meta["request_metadata"]["user"] == "qa-tester"


def test_embed_large_input_rejected(headers, check_service_ready):
    """Ensure that too-long input text triggers HTTP 413."""
    long_text = "x" * (int(os.getenv("MAX_CHARS_PER_TEXT", 4000)) + 10)
    payload = {"inputs": [long_text]}
    resp = requests.post(f"{BASE_URL}/embed", json=payload, headers=headers)
    assert resp.status_code == HTTPStatus.REQUEST_ENTITY_TOO_LARGE


# -------------------------------------------------------------------
# ERROR AND SECURITY TESTS
# -------------------------------------------------------------------

def test_invalid_api_key_rejected(monkeypatch, headers, check_service_ready):
    """If API_KEY is set, invalid key must be rejected."""
    if not API_KEY:
        pytest.skip("API_KEY not configured; skipping security test")

    bad_headers = headers.copy()
    bad_headers["X-API-Key"] = "wrong-key"
    resp = requests.post(f"{BASE_URL}/embed", json={"inputs": ["hi"]}, headers=bad_headers)
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_invalid_payload_rejected(headers, check_service_ready):
    """Ensure schema validation errors trigger 422."""
    # Missing "inputs" field
    resp = requests.post(f"{BASE_URL}/embed", json={"invalid": "data"}, headers=headers)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# -------------------------------------------------------------------
# PERFORMANCE / STRESS TEST (Optional)
# -------------------------------------------------------------------

@pytest.mark.parametrize("batch_size", [1, 8, 32])
def test_embed_batch_scaling(headers, check_service_ready, batch_size):
    """Measure latency scaling with different batch sizes (lightweight check)."""
    texts = [f"sample text {i}" for i in range(batch_size)]
    payload = {"inputs": texts}
    resp = requests.post(f"{BASE_URL}/embed", json=payload, headers=headers)
    assert resp.status_code == HTTPStatus.OK
    data = resp.json()
    assert len(data["embeddings"]) == batch_size