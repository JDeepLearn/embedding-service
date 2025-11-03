import requests
from typing import List
from app.providers.base import EmbeddingProvider
from app.core.logging import get_logger

log = get_logger("granite-provider")

class GraniteProvider(EmbeddingProvider):
    """
    Calls an on-prem IBM Granite runtime (REST endpoint).
    You can enable this later by switching EMBED_PROVIDER=granite.
    """
    def __init__(self, endpoint: str, model_id: str):
        self._endpoint = endpoint.rstrip("/")
        self._model_id = model_id

    def name(self): return "granite-local"
    def model(self): return self._model_id
    def ready(self): return True

    def embed(self, text: str) -> List[float]:
        payload = {"model_id": self._model_id, "input": [text]}
        r = requests.post(f"{self._endpoint}/v1/embeddings", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        payload = {"model_id": self._model_id, "input": texts}
        r = requests.post(f"{self._endpoint}/v1/embeddings", json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return [d["embedding"] for d in data["data"]]
