import pytest

from app.providers.base import BaseProvider
from tests.fixtures.mock_provider import MockProvider


def test_mock_provider_implements_base_provider():
    provider = MockProvider("test")
    assert isinstance(provider, BaseProvider)
    # Check that mandatory methods are implemented
    assert hasattr(provider, "health")
    assert hasattr(provider, "list_models")
    assert hasattr(provider, "chat")
    assert hasattr(provider, "supports")
    assert hasattr(provider, "get_capabilities")


@pytest.mark.asyncio
async def test_mock_provider_methods():
    provider = MockProvider("test")
    assert await provider.health() is True
    assert await provider.list_models() == []
    assert await provider.chat({"model": "gpt-4"})
