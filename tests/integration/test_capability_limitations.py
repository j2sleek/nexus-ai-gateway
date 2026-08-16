import pytest
from httpx import ASGITransport, AsyncClient

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.routing.engine import RouteResolver
from tests.fixtures.mock_provider import MockProvider


@pytest.fixture
async def test_app():
    async with lifespan(app):
        app.state.provider_registry = ProviderRegistry()
        app.state.model_registry = ModelRegistry()
        app.state.route_resolver = RouteResolver(
            app.state.provider_registry,
            app.state.model_registry,
        )
        yield app
        await app.state.provider_registry.clear()
        await app.state.model_registry.clear()


@pytest.mark.asyncio
async def test_capability_not_enforced(test_app):
    # Register a model that explicitly DOES NOT support CHAT
    model = ModelInfo(
        id="non-chat-model",
        provider="mock-provider",
        display_name="Non-Chat",
        capabilities=frozenset([Capability.EMBEDDINGS]),
    )
    await test_app.state.model_registry.register_model(model)
    provider = MockProvider("mock-provider")
    await test_app.state.provider_registry.register(provider)

    payload = {"model": "non-chat-model", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    # Current behavior: it is allowed because capability is not enforced
    assert response.status_code == 200
