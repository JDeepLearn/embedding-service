# app/providers/hf_provider.py
from sentence_transformers import SentenceTransformer
from app.providers.base import EmbeddingProvider
from app.core.logging import get_logger

log = get_logger("hf-provider")

class HFProvider(EmbeddingProvider):
    def __init__(self, model_name: str):
        log.info("Loading Hugging Face model", model=model_name)
        self._model_name = model_name
        self.model_instance = SentenceTransformer(model_name)
        log.info("Model loaded successfully")

    def name(self) -> str:
        return "hf-local"

    def model(self) -> str:   # satisfies abstract base
        return self._model_name

    def ready(self) -> bool:
        return True

    def embed(self, text: str):
        emb = self.model_instance.encode([text],
                                         convert_to_numpy=True,
                                         normalize_embeddings=True)
        return emb[0].tolist()

    def embed_batch(self, texts: list[str]):
        embs = self.model_instance.encode(texts,
                                          convert_to_numpy=True,
                                          normalize_embeddings=True)
        return [e.tolist() for e in embs]
