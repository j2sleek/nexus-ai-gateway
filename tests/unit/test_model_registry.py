import pytest

from app.core.model_registry import ModelRegistry
from app.models.capability import Capability
from app.models.model_info import ModelInfo


@pytest.fixture
def model_registry():
    return ModelRegistry()


@pytest.mark.asyncio
async def test_register_model(model_registry):
    model = ModelInfo(id="test-model", provider="test", display_name="Test")
    await model_registry.register_model(model)
    assert await model_registry.exists("test-model")
    assert await model_registry.get_model("test-model") is model


@pytest.mark.asyncio
async def test_duplicate_registration(model_registry):
    model = ModelInfo(id="test", provider="test", display_name="Test")
    await model_registry.register_model(model)
    with pytest.raises(ValueError):
        await model_registry.register_model(model)


@pytest.mark.asyncio
async def test_unregister_model(model_registry):
    model = ModelInfo(id="test", provider="test", display_name="Test")
    await model_registry.register_model(model)
    await model_registry.unregister_model("test")
    assert not await model_registry.exists("test")
    assert len(await model_registry.list_models()) == 0


@pytest.mark.asyncio
async def test_list_models(model_registry):
    models = [ModelInfo(id=f"m{i}", provider=f"p{i}", display_name=f"M{i}") for i in range(3)]
    for m in models:
        await model_registry.register_model(m)
    all_models = await model_registry.list_models()
    assert len(all_models) == 3


@pytest.mark.asyncio
async def test_list_by_capability(model_registry):
    model1 = ModelInfo(
        id="m1", provider="p1", display_name="M1", capabilities=frozenset([Capability.CHAT])
    )
    model2 = ModelInfo(
        id="m2", provider="p2", display_name="M2", capabilities=frozenset([Capability.CHAT])
    )
    model3 = ModelInfo(
        id="m3", provider="p3", display_name="M3", capabilities=frozenset([Capability.REASONING])
    )
    for m in [model1, model2, model3]:
        await model_registry.register_model(m)
    chat_models = await model_registry.list_by_capability(Capability.CHAT)
    assert len(chat_models) == 2
