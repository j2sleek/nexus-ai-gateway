from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

import pytest

from app.streaming.base import BaseStreamNormalizer


class MockNormalizer(BaseStreamNormalizer):
    def normalize_stream(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        return self._do_normalize(provider_stream)

    async def _do_normalize(self, provider_stream: AsyncIterator[Any]):
        async for event in provider_stream:
            yield f"data: {event}"


@pytest.mark.asyncio
async def test_normalize_stream_with_lifecycle():
    normalizer = MockNormalizer("test", "test-model")

    async def mock_stream():
        yield "chunk1"
        yield "chunk2"

    events = []
    async for event in normalizer.normalize_stream_with_lifecycle(mock_stream(), {}):
        events.append(event)

    assert events == ["data: chunk1", "data: chunk2"]


@pytest.mark.asyncio
async def test_normalize_stream_with_lifecycle_exception():
    normalizer = MockNormalizer("test", "test-model")

    async def mock_stream():
        yield "chunk1"
        raise Exception("stream error")

    events = []
    # This should yield an error event
    async for event in normalizer.normalize_stream_with_lifecycle(mock_stream(), {}):
        events.append(event)

    assert events[0] == "data: chunk1"
    assert "error" in events[1]
    assert "stream error" in events[1]
