from enum import StrEnum
from typing import frozenset

from pydantic import BaseModel, Field


class Permission(StrEnum):
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    SPEECH = "speech"
    ADMIN = "admin"


class APIKey(BaseModel):
    id: str
    key: str
    description: str = ""
    enabled: bool = True
    permissions: frozenset[Permission] = frozenset()


class AuthConfig(BaseModel):
    keys: list[APIKey] = Field(default_factory=list)
    public_endpoints: list[str] = Field(default_factory=lambda: ["/health"])
    metrics_public: bool = False
