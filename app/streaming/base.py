"""
Base streaming normalizer interface.

Responsibilities:
- Transform provider-agnostic chunks into normalized events
- Handle cancellation and errors
- Provide streaming context (provider, model, etc.)
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any


class BaseStreamNormalizer(ABC):
    """Abstract base class for streaming normalizers."""

    def __init__(self, provider_name: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name

    @abstractmethod
    async def normalize_stream(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[Any, None]:
        """
        Normalize provider stream into API-specific events.

        Args:
            provider_stream: Async iterator of raw provider chunks
            request_data: Original request body for context

        Returns:
            AsyncGenerator yielding normalized events
        """
        ...

    def _check_cancellation(self, request: Any) -> bool:
        """Check if client disconnected."""
        return request.is_disconnected()
