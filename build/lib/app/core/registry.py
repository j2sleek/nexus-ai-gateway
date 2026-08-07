from __future__ import annotations

from collections.abc import Iterator

from app.core.config import settings
from app.providers.base import BaseProvider
from app.resilience.proxy import ResilienceProxy


class ProviderRegistry:
    """
    Stores and manages provider instances.

    The registry owns provider objects and exposes a simple API for
    registering, retrieving and iterating over them.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._router_config = settings.load_router()
        self._resilience_config = self._router_config.get("policies", {}).get("circuit_breaker", {})

    async def register(self, provider: BaseProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        """Remove a provider."""
        self._providers.pop(name, None)

    def get(self, name: str) -> BaseProvider | None:
        """Retrieve a provider by name, wrapped in resilience proxy."""
        provider = self._providers.get(name)
        if provider:
            return ResilienceProxy(provider, self._resilience_config)
        return None

    def exists(self, name: str) -> bool:
        """Check if a provider exists."""
        return name in self._providers

    def list(self) -> list[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def names(self) -> list[str]:
        """Return provider names."""
        return sorted(self._providers.keys())

    async def clear(self) -> None:
        """Remove every provider."""
        self._providers.clear()

    def __iter__(self) -> Iterator[BaseProvider]:
        return iter(self._providers.values())

    def __len__(self) -> int:
        return len(self._providers)
