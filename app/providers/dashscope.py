from typing import Any

from app.models.capability import Capability
from app.providers.base import BaseProvider


class DashScopeProvider(BaseProvider):
    provider_name = "dashscope"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError


    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def stream_chat(self, request: dict[str, Any]) -> Any:
        raise NotImplementedError

    async def embeddings(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def image_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_transcription(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def supports(self, capability: Capability) -> bool:
        raise NotImplementedError

    def get_capabilities(self) -> frozenset[Capability]:
        raise NotImplementedError

    @property
    def provider_metadata(self) -> dict[str, Any]:
        raise NotImplementedError
