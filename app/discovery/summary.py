from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class DiscoverySummary:
    providers_loaded: int
    providers_healthy: int
    providers_failed: int
    models_discovered: int
