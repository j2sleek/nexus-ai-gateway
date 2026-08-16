import asyncio
from collections.abc import AsyncGenerator

import pytest

from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.providers.base import BaseProvider
from app.resilience.circuit_breaker import CircuitBreaker, CircuitState
from app.resilience.proxy import ResilienceProxy
from app.resilience.retry import RetryExhausted, RetryStrategy


class MockProvider(BaseProvider):
    provider_name = "mock"

    async def health(self) -> bool:
        return True

    async def list_models(self) -> list[ModelInfo]:
        return []

    async def chat(self, request: dict) -> dict:
        return {"response": "ok"}

    async def stream_chat(self, request: dict) -> AsyncGenerator[dict, None]:
        yield {"chunk": "data"}

    async def embeddings(self, request: dict) -> dict:
        return {"embedding": []}

    async def image_generation(self, request: dict) -> dict:
        return {}

    async def audio_transcription(self, request: dict) -> dict:
        return {}

    async def audio_generation(self, request: dict) -> dict:
        return {}

    def supports(self, capability: Capability) -> bool:
        return True

    def get_capabilities(self) -> frozenset[Capability]:
        return frozenset()

    @property
    def provider_metadata(self) -> dict:
        return {}


@pytest.mark.asyncio
async def test_retry_strategy_success():
    strategy = RetryStrategy(max_attempts=3)

    async def mock_func():
        return "success"

    result = await strategy.execute(mock_func, timeout=10)
    assert result == "success"


@pytest.mark.asyncio
async def test_retry_strategy_retry():
    strategy = RetryStrategy(max_attempts=3, base_delay=0.01)

    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("connection failed")
        return "success"

    result = await strategy.execute(mock_func, timeout=10)
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_strategy_exhausted():
    strategy = RetryStrategy(max_attempts=2, base_delay=0.01)

    async def mock_func():
        raise ConnectionError("connection failed")

    with pytest.raises(RetryExhausted):
        await strategy.execute(mock_func, timeout=10)


@pytest.mark.asyncio
async def test_retry_strategy_non_retryable():
    strategy = RetryStrategy(max_attempts=3)

    async def mock_func():
        raise ValueError("invalid input")

    with pytest.raises(ValueError):
        await strategy.execute(mock_func, timeout=10)


@pytest.mark.asyncio
async def test_circuit_breaker_closed():
    cb = CircuitBreaker(threshold=3, recovery_timeout=10, success_threshold=2)
    assert cb.can_execute()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    cb = CircuitBreaker(threshold=2, recovery_timeout=10, success_threshold=1)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert not cb.can_execute()


@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    cb = CircuitBreaker(threshold=2, recovery_timeout=0.1, success_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Wait for recovery timeout
    await asyncio.sleep(0.2)

    # can_execute() must be called to transition from OPEN to HALF_OPEN
    assert cb.can_execute()  # This transitions to HALF_OPEN

    cb.record_success()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_resilience_proxy_chat():
    provider = MockProvider()
    proxy = ResilienceProxy(provider, {"failure_threshold": 3, "recovery_timeout_seconds": 10})

    result = await proxy.chat({"prompt": "test"})
    assert result == {"response": "ok"}


@pytest.mark.asyncio
async def test_resilience_proxy_health():
    provider = MockProvider()
    proxy = ResilienceProxy(provider, {"failure_threshold": 3, "recovery_timeout_seconds": 10})

    result = await proxy.health()
    assert result is True


@pytest.mark.asyncio
async def test_resilience_proxy_list_models():
    provider = MockProvider()
    proxy = ResilienceProxy(provider, {"failure_threshold": 3, "recovery_timeout_seconds": 10})

    result = await proxy.list_models()
    assert result == []
