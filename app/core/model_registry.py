import asyncio
from collections import defaultdict

from app.models.capability import Capability
from app.models.model_info import ModelInfo


class ModelRegistry:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._models: dict[str, ModelInfo] = {}
        # Indexes
        self._by_provider: dict[str, set[str]] = defaultdict(set)
        self._by_capability: dict[Capability, set[str]] = defaultdict(set)
        self._by_modality: dict[str, set[str]] = defaultdict(set)

    async def register_provider(self, provider: str) -> None:
        async with self._lock:
            if provider not in self._by_provider:
                self._by_provider[provider] = set()

    async def unregister_provider(self, provider: str) -> None:
        async with self._lock:
            model_ids = self._by_provider.pop(provider, set())
            for model_id in model_ids:
                if model_id in self._models:
                    model = self._models.pop(model_id)
                    self._remove_from_indexes(model)

    async def register_model(self, model: ModelInfo) -> None:
        async with self._lock:
            if model.id in self._models:
                raise ValueError(f"Model {model.id} already registered.")
            self._models[model.id] = model
            self._add_to_indexes(model)

    async def unregister_model(self, model_id: str) -> None:
        async with self._lock:
            model = self._models.pop(model_id, None)
            if model:
                self._remove_from_indexes(model)

    async def get_model(self, model_id: str) -> ModelInfo | None:
        async with self._lock:
            return self._models.get(model_id)

    async def list_models(self) -> list[ModelInfo]:
        async with self._lock:
            return list(self._models.values())

    async def list_by_provider(self, provider: str) -> list[ModelInfo]:
        async with self._lock:
            model_ids = self._by_provider.get(provider, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def list_by_capability(self, capability: Capability) -> list[ModelInfo]:
        async with self._lock:
            model_ids = self._by_capability.get(capability, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def list_by_modality(self, modality: str) -> list[ModelInfo]:
        async with self._lock:
            model_ids = self._by_modality.get(modality, set())
            return [self._models[mid] for mid in model_ids if mid in self._models]

    async def search(self, query: str) -> list[ModelInfo]:
        query = query.lower()
        async with self._lock:
            return [
                m
                for m in self._models.values()
                if query in m.id.lower() or query in m.display_name.lower()
            ]

    async def exists(self, model_id: str) -> bool:
        async with self._lock:
            return model_id in self._models

    async def clear(self) -> None:
        async with self._lock:
            self._models.clear()
            self._by_provider.clear()
            self._by_capability.clear()
            self._by_modality.clear()

    # Helpers
    def _add_to_indexes(self, model: ModelInfo) -> None:
        self._by_provider[model.provider].add(model.id)
        for cap in model.capabilities:
            self._by_capability[cap].add(model.id)
        for mod in model.modalities:
            self._by_modality[mod].add(model.id)

    def _remove_from_indexes(self, model: ModelInfo) -> None:
        if model.provider in self._by_provider:
            self._by_provider[model.provider].discard(model.id)
        for cap in model.capabilities:
            self._by_capability[cap].discard(model.id)
        for mod in model.modalities:
            self._by_modality[mod].discard(model.id)
