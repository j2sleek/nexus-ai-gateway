import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.providers.base import BaseProvider

from .circuit_breaker import CircuitBreaker
from .retry import RetryStrategy


class ResilienceProxy(BaseProvider):
    def __init__(self, provider: BaseProvider, config: dict):
        self.provider = provider
        self.provider_name = provider.provider_name
        super().__init__()
        self.circuit_breaker = CircuitBreaker(
            threshold=config.get("failure_threshold", 5),
            recovery_timeout=config.get("recovery_timeout_seconds", 30),
            success_threshold=config.get("success_threshold", 3),
        )
        self.retry_strategy = RetryStrategy(max_attempts=config.get("retry_attempts", 3))
        self.timeout = config.get("timeout_seconds", 30)

    async def _wrap_call(self, func, *args, **kwargs):
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker OPEN")

        try:
            # Pass the total timeout to the retry strategy
            result = await self.retry_strategy.execute(func, self.timeout, *args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except Exception:
            self.circuit_breaker.record_failure()
            raise

    async def health(self) -> bool:
        try:
            # Use a short timeout for health checks
            return await asyncio.wait_for(self.provider.health(), timeout=5)
        except Exception:
            return False

    async def list_models(self) -> list[ModelInfo]:
        return await self._wrap_call(self.provider.list_models)

    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap_call(self.provider.chat, request)

    async def stream_chat(self, request: dict[str, Any]) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        # Timeout for streaming is handled during individual chunk retrieval or initial connection
        from collections.abc import AsyncGenerator
        from typing import cast

        provider_stream = self.provider.stream_chat(request)
        async for chunk in cast(AsyncGenerator[Any, None], provider_stream):
            yield chunk

    async def embeddings(self, request: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap_call(self.provider.embeddings, request)

    async def image_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap_call(self.provider.image_generation, request)

    async def audio_transcription(self, request: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap_call(self.provider.audio_transcription, request)

    async def audio_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        return await self._wrap_call(self.provider.audio_generation, request)

    def supports(self, capability: Capability) -> bool:
        return self.provider.supports(capability)

    def get_capabilities(self) -> frozenset[Capability]:
        return self.provider.get_capabilities()

    @property
    def provider_metadata(self) -> dict[str, Any]:
        return self.provider.provider_metadata
