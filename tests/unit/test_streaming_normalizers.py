import pytest

from app.streaming.anthropic import AnthropicStreamNormalizer
from app.streaming.openai import OpenAIStreamNormalizer


@pytest.mark.asyncio
async def test_openai_normalizer():
    normalizer = OpenAIStreamNormalizer("openai", "gpt-4")

    async def mock_stream():
        yield {"choices": [{"delta": {"content": "Hello"}}]}
        yield {"choices": [{"delta": {"content": " world"}}]}
        yield {"choices": [{"finish_reason": "stop"}]}

    events = []
    async for event in normalizer.normalize_stream(mock_stream(), {}):
        events.append(event)

    # OpenAI normalizer adds chunks and [DONE]
    assert len(events) == 4
    assert "Hello" in events[0]
    assert "world" in events[1]
    assert "[DONE]" in events[3]


@pytest.mark.asyncio
async def test_anthropic_normalizer():
    normalizer = AnthropicStreamNormalizer("anthropic", "claude-3")

    async def mock_stream():
        yield {"completion": "Hello", "stop_reason": None}
        yield {"completion": " world", "stop_reason": "end_turn"}

    events = []
    async for event in normalizer.normalize_stream(mock_stream(), {}):
        events.append(event)

    # Anthropic normalizer adds message_start, message_stop
    assert len(events) == 4
    assert "Hello" in events[1]
    assert "world" in events[2]
    assert "message_start" in events[0]
    assert "message_stop" in events[3]


@pytest.mark.asyncio
async def test_openai_normalizer_empty_stream():
    normalizer = OpenAIStreamNormalizer("openai", "gpt-4")

    async def mock_stream():
        return
        yield

    events = []
    async for event in normalizer.normalize_stream(mock_stream(), {}):
        events.append(event)

    # OpenAI still emits [DONE]
    assert len(events) == 1
    assert "[DONE]" in events[0]


@pytest.mark.asyncio
async def test_anthropic_normalizer_empty_stream():
    normalizer = AnthropicStreamNormalizer("anthropic", "claude-3")

    async def mock_stream():
        return
        yield

    events = []
    async for event in normalizer.normalize_stream(mock_stream(), {}):
        events.append(event)

    # Anthropic still emits start/stop events
    assert len(events) == 2
    assert "message_start" in events[0]
    assert "message_stop" in events[1]
