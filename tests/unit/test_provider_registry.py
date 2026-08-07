import pytest


@pytest.mark.asyncio
async def test_register_unregister_provider(provider_registry, mock_provider):
    provider_registry.register(mock_provider)
    assert provider_registry.exists(mock_provider.name)
    provider_registry.unregister(mock_provider.name)
    assert not provider_registry.exists(mock_provider.name)
