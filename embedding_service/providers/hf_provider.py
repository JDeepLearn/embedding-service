from typing import List, Optional
from sentence_transformers import SentenceTransformer

from embedding_service.core.config import settings
from embedding_service.core.logging import get_logger

log = get_logger(__name__)


class HFProvider:
    """
    Local Hugging Face embedding provider using SentenceTransformers.

    This implementation loads the model once and exposes simple
    synchronous APIs for single and batch text embeddings.
    """

    def __init__(self, model_name: Optional[str] = None, device: str = "cpu") -> None:
        model_id = model_name or settings.model_name
        self._model_name = model_id
        self._device = device

        log.info("Loading embedding model", extra={"model_name": model_id, "device": device})

        try:
            # Initialize the SentenceTransformer model
            self.model_instance = SentenceTransformer(model_id, device=device)
        except Exception as exc:
            log.exception("Failed to load embedding model", extra={"model_name": model_id, "error": str(exc)})
            raise RuntimeError(f"Failed to load model {model_id}: {exc}") from exc

        log.info("Model loaded successfully", extra={"model_name": model_id})

    def name(self) -> str:
        """Return the provider name."""
        return "hf-local"

    def model(self) -> str:
        """Return the model identifier."""
        return self._model_name

    def ready(self) -> bool:
        """Return True if the model is loaded."""
        return hasattr(self, "model_instance")

    def embed(self, text: str) -> List[float]:
        """
        Compute a single embedding vector for the given text.

        Returns:
            A list of float values (embedding vector).
        """
        if not text.strip():
            log.warning("Empty input text provided to embed()")
            return []

        try:
            embeddings = self.model_instance.encode(
                [text],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embeddings[0].tolist()
        except Exception as exc:
            log.exception("Embedding generation failed", extra={"error": str(exc)})
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Compute embeddings for multiple input texts.

        Returns:
            A list of embedding vectors (list[list[float]]).
        """
        if not texts:
            log.warning("Empty text list provided to embed_batch()")
            return []

        try:
            embeddings = self.model_instance.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as exc:
            log.exception("Batch embedding generation failed", extra={"error": str(exc)})
            raise