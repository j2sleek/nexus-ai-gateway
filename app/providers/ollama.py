from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from app.core.exceptions import ModelNotFound
from app.discovery.normalizer import normalize_capabilities
from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


def translate_exception(e: Exception) -> Exception:
    """Translate Ollama/httpx exceptions into canonical gateway exceptions."""
    if isinstance(e, httpx.ConnectError):
        return ConnectionError("Ollama daemon unavailable or unreachable")
    if isinstance(e, httpx.ConnectTimeout):
        return TimeoutError("Ollama connection timed out")
    if isinstance(e, httpx.TimeoutException):
        return TimeoutError("Ollama request timed out")
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return ModelNotFound("Requested model not found on Ollama")
        if status == 400:
            return ValueError("Invalid request to Ollama")
        return RuntimeError(f"Ollama server error (status {status})")
    return e


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        super().__init__()
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    async def health(self) -> bool:
        """Return True if Ollama daemon is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            logger.exception("Ollama health check failed")
            return False

    async def list_models(self) -> list[ModelInfo]:
        """Return models discovered from Ollama instance."""
        models: list[ModelInfo] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                raw_models = data.get("models", [])

                for item in raw_models:
                    model_id = item.get("name") or item.get("model")
                    if not model_id:
                        continue

                    details = item.get("details", {})
                    family = (details.get("family") or "").lower()
                    families = [f.lower() for f in details.get("families", [])]
                    name_lower = model_id.lower()

                    raw_caps: list[str] = []
                    if "embed" in name_lower or "embedding" in family or "embedding" in families:
                        raw_caps.append("embeddings")
                    elif (
                        family
                        or families
                        or "chat" in name_lower
                        or "instruct" in name_lower
                        or "llama" in families
                        or "mistral" in families
                        or "gemma" in families
                    ):
                        raw_caps.append("chat")

                    if "vision" in name_lower or "llava" in name_lower or "vision" in family:
                        raw_caps.append("vision")

                    normalized_caps = normalize_capabilities(raw_caps)

                    model_info = ModelInfo(
                        id=model_id,
                        provider=self.provider_name,
                        display_name=model_id,
                        capabilities=normalized_caps,
                    )
                    models.append(model_info)
        except Exception as e:
            logger.exception("Failed to list models from Ollama provider")
            raise translate_exception(e) from e

        return models

    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute non-streaming chat completion via Ollama."""
        try:
            model = request.get("model")
            messages = request.get("messages", [])
            options: dict[str, Any] = {}

            if "temperature" in request and request["temperature"] is not None:
                options["temperature"] = request["temperature"]
            if "top_p" in request and request["top_p"] is not None:
                options["top_p"] = request["top_p"]
            if "max_tokens" in request and request["max_tokens"] is not None:
                options["num_predict"] = request["max_tokens"]
            elif (
                "max_completion_tokens" in request and request["max_completion_tokens"] is not None
            ):
                options["num_predict"] = request["max_completion_tokens"]
            if "stop" in request and request["stop"] is not None:
                options["stop"] = request["stop"]

            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": False,
            }
            if options:
                payload["options"] = options

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                res_data = response.json()

            import time

            return {
                "id": f"chatcmpl-ollama-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": res_data.get("model", model),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": res_data.get("message", {}).get("role", "assistant"),
                            "content": res_data.get("message", {}).get("content", ""),
                        },
                        "finish_reason": res_data.get("done_reason")
                        or ("stop" if res_data.get("done") else None),
                    }
                ],
                "usage": {
                    "prompt_tokens": res_data.get("prompt_eval_count", 0),
                    "completion_tokens": res_data.get("eval_count", 0),
                    "total_tokens": res_data.get("prompt_eval_count", 0)
                    + res_data.get("eval_count", 0),
                },
            }
        except Exception as e:
            logger.exception("Ollama chat completion failed")
            raise translate_exception(e) from e

    async def stream_chat(  # type: ignore[override]
        self, request: dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        """Execute streaming chat completion via Ollama."""
        import json
        import time

        try:
            model = request.get("model")
            messages = request.get("messages", [])
            options: dict[str, Any] = {}

            if "temperature" in request and request["temperature"] is not None:
                options["temperature"] = request["temperature"]
            if "top_p" in request and request["top_p"] is not None:
                options["top_p"] = request["top_p"]
            if "max_tokens" in request and request["max_tokens"] is not None:
                options["num_predict"] = request["max_tokens"]
            elif (
                "max_completion_tokens" in request and request["max_completion_tokens"] is not None
            ):
                options["num_predict"] = request["max_completion_tokens"]
            if "stop" in request and request["stop"] is not None:
                options["stop"] = request["stop"]

            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            if options:
                payload["options"] = options

            async with (
                httpx.AsyncClient(timeout=60.0) as client,
                client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response,
            ):
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        res_data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    chunk_id = f"chatcmpl-ollama-{int(time.time())}"
                    yield {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": res_data.get("model", model),
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": res_data.get("message", {}).get("role"),
                                    "content": res_data.get("message", {}).get("content", ""),
                                },
                                "finish_reason": res_data.get("done_reason")
                                or ("stop" if res_data.get("done") else None),
                            }
                        ],
                    }
        except Exception as e:
            logger.exception("Ollama streaming failed")
            raise translate_exception(e) from e

    async def embeddings(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def image_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_transcription(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def audio_generation(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def supports(self, capability: Capability) -> bool:
        return capability == Capability.CHAT or capability == Capability.EMBEDDINGS

    def get_capabilities(self) -> frozenset[Capability]:
        return frozenset([Capability.CHAT, Capability.EMBEDDINGS])

    @property
    def provider_metadata(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "library": "httpx-ollama"}
