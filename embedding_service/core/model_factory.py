import os
from logging import Logger
from typing import Final, Optional

from sentence_transformers import SentenceTransformer, models
from transformers import AutoModel, AutoTokenizer

from .logger import log_json


MODERNBERT_HINTS: Final[list[str]] = [
    "modernbert",
    "does not recognize this architecture",
    "model type",
]


class ModelFactory:
    """
    Factory for loading Granite / Transformer / ModernBERT-based models.

    Robust loader that:
    - Supports local or Hugging Face directories.
    - Detects ModernBERT automatically.
    - Falls back to trust_remote_code=True for custom architectures.
    - Emits detailed structured logs for observability.
    """

    def __init__(self, logger: Logger, path: str, device: str, fallback_path: Optional[str] = None):
        self._logger = logger
        self._path = path
        self._device = device
        self._fallback_path = fallback_path

    # ----------------------------- #
    def load(self) -> SentenceTransformer:
        """Load and return a SentenceTransformer instance."""
        if not os.path.isdir(self._path):
            msg = f"Model path invalid: {self._path}"
            log_json(self._logger, "model_path_invalid", error=msg)
            raise RuntimeError(msg)

        log_json(
            self._logger,
            "model_loading_start",
            model_path=self._path,
            device=self._device,
        )

        try:
            model = self._load_with_fallback()
        except Exception as exc:  # noqa: BLE001
            log_json(self._logger, "model_loading_failure", error=str(exc))
            if self._fallback_path and os.path.isdir(self._fallback_path):
                log_json(
                    self._logger,
                    "model_fallback_invoke",
                    msg=f"Attempting fallback model at {self._fallback_path}",
                )
                model = self._load_path(self._fallback_path)
            else:
                raise

        model.eval()
        dim = int(model.get_sentence_embedding_dimension())
        log_json(self._logger, "model_loading_success", embedding_dim=dim)
        return model

    # ----------------------------- #
    def _load_with_fallback(self) -> SentenceTransformer:
        """
        Attempt normal load; if ModernBERT/Granite architecture is unrecognized,
        transparently switch to remote-code loader.
        """
        try:
            return SentenceTransformer(self._path, device=self._device)
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            if any(hint in message for hint in MODERNBERT_HINTS):
                log_json(
                    self._logger,
                    "modernbert_detected",
                    msg="Activating trust_remote_code fallback",
                )
                return self._load_modernbert_with_remote_code()
            raise  # propagate other exceptions

    # ----------------------------- #
    def _load_modernbert_with_remote_code(self) -> SentenceTransformer:
        """
        Fallback loader for Granite/ModernBERT models requiring custom code.

        SECURITY NOTE:
        trust_remote_code=True executes code from the model repo. This should
        only be used for vetted, internally hosted, or verified Hugging Face
        sources.
        """
        tokenizer = AutoTokenizer.from_pretrained(self._path, trust_remote_code=True)
        transformer = AutoModel.from_pretrained(self._path, trust_remote_code=True)

        word_emb = models.Transformer(
            model_name_or_path=self._path,
            tokenizer=tokenizer,
            model=transformer,
        )
        pooling = models.Pooling(
            word_emb.get_word_embedding_dimension(),
            pooling_mode_mean_tokens=True,
        )

        model = SentenceTransformer(modules=[word_emb, pooling], device=self._device)
        log_json(self._logger, "modernbert_loader_success", path=self._path)
        return model

    # ----------------------------- #
    def _load_path(self, path: str) -> SentenceTransformer:
        """Explicit path loader for fallback use."""
        return SentenceTransformer(path, device=self._device)