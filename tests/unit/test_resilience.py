import time

import pytest

from app.models.capability import Capability
from app.resilience.circuit_breaker import CircuitBreaker, CircuitState
from app.resilience.proxy import ResilienceProxy

# =============================================================================
# CircuitBreaker Tests
# =============================================================================


class TestCircuitBreaker:
    def test_closed_to_open(self):
        cb = CircuitBreaker(threshold=2, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_recovery(self):
        cb = CircuitBreaker(threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        # Simulate recovery timeout passing
        cb.last_failure_time = time.time() - 0.06
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_success_threshold(self):
        cb = CircuitBreaker(threshold=1, recovery_timeout=0.01, success_threshold=2)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        cb.last_failure_time = time.time() - 0.02
        assert cb.can_execute() is True
        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED


# =============================================================================
# ResilienceProxy Tests
# =============================================================================


class MockProvider:
    provider_name = "mock"

    def __init__(self):
        self.chat_calls = 0

    async def chat(self, request):
        self.chat_calls += 1
        if self.chat_calls == 1:
            raise ConnectionError("Temporary")
        return {"id": "123", "choices": [{"message": {"content": "ok"}}]}

    async def stream_chat(self, request):
        yield {"content": "chunk"}

    async def health(self):
        return True

    async def list_models(self):
        return []

    async def embeddings(self, request):
        return {}

    async def image_generation(self, request):
        return {}

    async def audio_transcription(self, request):
        return {}

    async def audio_generation(self, request):
        return {}

    def supports(self, capability):
        return True

    def get_capabilities(self):
        return frozenset([Capability.CHAT])

    @property
    def provider_metadata(self):
        return {}


@pytest.mark.asyncio
async def test_proxy_retry():
    config = {"retry_attempts": 2, "timeout_seconds": 10, "failure_threshold": 3}
    provider = MockProvider()
    proxy = ResilienceProxy(provider, config)
    result = await proxy.chat({"model": "test"})
    assert result["id"] == "123"
    assert provider.chat_calls == 2


@pytest.mark.asyncio
async def test_proxy_stream():
    config = {"retry_attempts": 0, "timeout_seconds": 1}
    provider = MockProvider()
    proxy = ResilienceProxy(provider, config)
    chunks = []
    async for chunk in proxy.stream_chat({"model": "test"}):
        chunks.append(chunk)
    assert len(chunks) == 1
