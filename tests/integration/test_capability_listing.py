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
async def test_model_capabilities_exposed(test_app):
    # Test 1: Model with CHAT capability
    model = ModelInfo(
        id="chat-model-1",
        provider="test-provider",
        display_name="Chat Model",
        capabilities=frozenset([Capability.CHAT]),
    )
    await test_app.state.model_registry.register_model(model)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "chat-model-1"
    assert data["data"][0]["capabilities"] == ["chat"]


@pytest.mark.asyncio
async def test_multiple_capabilities_serialization(test_app):
    # Test 2: Model supporting multiple capabilities
    model = ModelInfo(
        id="multi-model",
        provider="test-provider",
        display_name="Multi Model",
        capabilities=frozenset([Capability.CHAT, Capability.TOOLS, Capability.STREAMING]),
    )
    await test_app.state.model_registry.register_model(model)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    model_data = data["data"][0]
    assert model_data["id"] == "multi-model"
    # Verify deterministic sorting: chat, streaming, tools
    assert model_data["capabilities"] == ["chat", "streaming", "tools"]


@pytest.mark.asyncio
async def test_embeddings_only_model(test_app):
    # Test 3: Embeddings-only model
    model = ModelInfo(
        id="embeddings-model",
        provider="test-provider",
        display_name="Embeddings Model",
        capabilities=frozenset([Capability.EMBEDDINGS]),
    )
    await test_app.state.model_registry.register_model(model)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    model_data = data["data"][0]
    assert model_data["id"] == "embeddings-model"
    assert model_data["capabilities"] == ["embeddings"]
    assert "chat" not in model_data["capabilities"]


@pytest.mark.asyncio
async def test_capability_filtering(test_app):
    # Test 4: Capability filtering
    chat_model = ModelInfo(
        id="chat-m",
        provider="p1",
        display_name="Chat M",
        capabilities=frozenset([Capability.CHAT]),
    )
    embeddings_model = ModelInfo(
        id="embed-m",
        provider="p2",
        display_name="Embed M",
        capabilities=frozenset([Capability.EMBEDDINGS]),
    )
    await test_app.state.model_registry.register_model(chat_model)
    await test_app.state.model_registry.register_model(embeddings_model)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        # Filter by chat
        resp_chat = await ac.get("/v1/models?capability=chat")
        assert resp_chat.status_code == 200
        chat_data = resp_chat.json()["data"]
        assert len(chat_data) == 1
        assert chat_data[0]["id"] == "chat-m"

        # Filter by embeddings
        resp_embed = await ac.get("/v1/models?capability=embeddings")
        assert resp_embed.status_code == 200
        embed_data = resp_embed.json()["data"]
        assert len(embed_data) == 1
        assert embed_data[0]["id"] == "embed-m"

        # Invalid capability value should return 422 Unprocessable Entity
        resp_invalid = await ac.get("/v1/models?capability=nonexistent-capability")
        assert resp_invalid.status_code == 422


@pytest.mark.asyncio
async def test_provider_discovery_capability_retention(test_app):
    # Test 5: Provider discovery / ModelInfo registration retains capabilities
    provider = MockProvider("mock-prov")
    await test_app.state.provider_registry.register(provider)

    model = ModelInfo(
        id="discovered-model",
        provider="mock-prov",
        display_name="Discovered Model",
        capabilities=frozenset([Capability.REASONING, Capability.CHAT]),
    )
    await test_app.state.model_registry.register_model(model)

    retrieved = await test_app.state.model_registry.get_model("discovered-model")
    assert retrieved is not None
    assert retrieved.capabilities == frozenset([Capability.REASONING, Capability.CHAT])


@pytest.mark.asyncio
async def test_backward_compatibility_default_capability(test_app):
    # Test 6: Model without explicitly supplied capabilities retains default behavior (CHAT)
    model = ModelInfo(
        id="default-model",
        provider="test-provider",
        display_name="Default Model",
    )
    await test_app.state.model_registry.register_model(model)

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["data"][0]["capabilities"] == ["chat"]
