import litellm
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import CapabilityNotSupported
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.capability import Capability
from app.providers.litellm import LiteLLMProvider
from app.routing.engine import RouteResolver


class FakeAsyncStream:
    def __init__(self, chunks):
        self.chunks = chunks
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


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
        resp = await ac.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()["data"]
        ids = {m["id"] for m in data}
        assert "gpt-4o-litellm" in ids
        assert "embed-litellm" in ids

        resp_chat = await ac.get("/v1/models?capability=chat")
        assert resp_chat.status_code == 200
        chat_ids = {m["id"] for m in resp_chat.json()["data"]}
        assert "gpt-4o-litellm" in chat_ids
        assert "embed-litellm" not in chat_ids


@pytest.mark.asyncio
async def test_litellm_routing_capabilities_and_rejection(litellm_test_app):
    # Test 12, 19, 20: RouteResolver selects capable model, rejects incapable model
    resolver = litellm_test_app.state.route_resolver

    res_chat = await resolver.resolve(
        requested_model="gpt-4o-litellm", required_capability=Capability.CHAT
    )
    assert res_chat.model == "gpt-4o-litellm"
    assert res_chat.provider == "litellm"

    with pytest.raises(CapabilityNotSupported):
        await resolver.resolve(requested_model="embed-litellm", required_capability=Capability.CHAT)


@pytest.mark.asyncio
async def test_litellm_chat_completions_sync_and_stream(litellm_test_app, mocker):
    # Test 17 & 18: POST /v1/chat/completions sync and stream through LiteLLM provider
    mock_resp = litellm.ModelResponse(
        id="chatcmpl-999",
        model="gpt-4o-litellm",
        choices=[
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {"role": "assistant", "content": "Hello world!"},
            }
        ],
    )
    mock_acompletions = mocker.patch("litellm.acompletion", return_value=mock_resp)

    payload = {
        "model": "gpt-4o-litellm",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.5,
    }

    async with AsyncClient(
        transport=ASGITransport(app=litellm_test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        # Sync chat
        resp = await ac.post("/v1/chat/completions", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "chatcmpl-999"
        assert data["choices"][0]["message"]["content"] == "Hello world!"

        mock_acompletions.assert_called_with(
            model="gpt-4o-litellm",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
        )

        # Stream chat
        chunks = [
            litellm.ModelResponse(
                id="chatcmpl-c1",
                choices=[
                    {
                        "index": 0,
                        "delta": {"content": "Hello"},
                        "finish_reason": None,
                    }
                ],
            ),
            litellm.ModelResponse(
                id="chatcmpl-c2",
                choices=[
                    {
                        "index": 0,
                        "delta": {"content": " stream"},
                        "finish_reason": "stop",
                    }
                ],
            ),
        ]
        mocker.patch("litellm.acompletion", return_value=FakeAsyncStream(chunks))
        payload_stream = {**payload, "stream": True}

        resp_stream = await ac.post("/v1/chat/completions", json=payload_stream)
        assert resp_stream.status_code == 200
        assert "text/event-stream" in resp_stream.headers["content-type"]
        text = resp_stream.text
        assert "Hello" in text
        assert "stream" in text
        assert "[DONE]" in text
