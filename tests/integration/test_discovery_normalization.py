import pytest

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.manager import DiscoveryManager
from app.models.capability import Capability
from app.models.model_info import ModelInfo
from tests.fixtures.mock_provider import MockProvider


class NormalizationMockProvider(MockProvider):
    async def list_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(
                id="model-discovered-1",
                provider=self.provider_name,
                display_name="Model 1",
                capabilities=frozenset(["chat", "tools", "UNKNOWN-CAP"]),  # type: ignore
            )
        ]


@pytest.mark.asyncio
async def test_provider_discovery_and_registry_normalization(tmp_path):
    # Test 6 & 7: DiscoveryManager normalizes provider model
    # capabilities and populates ModelRegistry index.
    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()

    provider = NormalizationMockProvider("mock-norm-provider")
    await provider_registry.register(provider)

    config_file = tmp_path / "providers.yaml"
    config_file.write_text("providers: {}\n")

    manager = DiscoveryManager(
        provider_registry,
        model_registry,
        config_path=config_file,
    )
    summary = await manager.discover()

    assert summary.providers_loaded == 1
    assert summary.models_discovered == 1

    model = await model_registry.get_model("model-discovered-1")
    assert model is not None
    assert model.capabilities == frozenset([Capability.CHAT, Capability.TOOLS])

    chat_models = await model_registry.list_by_capability(Capability.CHAT)
    assert len(chat_models) == 1
    assert chat_models[0].id == "model-discovered-1"

    tools_models = await model_registry.list_by_capability(Capability.TOOLS)
    assert len(tools_models) == 1
    assert tools_models[0].id == "model-discovered-1"

    embeddings_models = await model_registry.list_by_capability(Capability.EMBEDDINGS)
    assert len(embeddings_models) == 0
