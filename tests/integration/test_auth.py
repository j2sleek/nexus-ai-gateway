import pytest
from httpx import ASGITransport, AsyncClient

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.routing.engine import RouteResolver


@pytest.fixture
async def test_app():
    """Fixture to provide an app instance with populated state."""
    async with lifespan(app):
        # Populate app state for testing
        app.state.provider_registry = ProviderRegistry()
        app.state.model_registry = ModelRegistry()
        app.state.route_resolver = RouteResolver(
            app.state.provider_registry,
            app.state.model_registry,
        )
        yield app
        # Cleanup
        await app.state.provider_registry.clear()
        await app.state.model_registry.clear()


@pytest.mark.asyncio
async def test_auth_missing_credentials(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing API Key"}


@pytest.mark.asyncio
async def test_auth_invalid_x_api_key(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "invalid-key"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}


@pytest.mark.asyncio
async def test_auth_invalid_bearer_token(test_app):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Authorization": "Bearer invalid-token"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API Key"}
