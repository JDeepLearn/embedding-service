import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_embed_single_success(client):
    fake_vec = [0.1, 0.2, 0.3]

    with patch("app.api.routes_embed.PROVIDER.embed", return_value=fake_vec):
        with patch("app.api.routes_embed.PROVIDER.ready", return_value=True):
            res = await client.post("/embed", json={"text": "Hello world"})
            assert res.status_code == 200
            data = res.json()
            assert data["embedding"] == fake_vec
            assert data["provider"] == "ibm"
            assert "dim" in data and data["dim"] == len(fake_vec)
