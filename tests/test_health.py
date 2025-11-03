import pytest

@pytest.mark.asyncio
async def test_health_ok(client):
    res = await client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert body["status"] in ["ok", "degraded"]
