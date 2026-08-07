import pytest

from app.models.capability import Capability
from app.models.model_info import ModelInfo


@pytest.mark.asyncio
async def test_exact_model_routing(
    model_registry, provider_registry, route_resolver, mock_provider
):
    model = ModelInfo(id="gpt-4", provider="mock-provider", display_name="GPT-4")
    await model_registry.register_model(model)
    await provider_registry.register(mock_provider)

    result = await route_resolver.resolve(requested_model="gpt-4")
    assert result.model == "gpt-4"
    assert result.provider == "mock-provider"
    assert result.routing_reason == "success"


@pytest.mark.asyncio
async def test_capability_routing(model_registry, provider_registry, route_resolver, mock_provider):
    model = ModelInfo(
        id="model-a",
        provider="mock-provider",
        display_name="Model A",
        capabilities=frozenset([Capability.CHAT]),
    )
    await model_registry.register_model(model)
    await provider_registry.register(mock_provider)

    result = await route_resolver.resolve(required_capability=Capability.CHAT)
    assert result.model == "model-a"
    assert result.capability_used == Capability.CHAT
