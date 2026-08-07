import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import RoutingError
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.main import app, lifespan
from app.models.model_info import ModelInfo
from app.routing.engine import RouteResolver


@pytest.fixture
async def test_app():
    """Fixture to provide an app instance with populated state."""
    async with lifespan(app):
        # Populate app state for testing
        app.state.provider_registry = ProviderRegistry()
        app.state.model_registry = ModelRegistry()
        app.state.route_resolver = RouteResolver(
            app.state.provider_registry,
            app.state.model_registry,
        )
        yield app
        # Cleanup
        app.state.provider_registry.clear()
        app.state.model_registry.clear()


@pytest.mark.asyncio
async def test_list_models_compatibility(test_app):
    model = ModelInfo(id="gpt-4", provider="litellm", display_name="GPT-4")
    await app.state.model_registry.register_model(model)

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "gpt-4"
    assert data["data"][0]["object"] == "model"
    assert data["data"][0]["owned_by"] == "litellm"


@pytest.mark.asyncio
async def test_chat_completion_unknown_model(test_app, mocker):
    mocker.patch.object(
        app.state.route_resolver, "resolve", side_effect=RoutingError("Model not found")
    )

    payload = {"model": "non-existent", "messages": [{"role": "user", "content": "Hello"}]}

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        response = await ac.post("/v1/chat/completions", json=payload)

    assert response.status_code == 404
