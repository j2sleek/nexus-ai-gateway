import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app, lifespan
from app.models.model_info import ModelInfo
from app.routing.engine import RouteResolver
from tests.fixtures.mock_provider import MockProvider


@pytest.fixture
async def app_with_provider(provider_registry, model_registry):
    app = create_app()
    async with lifespan(app):
        provider = MockProvider("litellm")
        provider.is_healthy = True
        await provider_registry.register(provider)

        app.state.provider_registry = provider_registry
        app.state.model_registry = model_registry
        app.state.route_resolver = RouteResolver(provider_registry, model_registry)

        yield app

        await provider_registry.clear()
        await model_registry.clear()


@pytest.mark.asyncio
async def test_anthropic_messages_compatibility(app_with_provider, model_registry):
    model = ModelInfo(id="claude-3-opus", provider="litellm", display_name="Claude 3 Opus")
    await model_registry.register_model(model)

    payload = {
        "model": "claude-3-opus",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello Anthropic!"}],
    }

    async with AsyncClient(
        transport=ASGITransport(app=app_with_provider), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/anthropic/messages", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "message"
