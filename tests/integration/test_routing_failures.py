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
async def test_chat_completion_unknown_model_integration(test_app):
    # Ensure no models are registered
    payload = {"model": "non-existent-model", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Model non-existent-model not found."}
