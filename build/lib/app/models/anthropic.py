from typing import Any

from pydantic import BaseModel, Field


class AnthropicMessage(BaseModel):
    role: str
    content: Any


class AnthropicRequest(BaseModel):
    model: str
    messages: list[AnthropicMessage]
    system: str | None = None
    max_tokens: int = Field(..., gt=0)
    temperature: float | None = 1.0
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None
    stream: bool | None = False


class AnthropicResponse(BaseModel):
    id: str
    type: str = "message"
    role: str = "assistant"
    model: str
    content: list[dict[str, Any]]
    stop_reason: str | None = None
    stop_sequence: str | None = None
    usage: dict[str, int]
