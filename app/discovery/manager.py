from __future__ import annotations

from pathlib import Path

import yaml

from app.core.registry import ProviderRegistry
from app.providers import PROVIDERS
from app.models import ModelRegistry

class DiscoveryManager:
    """
    Loads enabled providers from configuration and registers them.

    Model discovery is handled separately by the discovery scheduler.
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelRegistry,
        config_path: str | Path = "config/providers.yaml",
    ) -> None:
        self.registry = registry
        self.config_path = Path(config_path)

    async def discover(self) -> DiscoverySummary:
    """
    Load providers, perform health checks,
    discover models and populate the registry.
    """

        with self.config_path.open("r", encoding="utf-8") as fp:
            config = yaml.safe_load(fp) or {}

        providers = config.get("providers", {})

        for name, settings in providers.items():
            if not settings.get("enabled", False):
                continue

            provider_cls = PROVIDERS.get(name)

            if provider_cls is None:
                continue

            self.registry.register(provider_cls())

        return self.registry
