import httpx
import pytest

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.manager import DiscoveryManager
from app.models.capability import Capability
from app.providers.ollama import OllamaProvider


class FakeGetClientCtx:
    def __init__(self, resp=None, side_effect=None):
        self.resp = resp
        self.side_effect = side_effect

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def get(self, url):
        if self.side_effect:
            raise self.side_effect
        return self.resp


@pytest.fixture
def mock_ollama_tags():
    return {
        "models": [
            {
                "name": "llama3:latest",
                "model": "llama3:latest",
                "details": {
                    "family": "llama",
                    "families": ["llama"],
                },
            },
            {
                "name": "nomic-embed-text:latest",
                "model": "nomic-embed-text:latest",
                "details": {
                    "family": "nomic-bert",
                    "families": ["nomic-bert"],
                },
            },
            {
                "name": "llava:latest",
                "model": "llava:latest",
                "details": {
                    "family": "llama",
                    "families": ["llama", "clip"],
                },
            },
            {
                "name": "unknown-model",
                "model": "unknown-model",
                "details": {},
            },
        ]
    }


@pytest.mark.asyncio
async def test_ollama_basic_and_multiple_model_discovery(mocker, mock_ollama_tags):
    # Test 1, 2, 3, 4, 6: Discovery, multiple models, exact ID,
    # provider identity, capability normalization
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_ollama_tags
    mocker.patch("httpx.AsyncClient", return_value=FakeGetClientCtx(resp=mock_resp))

    provider = OllamaProvider()
    models = await provider.list_models()

    assert len(models) == 4
    model_ids = {m.id for m in models}
    assert model_ids == {
        "llama3:latest",
        "nomic-embed-text:latest",
        "llava:latest",
        "unknown-model",
    }

    for m in models:
        assert m.provider == "ollama"

    models_map = {m.id: m for m in models}
    assert Capability.CHAT in models_map["llama3:latest"].capabilities
    assert Capability.EMBEDDINGS in models_map["nomic-embed-text:latest"].capabilities
    assert Capability.CHAT in models_map["llava:latest"].capabilities
    assert Capability.VISION in models_map["llava:latest"].capabilities
    assert models_map["unknown-model"].capabilities == frozenset()


@pytest.mark.asyncio
async def test_ollama_discovery_manager_integration(mocker, mock_ollama_tags, tmp_path):
    # Test 11, 12, 13: Discovery failure isolation, ModelRegistry registration, capability indexing
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_ollama_tags
    mocker.patch("httpx.AsyncClient", return_value=FakeGetClientCtx(resp=mock_resp))

    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()

    provider = OllamaProvider()
    await provider_registry.register(provider)

    config_file = tmp_path / "providers.yaml"
    config_file.write_text("providers:\n  ollama:\n    enabled: true\n")

    manager = DiscoveryManager(provider_registry, model_registry, config_path=config_file)
    summary = await manager.discover()

    assert summary.providers_loaded == 1
    assert summary.models_discovered == 4

    chat_models = await model_registry.list_by_capability(Capability.CHAT)
    assert len(chat_models) >= 2


@pytest.mark.asyncio
async def test_ollama_health_and_unavailable(mocker):
    # Test 11: Ollama unavailable handling
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 200
    mocker.patch("httpx.AsyncClient", return_value=FakeGetClientCtx(resp=mock_resp))

    provider = OllamaProvider()
    assert await provider.health() is True

    mocker.patch(
        "httpx.AsyncClient",
        return_value=FakeGetClientCtx(side_effect=httpx.ConnectError("Connection refused")),
    )
    assert await provider.health() is False
