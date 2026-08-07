from fastapi import APIRouter, HTTPException, Request

from app.core.exceptions import RoutingError
from app.models.openai import ChatCompletionRequest

router = APIRouter(prefix="/v1")


@router.get("/models")
async def list_models(request: Request):
    registry = request.app.state.model_registry
    models = await registry.list_models()
    return {
        "object": "list",
        "data": [{"id": m.id, "object": "model", "owned_by": m.provider} for m in models],
    }


@router.post("/chat/completions")
async def chat_completions(request: Request, body: ChatCompletionRequest):
    resolver = request.app.state.route_resolver

    try:
        routing_result = await resolver.resolve(requested_model=body.model)
        provider = request.app.state.provider_registry.get(routing_result.provider)

        # Call provider (assuming OpenAI-compatible request format)
        response = await provider.chat(body.model_dump())

        return response
    except RoutingError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e
