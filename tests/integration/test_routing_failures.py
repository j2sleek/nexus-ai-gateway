import pytest
from httpx import ASGITransport, AsyncClient

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.model_info import ModelInfo
from app.routing.engine import RouteResolver
from tests.fixtures.mock_provider import MockProvider


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


@pytest.mark.asyncio
async def test_chat_completion_no_healthy_provider(test_app, mocker):
    # Register a model
    model = ModelInfo(id="gpt-4", provider="mock-provider", display_name="GPT-4")
    await test_app.state.model_registry.register_model(model)

    # Register an unhealthy provider
    provider = MockProvider("mock-provider", is_healthy=False)
    await test_app.state.provider_registry.register(provider)

    # Spy on the provider's chat method
    chat_spy = mocker.spy(provider, "chat")

    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "No healthy providers available."}

    # Verify chat was never called
    chat_spy.assert_not_called()
