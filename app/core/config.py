from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    log_format: str = "json"

    # Switchable providers
    embed_provider: str = "hf"  # "hf" or "granite"

    # HF model (local)
    hf_model: str = "intfloat/e5-large-v2"

    # Granite (future on-prem)
    granite_endpoint: str = "http://granite-runtime:8085"
    granite_model_id: str = "ibm/granite-embedding-english-r2"

    cors_origins: List[str] = ["*"]  # allow all origins by default

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
