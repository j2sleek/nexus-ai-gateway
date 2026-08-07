import pytest

from app.models.model_info import ModelInfo


@pytest.mark.asyncio
async def test_model_registration(model_registry):
    model = ModelInfo(id="test-model", provider="test-provider", display_name="Test Model")
    await model_registry.register_model(model)
    assert await model_registry.exists("test-model")
    assert await model_registry.get_model("test-model") == model


@pytest.mark.asyncio
async def test_duplicate_registration(model_registry):
    model = ModelInfo(id="test-model", provider="test-provider", display_name="Test Model")
    await model_registry.register_model(model)
    with pytest.raises(ValueError):
        await model_registry.register_model(model)
