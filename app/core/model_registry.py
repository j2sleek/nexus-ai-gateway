from collections.abc import Iterable

from app.models.capability import Capability
from app.models.model_info import ModelInfo


class ModelRegistry:
    def register(self, model: ModelInfo) -> None:
        pass

    def register_many(self, models: Iterable[ModelInfo]) -> None:
        pass

    def get(self, model_id: str) -> ModelInfo | None:
        pass

    def all(self) -> list[ModelInfo]:
        pass

    def providers(self) -> list[str]:
        pass

    def by_provider(self, provider: str) -> list[ModelInfo]:
        pass

    def by_capability(self, capability: Capability) -> list[ModelInfo]:
        pass

    def clear(self) -> None:
        pass
