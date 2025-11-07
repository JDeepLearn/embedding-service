from typing import Optional, List
from pydantic import Field, AnyUrl, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized configuration for the Granite Embedding Service.

    All fields are environment-driven (12-factor compliant).
    Supports multi-model, performance, and security controls.
    """

    # --- Model settings ---
    model_name: str = Field(
        default="granite-embedding-english-r2",
        description="Identifier of the embedding model (Hugging Face or local).",
    )
    model_version: str = Field(
        default="1.0.0",
        description="Internal version tag for this deployment of the model.",
    )
    model_path: str = Field(
        default="/opt/models/granite-embedding-english-r2",
        description="Filesystem path to the local model directory.",
    )

    # --- Device / compute ---
    device: str = Field(
        default="auto",
        description="Computation device: auto, cpu, or cuda.",
    )
    embed_batch_size: int = Field(
        default=32,
        description="Batch size for encode() operations; tune for GPU/CPU throughput.",
    )
    max_seq_length: int = Field(
        default=512,
        description="Maximum token length before truncation (for deterministic behavior).",
    )

    # --- Security / API ---
    api_key: Optional[str] = Field(
        default=None,
        description="If set, clients must include this in X-API-Key header.",
    )
    cors_allow_origins: Optional[str] = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins.",
    )

    # --- Input size limits ---
    max_texts_per_request: int = Field(default=64)
    max_chars_per_text: int = Field(default=4000)
    max_total_chars: int = Field(default=256_000)

    # --- Logging & monitoring ---
    log_level: str = Field(default="INFO")
    metrics_enabled: bool = Field(
        default=True,
        description="Expose Prometheus metrics endpoints if true.",
    )

    # --- Multi-model extension ---
    fallback_model_name: Optional[str] = Field(
        default=None,
        description="Optional fallback model if primary fails (used for A/B or resilience).",
    )
    fallback_model_path: Optional[str] = Field(default=None)

    # --- URLs / telemetry (optional hooks) ---
    monitoring_url: Optional[AnyUrl] = None

    class Config:
        env_file = ".env"
        protected_namespaces = ("settings_",)
        extra = "ignore"

    @field_validator("embed_batch_size")
    @classmethod
    def check_batch_size(cls, v: int, info: ValidationInfo):
        if v <= 0:
            raise ValueError("embed_batch_size must be positive")
        return v


# Single global instance to prevent repeated env parsing
settings = Settings()