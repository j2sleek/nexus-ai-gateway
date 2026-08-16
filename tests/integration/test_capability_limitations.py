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
async def test_capability_enforced_rejection(test_app, mocker):
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
    chat_spy = mocker.spy(provider, "chat")

    payload = {"model": "non-chat-model", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Model non-chat-model does not support capability chat."}
    chat_spy.assert_not_called()


@pytest.mark.asyncio
async def test_capability_enforced_success(test_app, mocker):
    model = ModelInfo(
        id="chat-model",
        provider="mock-provider",
        display_name="Chat Model",
        capabilities=frozenset([Capability.CHAT]),
    )
    await test_app.state.model_registry.register_model(model)
    provider = MockProvider("mock-provider")
    await test_app.state.provider_registry.register(provider)
    chat_spy = mocker.spy(provider, "chat")

    payload = {"model": "chat-model", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    chat_spy.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_models_capability_filtering(test_app):
    # Model A: high priority, but EMBEDDINGS only
    model_a = ModelInfo(
        id="model-embeddings",
        provider="provider-a",
        display_name="Embeddings Model",
        capabilities=frozenset([Capability.EMBEDDINGS]),
        priority=100,
    )
    # Model B: lower priority, but supports CHAT
    model_b = ModelInfo(
        id="model-chat",
        provider="provider-b",
        display_name="Chat Model",
        capabilities=frozenset([Capability.CHAT]),
        priority=10,
    )
    await test_app.state.model_registry.register_model(model_a)
    await test_app.state.model_registry.register_model(model_b)

    provider_a = MockProvider("provider-a")
    provider_b = MockProvider("provider-b")
    await test_app.state.provider_registry.register(provider_a)
    await test_app.state.provider_registry.register(provider_b)

    # Resolve using RouteResolver directly with required_capability=Capability.CHAT
    result = await test_app.state.route_resolver.resolve(required_capability=Capability.CHAT)
    assert result.model == "model-chat"
    assert result.provider == "provider-b"
    assert result.capability_used == Capability.CHAT
