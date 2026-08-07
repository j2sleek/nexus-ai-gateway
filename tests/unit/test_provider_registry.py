import pytest


@pytest.mark.asyncio
async def test_register_unregister_provider(provider_registry, mock_provider):
    await provider_registry.register(mock_provider)
    assert provider_registry.exists(mock_provider.name)
    provider_registry.unregister(mock_provider.name)
    assert not provider_registry.exists(mock_provider.name)


@pytest.mark.asyncio
async def test_clear_registry(provider_registry, mock_provider):
    await provider_registry.register(mock_provider)
    assert provider_registry.exists(mock_provider.name)
    await provider_registry.clear()
    assert not provider_registry.exists(mock_provider.name)
