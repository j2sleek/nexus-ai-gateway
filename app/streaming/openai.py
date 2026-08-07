import json
import time
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from .base import BaseStreamNormalizer


class OpenAIStreamNormalizer(BaseStreamNormalizer):
    async def normalize_stream(
        self,
        provider_stream: AsyncIterator[Any],
        request_data: dict[str, Any],
    ) -> AsyncGenerator[str, None]:

        async for chunk in provider_stream:
            # Normalize chunk to OpenAI format
            # Assuming provider chunk has 'content' or is already structured
            normalized_chunk = {
                "id": "chatcmpl-" + str(int(time.time())),
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": self.model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": chunk.get("content", "")},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(normalized_chunk)}\n\n"

        # Send [DONE]
        yield "data: [DONE]\n\n"
