import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.model_info import ModelInfo


@pytest.mark.asyncio
async def test_list_models_compatibility(model_registry):
    model = ModelInfo(id="gpt-4", provider="litellm", display_name="GPT-4")
    await model_registry.register_model(model)

    # Use AsyncClient with ASGITransport to test the app directly
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "gpt-4"
    assert data["data"][0]["object"] == "model"
    assert data["data"][0]["owned_by"] == "litellm"
