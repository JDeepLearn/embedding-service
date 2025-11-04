from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Abstract base class defining the embedding provider interface.

    Each provider implementation (HFProvider, GraniteProvider, etc.)
    must implement these methods to ensure compatibility with the API.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the provider's display name (e.g., 'hf-local')."""
        raise NotImplementedError

    @abstractmethod
    def model(self) -> str:
        """Return the model identifier (e.g., 'intfloat/e5-large-v2')."""
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> bool:
        """Return True if the provider is initialized and ready."""
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate an embedding for a single text input."""
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError
