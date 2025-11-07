from typing import List

from sentence_transformers import SentenceTransformer

from .core.config import settings


class EmbeddingService:
    """
    Encapsulates the core embedding logic.

    This class is intentionally framework-agnostic so it can be reused
    in scripts, batch jobs, or other services without bringing in FastAPI.
    """

    def __init__(self, model: SentenceTransformer):
        self._model = model
        self._batch_size = settings.embed_batch_size

        # Apply deterministic truncation behavior if the model exposes it.
        if hasattr(self._model, "max_seq_length"):
            self._model.max_seq_length = settings.max_seq_length

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Encode input texts into normalized embeddings.

        Args:
            texts: List of input text strings.

        Returns:
            List of embedding vectors (each a list of floats).
        """
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        # Convert NumPy array -> pure Python lists for JSON serialization.
        return [v.tolist() for v in vectors]
