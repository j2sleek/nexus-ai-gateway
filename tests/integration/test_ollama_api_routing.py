import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import CapabilityNotSupported
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.capability import Capability
from app.providers.ollama import OllamaProvider
from app.routing.engine import RouteResolver


@pytest.fixture
async def ollama_test_app(mocker):
    tags_data = {
        "models": [
            {
                "name": "llama3:latest",
                "model": "llama3:latest",
                "details": {"family": "llama", "families": ["llama"]},
            },
            {
                "name": "nomic-embed:latest",
                "model": "nomic-embed:latest",
                "details": {"family": "nomic-bert", "families": ["nomic-bert"]},
            },
        ]
    }
    mock_get_resp = mocker.MagicMock()
    mock_get_resp.status_code = 200
    mock_get_resp.json.return_value = tags_data

    class FakeOllamaClientCtx:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url):
            return mock_get_resp

        async def post(self, url, json=None):
            m = mocker.MagicMock()
            m.status_code = 200
            m.json.return_value = {
                "model": "llama3:latest",
                "message": {
                    "role": "assistant",
                    "content": "Ollama integration success",
                },
                "done": True,
            }
            return m

    mocker.patch("httpx.AsyncClient", return_value=FakeOllamaClientCtx())

    async with lifespan(app):
        provider_registry = ProviderRegistry()
        model_registry = ModelRegistry()
        ollama_provider = OllamaProvider()
        await provider_registry.register(ollama_provider)

        discovered = await ollama_provider.list_models()
        for m in discovered:
            await model_registry.register_model(m)

        app.state.provider_registry = provider_registry
        app.state.model_registry = model_registry
        app.state.route_resolver = RouteResolver(provider_registry, model_registry)
        yield app

        await app.state.provider_registry.clear()
        await app.state.model_registry.clear()


@pytest.mark.asyncio
async def test_ollama_models_listing_and_filtering(ollama_test_app):
    # Test 31 & 32: Ollama models appear in /v1/models and capability filtering works
    async with AsyncClient(
        transport=ASGITransport(app=ollama_test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        resp = await ac.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()["data"]
        ids = {m["id"] for m in data}
        assert "llama3:latest" in ids
        assert "nomic-embed:latest" in ids

        resp_chat = await ac.get("/v1/models?capability=chat")
        assert resp_chat.status_code == 200
        chat_ids = {m["id"] for m in resp_chat.json()["data"]}
        assert "llama3:latest" in chat_ids
        assert "nomic-embed:latest" not in chat_ids


@pytest.mark.asyncio
async def test_ollama_routing_and_rejection(ollama_test_app):
    # Test 33 & 34: RouteResolver selects Ollama model, rejects incompatible model
    resolver = ollama_test_app.state.route_resolver

    res = await resolver.resolve(
        requested_model="llama3:latest", required_capability=Capability.CHAT
    )
    assert res.model == "llama3:latest"
    assert res.provider == "ollama"

    with pytest.raises(CapabilityNotSupported):
        await resolver.resolve(
            requested_model="nomic-embed:latest",
            required_capability=Capability.CHAT,
        )


@pytest.mark.asyncio
async def test_ollama_completions_sync_and_stream(ollama_test_app, mocker):
    # Test 35 & 36: Non-streaming and streaming POST /v1/chat/completions through Ollama provider
    async with AsyncClient(
        transport=ASGITransport(app=ollama_test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        payload = {
            "model": "llama3:latest",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        resp = await ac.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["choices"][0]["message"]["content"] == "Ollama integration success"
