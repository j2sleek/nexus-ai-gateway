import secrets

import yaml
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.core.config import settings

from .models import APIKey, Permission

# Security schemes
header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def get_api_keys() -> dict[str, APIKey]:
    auth_config_path = settings.ROOT_DIR / "config" / "auth.yaml"
    with open(auth_config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    keys = {}
    for key_data in config.get("keys", []):
        key = APIKey(
            id=key_data["id"],
            key=key_data["key"],
            description=key_data.get("description", ""),
            enabled=key_data.get("enabled", True),
            permissions=frozenset(key_data.get("permissions", [])),
        )
        keys[key.id] = key
    return keys


async def _get_bearer(
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),  # noqa: B008
) -> str | None:
    if bearer:
        return bearer.credentials
    return None


async def get_current_principal(
    request: Request,
    x_api_key: str | None = Security(header_scheme),
    bearer: str | None = Depends(_get_bearer),
) -> APIKey:
    key = x_api_key or bearer

    if not key:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API Key")

    keys = get_api_keys()

    for k in keys.values():
        if secrets.compare_digest(k.key, key):
            if not k.enabled:
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="API Key disabled")

            request.state.principal = k
            return k

    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")


async def _get_principal(principal: APIKey = Depends(get_current_principal)):  # noqa: B008
    return principal


def check_permission(permission: Permission):
    async def checker(principal: APIKey = Depends(_get_principal)):  # noqa: B008
        if Permission.ADMIN in principal.permissions or permission in principal.permissions:
            return principal
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return checker
