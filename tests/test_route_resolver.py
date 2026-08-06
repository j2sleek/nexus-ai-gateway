import pytest

from app.models.capability import Capability
from app.models.model_info import ModelInfo


@pytest.mark.asyncio
async def test_exact_model_routing(model_registry, route_resolver):
    model = ModelInfo(id="gpt-4", provider="litellm", display_name="GPT-4")
    await model_registry.register_model(model)

    result = await route_resolver.resolve(requested_model="gpt-4")
    assert result.model == "gpt-4"
    assert result.provider == "litellm"
    assert result.reason == "exact_match"


@pytest.mark.asyncio
async def test_capability_routing(model_registry, route_resolver):
    model = ModelInfo(
        id="model-a",
        provider="litellm",
        display_name="Model A",
        capabilities=frozenset([Capability.CHAT]),
    )
    await model_registry.register_model(model)

    result = await route_resolver.resolve(required_capability=Capability.CHAT)
    assert result.model == "model-a"
    assert result.reason == "capability_match"
