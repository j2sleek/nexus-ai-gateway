import asyncio

import litellm
import pytest

from app.core.exceptions import ModelNotFound
from app.providers.litellm import LiteLLMProvider


class FakeAsyncStream:
    def __init__(self, chunks, fail_on_chunk=None):
        self.chunks = chunks
        self.fail_on_chunk = fail_on_chunk
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.fail_on_chunk is not None and self.index == self.fail_on_chunk:
            raise litellm.RateLimitError(
                message="Rate limit hit mid-stream",
                model="gpt-4o",
                llm_provider="openai",
            )
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk


@pytest.mark.asyncio
async def test_chat_successful_completion(mocker):
    # Test 1, 2, 3, 4, 5: Successful chat, model/messages/kwargs forwarding, response dict return
    mock_resp = litellm.ModelResponse(
        id="chatcmpl-999",
        model="gpt-4o",
        choices=[
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {"role": "assistant", "content": "Hello from LiteLLM!"},
            }
        ],
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    mock_acompletion = mocker.patch("litellm.acompletion", return_value=mock_resp)

    provider = LiteLLMProvider()
    request = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "stop": ["END"],
    }

    result = await provider.chat(request)

    assert result["id"] == "chatcmpl-999"
    assert result["model"] == "gpt-4o"
    assert result["choices"][0]["message"]["content"] == "Hello from LiteLLM!"

    mock_acompletion.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hi"}],
        temperature=0.7,
        max_tokens=100,
        top_p=0.9,
        stop=["END"],
    )


@pytest.mark.asyncio
async def test_chat_error_translations(mocker):
    # Test 6, 7, 8: Authentication, Rate Limit, Timeout error translation
    provider = LiteLLMProvider()

    # AuthenticationError
    mocker.patch(
        "litellm.acompletion",
        side_effect=litellm.AuthenticationError(
            message="Invalid API Key", model="gpt-4o", llm_provider="openai"
        ),
    )
    with pytest.raises(ValueError, match="Provider authentication failed"):
        await provider.chat({"model": "gpt-4o", "messages": []})

    # RateLimitError
    mocker.patch(
        "litellm.acompletion",
        side_effect=litellm.RateLimitError(
            message="Rate limit exceeded", model="gpt-4o", llm_provider="openai"
        ),
    )
    with pytest.raises(RuntimeError, match="Provider rate limit exceeded"):
        await provider.chat({"model": "gpt-4o", "messages": []})

    # Timeout
    mocker.patch(
        "litellm.acompletion",
        side_effect=litellm.Timeout(
            message="Request timed out", model="gpt-4o", llm_provider="openai"
        ),
    )
    with pytest.raises(asyncio.TimeoutError, match="Provider request timed out"):
        await provider.chat({"model": "gpt-4o", "messages": []})

    # NotFoundError
    mocker.patch(
        "litellm.acompletion",
        side_effect=litellm.NotFoundError(
            message="Model not found", model="unknown-m", llm_provider="openai"
        ),
    )
    with pytest.raises(ModelNotFound, match="Requested model not found on provider"):
        await provider.chat({"model": "unknown-m", "messages": []})


@pytest.mark.asyncio
async def test_stream_chat_successful(mocker):
    # Test 9, 10, 11, 12, 15: Successful streaming, incremental chunks,
    # finish_reason preserved, no accidental await
    chunks = [
        litellm.ModelResponse(
            id="chatcmpl-chunk-1",
            model="gpt-4o",
            choices=[{"index": 0, "delta": {"content": "Hello"}, "finish_reason": None}],
        ),
        litellm.ModelResponse(
            id="chatcmpl-chunk-2",
            model="gpt-4o",
            choices=[
                {
                    "index": 0,
                    "delta": {"content": " world!"},
                    "finish_reason": "stop",
                }
            ],
        ),
    ]
    fake_stream = FakeAsyncStream(chunks)
    mocker.patch("litellm.acompletion", return_value=fake_stream)

    provider = LiteLLMProvider()
    request = {"model": "gpt-4o", "messages": [{"role": "user", "content": "Hi"}]}

    stream = provider.stream_chat(request)
    assert not asyncio.iscoroutine(stream)

    yielded_chunks = []
    async for chunk in stream:
        yielded_chunks.append(chunk)

    assert len(yielded_chunks) == 2
    assert yielded_chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert yielded_chunks[1]["choices"][0]["delta"]["content"] == " world!"
    assert yielded_chunks[1]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_stream_chat_initial_failure_and_midstream_exception(mocker):
    # Test 13 & 14: Initial streaming invocation failure & mid-stream exception
    provider = LiteLLMProvider()

    # Initial invocation failure
    mocker.patch(
        "litellm.acompletion",
        side_effect=litellm.AuthenticationError(
            message="Bad key", model="gpt-4o", llm_provider="openai"
        ),
    )
    stream_fail_initial = provider.stream_chat({"model": "gpt-4o", "messages": []})
    with pytest.raises(ValueError, match="Provider authentication failed"):
        async for _ in stream_fail_initial:
            pass

    # Exception mid-stream
    chunks = [
        litellm.ModelResponse(
            id="chatcmpl-c1",
            choices=[{"index": 0, "delta": {"content": "First"}, "finish_reason": None}],
        )
    ]
    fake_failing_stream = FakeAsyncStream(chunks, fail_on_chunk=1)
    mocker.patch("litellm.acompletion", return_value=fake_failing_stream)

    stream_mid_fail = provider.stream_chat({"model": "gpt-4o", "messages": []})
    received = []
    with pytest.raises(RuntimeError, match="Provider rate limit exceeded"):
        async for chunk in stream_mid_fail:
            received.append(chunk)

    assert len(received) == 1
    assert received[0]["choices"][0]["delta"]["content"] == "First"
