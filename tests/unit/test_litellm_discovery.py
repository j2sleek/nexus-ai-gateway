import pytest

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.manager import DiscoveryManager
from app.models.capability import Capability
from app.providers.litellm import LiteLLMProvider


@pytest.fixture
def mock_litellm_cost_map(mocker):
    fake_cost_map = {
        "gpt-4o": {
            "mode": "chat",
            "supports_function_calling": True,
            "supports_vision": True,
            "max_input_tokens": 128000,
            "max_output_tokens": 4096,
            "input_cost_per_token": 0.000005,
            "output_cost_per_token": 0.000015,
        },
        "text-embedding-3-small": {
            "mode": "embedding",
            "max_input_tokens": 8191,
            "input_cost_per_token": 0.00000002,
        },
        "custom-multimodal-model": {
            "mode": "chat",
            "supports_audio_input": True,
            "supports_reasoning": True,
            "unknown_feature_flag": "some-value",
        },
        "duplicate-cap-model": {
            "mode": "chat",
            "supports_tool_choice": True,
            "supports_function_calling": True,
        },
        "no-cap-metadata-model": {},
        "sample_spec": {
            "mode": "sample",
        },
    }
    mocker.patch("litellm.model_cost", fake_cost_map)
    return fake_cost_map


@pytest.mark.asyncio
async def test_litellm_basic_and_multiple_model_discovery(mock_litellm_cost_map):
    # Test 1, 2, 7: Basic model discovery, multiple models, provider identity
    provider = LiteLLMProvider()
    models = await provider.list_models()

    assert len(models) == 5
    model_ids = {m.id for m in models}
    assert model_ids == {
        "gpt-4o",
        "text-embedding-3-small",
        "custom-multimodal-model",
        "duplicate-cap-model",
        "no-cap-metadata-model",
    }

    for m in models:
        assert m.provider == "litellm"


@pytest.mark.asyncio
async def test_litellm_capability_metadata_normalization(mock_litellm_cost_map):
    # Test 3: Native capability metadata normalizes to canonical Capability enums
    provider = LiteLLMProvider()
    models = {m.id: m for m in await provider.list_models()}

    gpt4o = models["gpt-4o"]
    assert gpt4o.capabilities == frozenset(
        [
            Capability.CHAT,
            Capability.TOOLS,
            Capability.FUNCTION_CALLING,
            Capability.VISION,
        ]
    )
    assert gpt4o.context_window == 128000
    assert gpt4o.max_output_tokens == 4096
    assert gpt4o.input_cost_per_million == 5.0
    assert gpt4o.output_cost_per_million == 15.0

    embed_model = models["text-embedding-3-small"]
    assert embed_model.capabilities == frozenset([Capability.EMBEDDINGS])


@pytest.mark.asyncio
async def test_litellm_unknown_and_duplicate_capabilities(mock_litellm_cost_map):
    # Test 4 & 5: Unknown capability ignored, duplicate capability deduplicated
    provider = LiteLLMProvider()
    models = {m.id: m for m in await provider.list_models()}

    multimodal = models["custom-multimodal-model"]
    assert Capability.CHAT in multimodal.capabilities
    assert Capability.AUDIO_INPUT in multimodal.capabilities
    assert Capability.REASONING in multimodal.capabilities

    dup_model = models["duplicate-cap-model"]
    assert Capability.TOOLS in dup_model.capabilities


@pytest.mark.asyncio
async def test_litellm_missing_capability_metadata(mock_litellm_cost_map):
    # Test 6: Model with no capability metadata has empty frozenset (no fabricated CHAT)
    provider = LiteLLMProvider()
    models = {m.id: m for m in await provider.list_models()}

    no_cap_model = models["no-cap-metadata-model"]
    assert no_cap_model.capabilities == frozenset()


@pytest.mark.asyncio
async def test_litellm_discovery_manager_and_registry_integration(mock_litellm_cost_map, tmp_path):
    # Test 8 & 9: DiscoveryManager runs LiteLLMProvider,
    # populates ModelRegistry and capability index
    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()

    provider = LiteLLMProvider()
    await provider_registry.register(provider)

    config_file = tmp_path / "providers.yaml"
    config_file.write_text("providers:\n  litellm:\n    enabled: true\n")

    manager = DiscoveryManager(provider_registry, model_registry, config_path=config_file)
    summary = await manager.discover()

    assert summary.providers_loaded == 1
    assert summary.models_discovered == 5

    gpt4o = await model_registry.get_model("gpt-4o")
    assert gpt4o is not None
    assert gpt4o.provider == "litellm"

    chat_models = await model_registry.list_by_capability(Capability.CHAT)
    chat_ids = {m.id for m in chat_models}
    assert "gpt-4o" in chat_ids
    assert "text-embedding-3-small" not in chat_ids

    embed_models = await model_registry.list_by_capability(Capability.EMBEDDINGS)
    embed_ids = {m.id for m in embed_models}
    assert "text-embedding-3-small" in embed_ids
    assert "gpt-4o" not in embed_ids


@pytest.mark.asyncio
async def test_litellm_discovery_failure_isolation(mocker, tmp_path):
    # Test 13: Provider isolation when LiteLLM discovery fails
    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()

    failing_provider = LiteLLMProvider()
    mocker.patch.object(
        failing_provider,
        "list_models",
        side_effect=RuntimeError("LiteLLM catalog error"),
    )
    await provider_registry.register(failing_provider)

    config_file = tmp_path / "providers.yaml"
    config_file.write_text("providers:\n  litellm:\n    enabled: true\n")

    manager = DiscoveryManager(provider_registry, model_registry, config_path=config_file)
    summary = await manager.discover()

    assert summary.providers_failed == 1


@pytest.mark.asyncio
async def test_litellm_health_and_missing_credentials(mocker):
    # Test 14: Health check and missing credentials handling
    provider = LiteLLMProvider()
    assert await provider.health() is True

    mocker.patch("litellm.model_cost", None)
    assert await provider.health() is False
    assert await provider.list_models() == []
