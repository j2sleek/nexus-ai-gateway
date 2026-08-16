from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from app.models.capability import Capability
from app.models.model_info import ModelInfo


class BaseProvider(ABC):
    """
    Base interface implemented by every AI provider.
    """

    provider_name: str

    def __init__(self) -> None:
        self.name = self.provider_name

    @abstractmethod
    async def health(self) -> bool:
        """Return True if the provider is reachable."""
        ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """Return the models exposed by this provider."""
        ...

    @abstractmethod
    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a chat completion request."""
        ...

    @abstractmethod
    async def stream_chat(self, request: dict[str, Any]) -> AsyncGenerator[Any, None]:
        """Execute a streaming chat completion request."""
        ...

    @abstractmethod
    async def embeddings(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate embeddings."""
        ...

    @abstractmethod
    async def image_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate images."""
        ...

    @abstractmethod
    async def audio_transcription(self, request: dict[str, Any]) -> dict[str, Any]:
        """Transcribe audio."""
        ...

    @abstractmethod
    async def audio_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate audio."""
        ...

    @abstractmethod
    def supports(self, capability: Capability) -> bool:
        """Check if provider supports a capability."""
        ...

    @abstractmethod
    def get_capabilities(self) -> frozenset[Capability]:
        """Return all supported capabilities."""
        ...

    @property
    @abstractmethod
    def provider_metadata(self) -> dict[str, Any]:
        """Return provider-specific metadata."""
        ...
