from __future__ import annotations

from pathlib import Path

import yaml

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.summary import DiscoverySummary


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
        self.provider_registry = provider_registry
        self.model_registry = model_registry
        self.config_path = Path(config_path)

    async def discover(self) -> DiscoverySummary:
        """
        Load providers, perform health checks,
        discover models and populate the registry.
        """
        with self.config_path.open("r", encoding="utf-8") as fp:
            config = yaml.safe_load(fp) or {}

        providers_config = config.get("providers", {})

        # Registry already contains registered provider instances.
        for provider in self.provider_registry:
            settings = providers_config.get(provider.name, {})
            if not settings.get("enabled", False):
                continue

            # In a full implementation, perform health checks here.
            # ...

        return DiscoverySummary(
            providers_loaded=0,
            providers_healthy=0,
            providers_failed=0,
            models_discovered=0,
        )
