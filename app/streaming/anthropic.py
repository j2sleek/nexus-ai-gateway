import json
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from .base import BaseStreamNormalizer


class AnthropicStreamNormalizer(BaseStreamNormalizer):
    # type: ignore
    async def normalize_stream(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        message_start_data = {
            "type": "message_start",
            "message": {
                "id": "msg_01",
                "type": "message",
                "role": "assistant",
                "content": [],
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        }
        yield f"event: message_start\ndata: {json.dumps(message_start_data)}\n\n"

        async for chunk in provider_stream:
            # Extract content from Anthropic completion field
            content = chunk.get("completion", "")
            event_data = {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": content},
            }
            yield f"event: content_block_delta\ndata: {json.dumps(event_data)}\n\n"

        yield 'event: message_stop\ndata: {"type": "message_stop"}\n\n'
