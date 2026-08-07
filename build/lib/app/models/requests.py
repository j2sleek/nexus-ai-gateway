from dataclasses import dataclass, field

from app.models.capability import Capability
from app.models.task import TaskType


@dataclass(slots=True, frozen=True)
class GenerationConfig:
    temperature: float | None = None

    top_p: float | None = None

    max_tokens: int | None = None

    stop: tuple[str, ...] = ()

    seed: int | None = None

    stream: bool = False

    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class RoutingPreferences:
    preferred_provider: str | None = None

    preferred_model: str | None = None

    required_capabilities: frozenset[Capability] = field(default_factory=frozenset)

    excluded_providers: frozenset[str] = field(default_factory=frozenset)


@dataclass(slots=True, frozen=True)
class GatewayRequest:
    task: TaskType

    messages: tuple[dict[str, object], ...]

    routing: RoutingPreferences

    generation: GenerationConfig

    metadata: dict[str, object] = field(default_factory=dict)
