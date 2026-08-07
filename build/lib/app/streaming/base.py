import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from .metrics import record_stream_event


class BaseStreamNormalizer(ABC):
    """Abstract base class for streaming normalizers."""

    def __init__(self, provider_name: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name

    async def normalize_stream_with_lifecycle(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        start_time = time.time()
        record_stream_event("stream_started", self.provider_name, self.model_name)

        try:
            async for event in self.normalize_stream(provider_stream, request_data):
                yield event
            duration = time.time() - start_time
            record_stream_event("stream_completed", self.provider_name, self.model_name, duration)
        except asyncio.CancelledError:
            duration = time.time() - start_time
            record_stream_event("stream_cancelled", self.provider_name, self.model_name, duration)
            raise
        except Exception as e:
            duration = time.time() - start_time
            record_stream_event("stream_failed", self.provider_name, self.model_name, duration)
            # Normalize error termination event
            yield f'data: {{"error": "{e!s}"}}\n\n'
            raise

    @abstractmethod
    async def normalize_stream(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[str, None]: ...
