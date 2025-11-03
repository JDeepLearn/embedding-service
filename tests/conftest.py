# tests/conftest.py
import pytest
import httpx
from app.main import create_app
from fastapi import FastAPI


@pytest.fixture(scope="session")
def app() -> FastAPI:
    """Create a FastAPI app instance once per test session."""
    return create_app()


@pytest.fixture(scope="session")
async def client(app: FastAPI):
    """
    Async HTTP client for integration tests.
    Uses ASGITransport (httpx>=0.28) to call app directly without network IO.
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
