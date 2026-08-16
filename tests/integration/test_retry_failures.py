import pytest
from httpx import ASGITransport, AsyncClient

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.model_info import ModelInfo
from app.routing.engine import RouteResolver
from tests.fixtures.mock_provider import MockProvider


class FailingProvider(MockProvider):
    async def chat(self, request: dict) -> dict:
        raise Exception("503 Temporary Service Unavailable")


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
async def test_chat_completion_retry_exhaustion(test_app, mocker):
    model = ModelInfo(id="gpt-4", provider="failing-provider", display_name="GPT-4")
    await test_app.state.model_registry.register_model(model)

    provider = FailingProvider("failing-provider")
    await test_app.state.provider_registry.register(provider)

    # Spy on the provider's chat method
    chat_spy = mocker.spy(provider, "chat")

    payload = {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"X-API-Key": "test-key-12345"},
    ) as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    # Expect 500 status on exhaustion
    assert response.status_code == 500
    # Current behavior exposes the exception in the detail
    assert "Internal server error" in response.json()["detail"]
    assert "Exhausted 3 attempts" in response.json()["detail"]

    # 3 attempts (1 initial + 2 retries)
    assert chat_spy.call_count == 3
