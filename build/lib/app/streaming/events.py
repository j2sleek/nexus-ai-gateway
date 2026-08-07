from typing import Any

from pydantic import BaseModel


class StreamingEvent(BaseModel):
    """Base class for normalized streaming events."""

    event: str
    data: Any


# OpenAI Specific
class OpenAIStreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any] | None = None
