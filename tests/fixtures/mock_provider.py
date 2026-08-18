from collections.abc import AsyncGenerator
from typing import Any

from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.providers.base import BaseProvider


class MockProvider(BaseProvider):
    def __init__(self, name: str, is_healthy: bool = True, latency: float = 0.0):
        self.provider_name = name
        super().__init__()
        self.is_healthy = is_healthy
        self.latency = latency

    async def health(self) -> bool:
        return self.is_healthy

    async def list_models(self) -> list[ModelInfo]:
        return []

    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "chatcmpl-123",
            "model": request.get("model", "gpt-4"),
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response from the provider.",
                    }
                }
            ],
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }

    async def stream_chat(self, request: dict[str, Any]) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        yield {"content": "chunk"}

    async def embeddings(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def image_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_transcription(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def supports(self, capability: Capability) -> bool:
        return True

    def get_capabilities(self) -> frozenset[Capability]:
        return frozenset([Capability.CHAT])

    @property
    def provider_metadata(self) -> dict[str, Any]:
        return {"is_mock": True}
