from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.exceptions import RoutingError
from app.models.anthropic import AnthropicRequest, AnthropicResponse
from app.streaming.anthropic import AnthropicStreamNormalizer

router = APIRouter(prefix="/v1/anthropic")


@router.post("/messages", response_model=AnthropicResponse)
async def messages(request: Request, body: AnthropicRequest):
    resolver = request.app.state.route_resolver

    try:
        routing_result = await resolver.resolve(requested_model=body.model)
        provider = request.app.state.provider_registry.get(routing_result.provider)

        # Call provider (assuming OpenAI-compatible request format, needing translation)
        # Anthropic -> OpenAI translation needed
        openai_payload = {
            "model": body.model,
            "messages": [{"role": m.role, "content": m.content} for m in body.messages],
        }

        if body.stream:
            # Streaming path
            normalizer = AnthropicStreamNormalizer(provider.provider_name, body.model)
            stream = await provider.stream_chat(openai_payload)
            return StreamingResponse(
                normalizer.normalize_stream(stream, openai_payload), media_type="text/event-stream"
            )

        # Synchronous path
        raw_response = await provider.chat(openai_payload)

        # Normalize response
        return AnthropicResponse(
            id=raw_response["id"],
            model=raw_response["model"],
            content=[{"type": "text", "text": raw_response["choices"][0]["message"]["content"]}],
            usage=raw_response.get("usage", {"input_tokens": 0, "output_tokens": 0}),
        )
    except RoutingError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}") from e
