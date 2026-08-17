from __future__ import annotations

import logging
from pathlib import Path

import yaml

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.normalizer import normalize_capabilities
from app.discovery.summary import DiscoverySummary
from app.models.model_info import ModelInfo

logger = logging.getLogger(__name__)


class DiscoveryManager:
    """
    Loads enabled providers from configuration and registers them.

    Performs health checks, discovers models from providers, normalizes capabilities,
    and populates the model registry.
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
        if self.config_path.exists():
            with self.config_path.open("r", encoding="utf-8") as fp:
                config = yaml.safe_load(fp) or {}
        else:
            config = {}

        providers_config = config.get("providers", {})

        providers_loaded = 0
        providers_healthy = 0
        providers_failed = 0

        for provider in self.provider_registry:
            settings = providers_config.get(provider.name, {})
            if providers_config and not settings.get("enabled", False):
                continue

            providers_loaded += 1

            # Health check
            try:
                is_healthy = await provider.health()
            except Exception:
                is_healthy = False

            if not is_healthy:
                providers_failed += 1
                continue

            providers_healthy += 1

            # List models
            try:
                provider_models = await provider.list_models()
            except NotImplementedError:
                continue
            except Exception:
                logger.exception("Failed to list models for provider %s", provider.name)
                providers_failed += 1
                continue

            for model_info in provider_models:
                normalized_caps = normalize_capabilities(model_info.capabilities)
                updated_model = ModelInfo(
                    id=model_info.id,
                    provider=model_info.provider,
                    display_name=model_info.display_name,
                    context_window=model_info.context_window,
                    max_output_tokens=model_info.max_output_tokens,
                    input_cost_per_million=model_info.input_cost_per_million,
                    output_cost_per_million=model_info.output_cost_per_million,
                    capabilities=normalized_caps,
                    modalities=model_info.modalities,
                    supports_streaming=model_info.supports_streaming,
                    supports_tools=model_info.supports_tools,
                    supports_vision=model_info.supports_vision,
                    supports_audio=model_info.supports_audio,
                    supports_embeddings=model_info.supports_embeddings,
                    supports_reasoning=model_info.supports_reasoning,
                    status=model_info.status,
                    priority=model_info.priority,
                    tags=model_info.tags,
                )
                try:
                    if not await self.model_registry.exists(updated_model.id):
                        await self.model_registry.register_model(updated_model)
                except Exception:
                    logger.exception("Failed to register discovered model %s", updated_model.id)

        models = await self.model_registry.list_models()
        return DiscoverySummary(
            providers_loaded=providers_loaded,
            providers_healthy=providers_healthy,
            providers_failed=providers_failed,
            models_discovered=len(models),
        )

    async def is_ready(self) -> bool:
        """Check if discovery is complete and gateway is ready."""
        return len(self.provider_registry) > 0
