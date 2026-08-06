from dataclasses import dataclass

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.models.capability import Capability


@dataclass(frozen=True)
class RoutingResult:
    provider: str
    model: str
    reason: str
    fallback: bool
    capability_used: Capability | None


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
        # Exact model routing
        if requested_model:
            model = await self.model_registry.get_model(requested_model)
            if model:
                return RoutingResult(
                    provider=model.provider,
                    model=model.id,
                    reason="exact_match",
                    fallback=False,
                    capability_used=required_capability,
                )

        # Capability routing
        if required_capability:
            models = await self.model_registry.list_by_capability(required_capability)
            if models:
                # Simple selection: pick the first available
                model = models[0]
                return RoutingResult(
                    provider=model.provider,
                    model=model.id,
                    reason="capability_match",
                    fallback=False,
                    capability_used=required_capability,
                )

        # Fallback
        raise ValueError("No suitable model found for request")
