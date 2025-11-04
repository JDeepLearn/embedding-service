from typing import List

from sentence_transformers import SentenceTransformer

from embedding_service.providers.base import EmbeddingProvider
from embedding_service.core.config import settings
from embedding_service.core.logging import get_logger

log = get_logger(__name__)


class HFProvider(EmbeddingProvider):
    """
    Local Hugging Face embedding provider using SentenceTransformers.

    This implementation loads the model once and exposes simple
    synchronous APIs for single and batch text embeddings.
    """

    def __init__(self, model_name: str | None = None) -> None:
        model_id = model_name or settings.model_name
        log.info("Loading embedding model", extra={"model_name": model_id})

        # Model initialization
        self._model_name: str = model_id
        self.model_instance: SentenceTransformer = SentenceTransformer(model_id)

        log.info("Model loaded successfully", extra={"model_name": model_id})

    def name(self) -> str:
        """Return the provider name."""
        return "hf-local"

    def model(self) -> str:
        """Return the model identifier."""
        return self._model_name

    def ready(self) -> bool:
        """Return True if the model is loaded."""
        return True

    def embed(self, text: str) -> List[float]:
        """
        Compute a single embedding vector for the given text.

        Returns:
            A list of float values (embedding vector).
        """
        embeddings = self.model_instance.encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings[0].tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Compute embeddings for multiple input texts.

        Returns:
            A list of embedding vectors (list[list[float]]).
        """
        embeddings = self.model_instance.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return [emb.tolist() for emb in embeddings]
