from fastapi import APIRouter, Request, Response, status

from app.discovery.manager import DiscoveryManager

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request):
    discovery_manager: DiscoveryManager = request.app.state.discovery_manager
    if await discovery_manager.is_ready():
        return {"status": "ready"}
    return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
