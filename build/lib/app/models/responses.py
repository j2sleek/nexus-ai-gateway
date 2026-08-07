from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class UsageInfo:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    estimated_cost: float | None = None


@dataclass(slots=True, frozen=True)
class TimingInfo:
    queue_ms: float = 0.0

    routing_ms: float = 0.0

    provider_ms: float = 0.0

    total_ms: float = 0.0


@dataclass(slots=True, frozen=True)
class ModelSelection:
    provider: str

    model: str

    reason: str

    fallback: bool = False


@dataclass(slots=True, frozen=True)
class ResponseContent:
    content: str
    tool_calls: tuple[Any, ...]
    finish_reason: str


@dataclass(slots=True, frozen=True)
class GatewayResponse:
    selection: ModelSelection

    content: ResponseContent

    usage: UsageInfo

    timing: TimingInfo

    metadata: dict[str, object]
