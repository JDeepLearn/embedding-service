from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from .config import settings


class EmbeddingRequest(BaseModel):
    """
    Request payload for /embed endpoint.

    - model: optional, defaults to active model.
    - inputs: list of text strings to embed.
    - metadata: optional user-supplied metadata for audit/trace.
    """

    model: str = Field(
        default_factory=lambda: settings.model_name,
        description="Model identifier for embedding (defaults to active model).",
    )
    inputs: List[str] = Field(
        ...,
        min_length=1,
        description="List of input texts to encode as embeddings.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for tracking or audit purposes.",
    )

    model_config = ConfigDict(extra="ignore")  # ignore unexpected keys


class EmbeddingVector(BaseModel):
    """
    Represents a single embedding vector in a response.
    Includes optional metadata for interpretability.
    """

    vector: List[float] = Field(..., description="Dense embedding vector representation.")
    text: Optional[str] = Field(
        default=None,
        description="Original text (optional, may be omitted for large requests).",
    )
    index: Optional[int] = Field(
        default=None,
        description="Index of this embedding in the original request.",
    )


class EmbeddingResponse(BaseModel):
    """
    Response payload for /embed endpoint.

    Contains:
    - model & version for traceability
    - embedding_dim: dimension of generated embeddings
    - embeddings: list of EmbeddingVector objects
    - metadata: optional server metadata
    """

    model: str = Field(..., description="Name of the embedding model used.")
    model_version: str = Field(..., description="Version or tag of the model.")
    embedding_dim: int = Field(..., description="Dimensionality of the embeddings.")
    embeddings: List[EmbeddingVector] = Field(
        ...,
        description="List of embedding vectors corresponding to input texts.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about the inference or request context.",
    )

    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when embeddings were generated.",
    )


class InfoResponse(BaseModel):
    """
    Response payload for /info endpoint.

    Provides detailed runtime information about the service
    and model configuration, useful for monitoring and debugging.
    """

    model_name: str
    model_version: str
    embedding_dim: int
    device: str
    service_version: str
    max_texts_per_request: int
    max_chars_per_text: int
    max_total_chars: int
    batch_size: int = Field(default_factory=lambda: settings.embed_batch_size)
    max_seq_length: int = Field(default_factory=lambda: settings.max_seq_length)
    metrics_enabled: bool = Field(default_factory=lambda: settings.metrics_enabled)
    fallback_model: Optional[str] = Field(
        default_factory=lambda: settings.fallback_model_name,
        description="Name of fallback model if configured.",
    )
    log_level: str = Field(default_factory=lambda: settings.log_level)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
