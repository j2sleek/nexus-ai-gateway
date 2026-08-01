from __future__ import annotations

from dataclasses import dataclass, field

from app.models.capability import Capability


@dataclass(slots=True, frozen=True)
class ModelInfo:
    """
    Canonical representation of an AI model inside Nexus AI Gateway.

    Every provider must normalize its model metadata into this structure.
    """

    # Required identifiers
    id: str
    provider: str
    display_name: str

    # Token limits
    context_window: int | None = None
    max_output_tokens: int | None = None

    # Pricing (optional)
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None

    # Runtime metadata
    capabilities: frozenset[Capability] = field(default_factory=frozenset)

    # Free-form provider metadata
    metadata: dict[str, object] = field(default_factory=dict)

    def has(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def supports_all(
        self,
        capabilities: set[Capability],
    ) -> bool:
        return capabilities.issubset(self.capabilities)

    def supports_any(
        self,
        capabilities: set[Capability],
    ) -> bool:
        return bool(self.capabilities & capabilities)
