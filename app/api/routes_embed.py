# app/api/routes_embed.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.providers.hf_provider import HFProvider

router = APIRouter()
provider = HFProvider("intfloat/e5-large-v2")

class EmbedRequest(BaseModel):
    text: str | None = None
    texts: list[str] | None = None

@router.post("/embed")
async def embed_text(req: EmbedRequest):
    try:
        if req.text:
            vec = provider.embed(req.text)
            return {
                "provider": provider.name(),
                "model": provider.model(),  # returns string "intfloat/e5-large-v2"
                "embedding": vec,
                "dim": len(vec),
            }
        elif req.texts:
            vecs = provider.embed_batch(req.texts)
            return {
                "provider": provider.name(),
                "model": provider.model(),
                "embeddings": vecs,
                "count": len(vecs),
                "dim": len(vecs[0]),
            }
        else:
            raise HTTPException(status_code=400, detail="Missing 'text' or 'texts'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
