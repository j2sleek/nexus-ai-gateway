import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import CapabilityNotSupported
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.capability import Capability
from app.providers.litellm import LiteLLMProvider
from app.routing.engine import RouteResolver


@pytest.fixture
async def litellm_test_app(mocker):
    fake_cost_map = {
        "gpt-4o-litellm": {
            "mode": "chat",
            "supports_function_calling": True,
        },
        "embed-litellm": {
            "mode": "embedding",
        },
    }
    mocker.patch("litellm.model_cost", fake_cost_map)

    async with lifespan(app):
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry()
        litellm_provider = LiteLLMProvider()
        await provider_registry.register(litellm_provider)

        discovered_models = await litellm_provider.list_models()
        for m in discovered_models:
            await model_registry.register_model(m)

        app.state.provider_registry = provider_registry
        app.state.model_registry = model_registry
        app.state.route_resolver = RouteResolver(provider_registry, model_registry)
        yield app

        await app.state.provider_registry.clear()
        await app.state.model_registry.clear()


@pytest.mark.asyncio
async def test_litellm_v1_models_endpoint_and_filtering(litellm_test_app):
    # Test 10 & 11: GET /v1/models exposes LiteLLM models and filtering works
    async with AsyncClient(
        transport=ASGITransport(app=litellm_test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        # All models
        resp = await ac.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()["data"]
        ids = {m["id"] for m in data}
        assert "gpt-4o-litellm" in ids
        assert "embed-litellm" in ids

        # Chat filtering
        resp_chat = await ac.get("/v1/models?capability=chat")
        assert resp_chat.status_code == 200
        chat_ids = {m["id"] for m in resp_chat.json()["data"]}
        assert "gpt-4o-litellm" in chat_ids
        assert "embed-litellm" not in chat_ids

        # Embeddings filtering
        resp_embed = await ac.get("/v1/models?capability=embeddings")
        assert resp_embed.status_code == 200
        embed_ids = {m["id"] for m in resp_embed.json()["data"]}
        assert "embed-litellm" in embed_ids
        assert "gpt-4o-litellm" not in embed_ids


@pytest.mark.asyncio
async def test_litellm_routing_capabilities_and_rejection(litellm_test_app):
    # Test 12: RouteResolver selects capable model, rejects incapable model
    resolver = litellm_test_app.state.route_resolver

    # Capable model for CHAT
    res_chat = await resolver.resolve(
        requested_model="gpt-4o-litellm", required_capability=Capability.CHAT
    )
    assert res_chat.model == "gpt-4o-litellm"
    assert res_chat.provider == "litellm"

    # Incapable model for CHAT (embed-litellm)
    with pytest.raises(CapabilityNotSupported):
        await resolver.resolve(requested_model="embed-litellm", required_capability=Capability.CHAT)
