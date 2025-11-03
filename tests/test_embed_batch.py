import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_embed_batch_success(client):
    fake_vecs = [[0.1, 0.2], [0.3, 0.4]]

    with patch("app.api.routes_embed.PROVIDER.embed_batch", return_value=fake_vecs):
        with patch("app.api.routes_embed.PROVIDER.ready", return_value=True):
            res = await client.post("/embed", json={"texts": ["a", "b"]})
            assert res.status_code == 200
            body = res.json()
            assert "embeddings" in body
            assert len(body["embeddings"]) == 2
            assert body["provider"] == "ibm"
