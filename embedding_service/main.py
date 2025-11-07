from fastapi import FastAPI
from contextlib import asynccontextmanager

from embedding_service.core.config import settings
from embedding_service.core.logger import configure_logging, get_logger, log_json
from embedding_service.core.model_factory import ModelFactory
from embedding_service.service import EmbeddingService
from embedding_service.api import api_router
from embedding_service.core.exceptions import install_exception_handlers
import torch

configure_logging(settings.log_level)
logger = get_logger("granite-embedding-service")

def resolve_device(device_setting: str) -> str:
    if device_setting == "cpu":
        return "cpu"
    if device_setting == "cuda":
        if not torch.cuda.is_available():
            log_json(logger, "device_warning", msg="CUDA requested but unavailable; using CPU")
            return "cpu"
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"

@asynccontextmanager
async def lifespan(app: FastAPI):
    device = resolve_device(settings.device)
    model = ModelFactory(logger, settings.model_path, device, settings.fallback_model_path).load()
    app.state.embedding_service = EmbeddingService(model)
    app.state.embedding_dim = model.get_sentence_embedding_dimension()
    app.state.device = device
    log_json(logger, "startup", device=device, model_name=settings.model_name)
    yield
    log_json(logger, "shutdown", msg="Service stopping")

app = FastAPI(
    title="Granite Embedding API",
    version="1.5.0",
    lifespan=lifespan,
)

# include router
app.include_router(api_router)

# install global exception handlers
install_exception_handlers(app, logger)
