import logging
import secrets

from fastapi import HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from .deps import get_api_keys
from .models import APIKey

logger = logging.getLogger(__name__)


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Skip public endpoints
        if self._is_public(request):
            return await call_next(request)

        # Check if metrics endpoint is public
        if request.url.path == "/metrics" and self._is_metrics_public():
            return await call_next(request)

        # Validate API key
        try:
            principal = await self._validate_api_key(request)
            request.state.principal = principal
            logger.info(f"Authentication successful for key: {principal.id}")
        except HTTPException as e:
            logger.warning(f"Authentication failed: {e.detail}")
            return e
        except Exception as e:
            logger.warning(f"Authentication error: {e!s}")
            return HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authentication error")

        # Check permissions
        if not self._check_permissions(request):
            logger.warning(f"Authorization failed for key: {request.state.principal.id}")
            return HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Insufficient permissions")

        return await call_next(request)

    def _is_public(self, request: Request) -> bool:
        from app.auth.models import AuthConfig

        config = AuthConfig()
        return request.url.path in config.public_endpoints

    def _is_metrics_public(self) -> bool:
        from app.auth.models import AuthConfig

        config = AuthConfig()
        return config.metrics_public

    async def _validate_api_key(self, request: Request) -> APIKey:
        keys = get_api_keys()

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            for k in keys.values():
                if secrets.compare_digest(k.key, api_key):
                    if not k.enabled:
                        raise HTTPException(
                            status_code=HTTP_401_UNAUTHORIZED, detail="API Key disabled"
                        )
                    return k
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

        # Check Authorization: Bearer header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
            for k in keys.values():
                if secrets.compare_digest(k.key, api_key):
                    if not k.enabled:
                        raise HTTPException(
                            status_code=HTTP_401_UNAUTHORIZED, detail="API Key disabled"
                        )
                    return k
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API Key")

    def _check_permissions(self, request: Request) -> bool:
        return True
