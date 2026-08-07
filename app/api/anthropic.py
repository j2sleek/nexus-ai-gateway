from fastapi import APIRouter, HTTPException, Request

from app.core.exceptions import RoutingError
from app.models.anthropic import AnthropicRequest, AnthropicResponse

router = APIRouter(prefix="/v1")


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
        raise HTTPException(status_code=500, detail="Internal server error") from e
