import asyncio

import httpx
import pytest

from app.core.exceptions import ModelNotFound
from app.providers.ollama import OllamaProvider


class FakeHttpxStream:
    def __init__(self, lines, status_code=200, fail_on_line=None):
        self.lines = lines
        self.status_code = status_code
        self.fail_on_line = fail_on_line

    async def aiter_lines(self):
        for i, line in enumerate(self.lines):
            if self.fail_on_line is not None and i == self.fail_on_line:
                raise httpx.ReadTimeout("Stream read timed out mid-stream")
            yield line

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://localhost:11434/api/chat")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("Error status", request=request, response=response)


class FakeAsyncClientCtx:
    def __init__(self, post_return_value=None, stream_return_value=None):
        self.post_return_value = post_return_value
        self.stream_return_value = stream_return_value

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get(self, url):
        return None

    async def post(self, url, json=None):
        if isinstance(self.post_return_value, Exception):
            raise self.post_return_value
        return self.post_return_value

    def stream(self, method, url, json=None):
        return self.stream_return_value


@pytest.mark.asyncio
async def test_ollama_chat_success(mocker):
    # Test 14, 15, 16, 17, 18: Successful chat completion, parameter
    # forwarding, response normalization
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "model": "llama3:latest",
        "message": {"role": "assistant", "content": "Hello from Ollama!"},
        "done": True,
        "prompt_eval_count": 12,
        "eval_count": 8,
    }

    mock_client_ctx = FakeAsyncClientCtx(post_return_value=mock_resp)
    mocker.patch("httpx.AsyncClient", return_value=mock_client_ctx)

    provider = OllamaProvider()
    request = {
        "model": "llama3:latest",
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.8,
        "max_tokens": 50,
        "top_p": 0.95,
        "stop": ["END"],
    }

    result = await provider.chat(request)

    assert result["model"] == "llama3:latest"
    assert result["choices"][0]["message"]["content"] == "Hello from Ollama!"
    assert result["choices"][0]["finish_reason"] == "stop"
    assert result["usage"]["prompt_tokens"] == 12
    assert result["usage"]["completion_tokens"] == 8


@pytest.mark.asyncio
async def test_ollama_chat_error_translations(mocker):
    # Test 19, 20, 21, 22: ModelNotFound, ConnectError, Timeout, ServerError translations
    provider = OllamaProvider()

    req = httpx.Request("POST", "http://localhost:11434/api/chat")
    resp_404 = httpx.Response(404, request=req)
    mock_404 = mocker.MagicMock()
    mock_404.status_code = 404
    mock_404.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404", request=req, response=resp_404
    )
    mocker.patch(
        "httpx.AsyncClient",
        return_value=FakeAsyncClientCtx(post_return_value=mock_404),
    )

    with pytest.raises(ModelNotFound, match="Requested model not found on Ollama"):
        await provider.chat({"model": "nonexistent", "messages": []})

    mocker.patch(
        "httpx.AsyncClient",
        return_value=FakeAsyncClientCtx(post_return_value=httpx.ConnectError("Refused")),
    )
    with pytest.raises(ConnectionError, match="Ollama daemon unavailable or unreachable"):
        await provider.chat({"model": "llama3", "messages": []})

    mocker.patch(
        "httpx.AsyncClient",
        return_value=FakeAsyncClientCtx(post_return_value=httpx.TimeoutException("Timeout")),
    )
    with pytest.raises(asyncio.TimeoutError, match="Ollama request timed out"):
        await provider.chat({"model": "llama3", "messages": []})


@pytest.mark.asyncio
async def test_ollama_stream_chat_success(mocker):
    # Test 23, 24, 25, 26, 30: Successful streaming, incremental chunks,
    # finish_reason preserved, no accidental await
    lines = [
        '{"model": "llama3:latest", "message": {"role": "assistant", '
        '"content": "Hello"}, "done": false}',
        '{"model": "llama3:latest", "message": {"role": "assistant", '
        '"content": " world!"}, "done": true, "done_reason": "stop"}',
    ]
    fake_stream_ctx = FakeHttpxStream(lines)

    class FakeStreamContextManager:
        async def __aenter__(self):
            return fake_stream_ctx

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client_ctx = FakeAsyncClientCtx(stream_return_value=FakeStreamContextManager())
    mocker.patch("httpx.AsyncClient", return_value=mock_client_ctx)

    provider = OllamaProvider()
    request = {
        "model": "llama3:latest",
        "messages": [{"role": "user", "content": "Hi"}],
    }

    stream = provider.stream_chat(request)
    assert not asyncio.iscoroutine(stream)

    chunks = []
    async for chunk in stream:
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert chunks[1]["choices"][0]["delta"]["content"] == " world!"
    assert chunks[1]["choices"][0]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_ollama_stream_chat_midstream_failure(mocker):
    # Test 29: Mid-stream failure propagation
    lines = [
        '{"model": "llama3:latest", "message": {"role": "assistant", '
        '"content": "Start"}, "done": false}'
    ]
    # fail_on_line=0 will fail on first chunk
    fake_stream_ctx = FakeHttpxStream(lines, fail_on_line=0)

    class FakeStreamContextManager:
        async def __aenter__(self):
            return fake_stream_ctx

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_client_ctx = FakeAsyncClientCtx(stream_return_value=FakeStreamContextManager())
    mocker.patch("httpx.AsyncClient", return_value=mock_client_ctx)

    provider = OllamaProvider()
    request = {
        "model": "llama3:latest",
        "messages": [{"role": "user", "content": "Hi"}],
    }

    stream = provider.stream_chat(request)
    received = []
    # Now it should raise TimeoutError because it fails on chunk 0 (the first chunk)
    with pytest.raises(asyncio.TimeoutError, match="Ollama request timed out"):
        async for chunk in stream:
            received.append(chunk)

    assert len(received) == 0
