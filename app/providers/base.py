from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def model(self) -> str: ...
    @abstractmethod
    def ready(self) -> bool: ...
    @abstractmethod
    def embed(self, text: str) -> List[float]: ...
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]
