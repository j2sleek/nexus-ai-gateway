import logging
from dataclasses import dataclass

from app.core.exceptions import (
    CapabilityNotSupported,
    ModelNotFound,
    NoHealthyProvider,
    RoutingFailure,
)
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.models.capability import Capability
from app.models.model_info import ModelInfo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoutingResult:
    provider: str
    model: str
    capability_used: Capability | None
    fallback_used: bool
    routing_reason: str


class RouteResolver:
    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelRegistry,
    ) -> None:
        self.provider_registry = provider_registry
        self.model_registry = model_registry

    async def resolve(
        self,
        requested_model: str | None = None,
        required_capability: Capability | None = None,
    ) -> RoutingResult:
        candidates = await self._generate_candidates(requested_model, required_capability)
        healthy_candidates = await self._filter_healthy(candidates)

        if not healthy_candidates:
            raise NoHealthyProvider("No healthy providers available.")

        # Deterministic selection: rank by priority
        ranked = sorted(healthy_candidates, key=lambda m: m.priority, reverse=True)
        selected = ranked[0]

        logger.info(
            "Routing decision",
            provider=selected.provider,
            model=selected.id,
            reason="success",
            fallback=len(ranked) > 1,
        )

        return RoutingResult(
            provider=selected.provider,
            model=selected.id,
            capability_used=required_capability,
            fallback_used=len(ranked) > 1,
            routing_reason="success",
        )

    async def _generate_candidates(
        self, requested_model: str | None, required_capability: Capability | None
    ) -> list[ModelInfo]:
        if requested_model:
            model = await self.model_registry.get_model(requested_model)
            if not model:
                raise ModelNotFound(f"Model {requested_model} not found.")
            return [model]

        if required_capability:
            models = await self.model_registry.list_by_capability(required_capability)
            if not models:
                raise CapabilityNotSupported(
                    f"No models support capability {required_capability.value}."
                )
            return models

        raise RoutingFailure("Must specify model or capability.")

    async def _filter_healthy(self, models: list[ModelInfo]) -> list[ModelInfo]:
        healthy_models = []
        for model in models:
            provider = self.provider_registry.get(model.provider)
            if provider and await provider.health():
                healthy_models.append(model)
        return healthy_models
