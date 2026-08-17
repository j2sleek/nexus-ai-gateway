from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

import litellm

from app.core.exceptions import ModelNotFound
from app.discovery.normalizer import normalize_capabilities
from app.models.capability import Capability
from app.models.model_info import ModelInfo
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


def translate_exception(e: Exception) -> Exception:
    """Translate LiteLLM exceptions into canonical gateway/standard exceptions."""
    if isinstance(e, litellm.AuthenticationError):
        return ValueError("Provider authentication failed")
    if isinstance(e, litellm.PermissionDeniedError):
        return ValueError("Permission denied by provider")
    if isinstance(e, litellm.RateLimitError):
        return RuntimeError("Provider rate limit exceeded")
    if isinstance(e, litellm.NotFoundError):
        return ModelNotFound("Requested model not found on provider")
    if isinstance(e, litellm.BadRequestError):
        return ValueError("Invalid request to provider")
    if isinstance(e, litellm.Timeout):
        return TimeoutError("Provider request timed out")
    if isinstance(e, litellm.APIConnectionError):
        return ConnectionError("Failed to connect to provider")
    if isinstance(e, litellm.APIError):
        return RuntimeError(f"Provider API error: {e.message if hasattr(e, 'message') else str(e)}")
    return e


class LiteLLMProvider(BaseProvider):
    provider_name = "litellm"

    async def health(self) -> bool:
        """Return True if LiteLLM model catalog is accessible."""
        try:
            cost_map = getattr(litellm, "model_cost", None)
            return cost_map is not None and isinstance(cost_map, dict)
        except Exception:
            logger.exception("LiteLLM health check failed")
            return False

    async def list_models(self) -> list[ModelInfo]:
        """Return the models exposed by this provider via LiteLLM model cost map."""
        models: list[ModelInfo] = []
        try:
            cost_map = getattr(litellm, "model_cost", {})
            if not isinstance(cost_map, dict):
                return []

            for model_id, info in cost_map.items():
                if not isinstance(model_id, str) or model_id == "sample_spec":
                    continue
                if not isinstance(info, dict):
                    info = {}

                raw_caps: list[Any] = []
                mode = info.get("mode")
                if mode:
                    raw_caps.append(str(mode))

                if info.get("supports_function_calling") or info.get("supports_tool_choice"):
                    raw_caps.extend(["tools", "function_calling"])
                if info.get("supports_vision"):
                    raw_caps.append("vision")
                if info.get("supports_audio_input"):
                    raw_caps.append("audio_input")
                if info.get("supports_audio_output"):
                    raw_caps.append("audio_output")
                if info.get("supports_reasoning") or info.get("supports_adaptive_thinking"):
                    raw_caps.append("reasoning")
                if info.get("supports_prompt_caching"):
                    raw_caps.append("long_context")

                normalized_caps = normalize_capabilities(raw_caps)

                raw_ctx = info.get("max_input_tokens") or info.get("max_tokens")
                context_window = int(raw_ctx) if raw_ctx is not None else None

                raw_out = info.get("max_output_tokens")
                max_output_tokens = int(raw_out) if raw_out is not None else None

                input_cost = info.get("input_cost_per_token")
                output_cost = info.get("output_cost_per_token")

                input_cost_per_million = (
                    float(input_cost) * 1_000_000 if input_cost is not None else None
                )
                output_cost_per_million = (
                    float(output_cost) * 1_000_000 if output_cost is not None else None
                )

                model_info = ModelInfo(
                    id=model_id,
                    provider=self.provider_name,
                    display_name=model_id,
                    context_window=context_window,
                    max_output_tokens=max_output_tokens,
                    input_cost_per_million=input_cost_per_million,
                    output_cost_per_million=output_cost_per_million,
                    capabilities=normalized_caps,
                )
                models.append(model_info)
        except Exception:
            logger.exception("Failed to list models from LiteLLM provider")
            raise

        return models

    async def chat(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a chat completion request using LiteLLM."""
        try:
            kwargs: dict[str, Any] = {
                "model": request.get("model"),
                "messages": request.get("messages", []),
            }

            for key in (
                "temperature",
                "top_p",
                "max_tokens",
                "max_completion_tokens",
                "stop",
                "tools",
                "tool_choice",
                "functions",
                "function_call",
                "response_format",
            ):
                if key in request and request[key] is not None:
                    kwargs[key] = request[key]

            response = await litellm.acompletion(**kwargs)

            if hasattr(response, "model_dump"):
                return response.model_dump()
            elif hasattr(response, "dict"):
                return response.dict()
            return dict(response)
        except Exception as e:
            logger.exception("LiteLLM chat completion failed")
            raise translate_exception(e) from e

    async def stream_chat(self, request: dict[str, Any]) -> AsyncGenerator[Any, None]:  # type: ignore[override]
        """Execute a streaming chat completion request using LiteLLM."""
        try:
            kwargs: dict[str, Any] = {
                "model": request.get("model"),
                "messages": request.get("messages", []),
                "stream": True,
            }

            for key in (
                "temperature",
                "top_p",
                "max_tokens",
                "max_completion_tokens",
                "stop",
                "tools",
                "tool_choice",
                "functions",
                "function_call",
                "response_format",
            ):
                if key in request and request[key] is not None:
                    kwargs[key] = request[key]

            response_stream = await litellm.acompletion(**kwargs)

            async for chunk in response_stream:
                if hasattr(chunk, "model_dump"):
                    yield chunk.model_dump()
                elif hasattr(chunk, "dict"):
                    yield chunk.dict()
                else:
                    yield dict(chunk)
        except Exception as e:
            logger.exception("LiteLLM streaming failed")
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
        return frozenset(
            [
                Capability.CHAT,
                Capability.EMBEDDINGS,
                Capability.TOOLS,
                Capability.VISION,
            ]
        )

    @property
    def provider_metadata(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "library": "litellm"}
