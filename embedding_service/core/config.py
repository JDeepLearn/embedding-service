from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global configuration for the Embedding Service.

    Values are loaded automatically from environment variables or `.env`.
    Safe defaults are provided for local environments.
    """

    # --- Application Metadata ---
    app_name: str = "Embedding Service"
    app_version: str = "1.0.0"
    environment: str = "local"  # local | dev | prod

    # --- Logging ---
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # --- Model Configuration ---
    model_name: str = "intfloat/e5-large-v2"

    # --- Metrics / Observability ---
    metrics_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


# Singleton settings instance
settings = Settings()
