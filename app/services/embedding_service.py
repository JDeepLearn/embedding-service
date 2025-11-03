from app.core.config import settings
from app.providers.hf_provider import HFProvider
from app.providers.granite_provider import GraniteProvider

def build_provider():
    provider = settings.embed_provider.lower()
    if provider == "hf":
        return HFProvider(model_name=settings.hf_model)
    elif provider == "granite":
        return GraniteProvider(
            endpoint=settings.granite_endpoint,
            model_id=settings.granite_model_id,
        )
    raise RuntimeError(f"Unknown EMBED_PROVIDER: {provider}")
