from __future__ import annotations

from enum import StrEnum


class Capability(StrEnum):
    """
    Canonical capabilities understood by Nexus AI Gateway.

    Providers translate their native feature sets into these
    capabilities during model discovery.
    """

    CHAT = "chat"

    CODING = "coding"

    REASONING = "reasoning"

    TOOLS = "tools"

    STREAMING = "streaming"

    VISION = "vision"

    IMAGE_GENERATION = "image_generation"

    IMAGE_UNDERSTANDING = "image_understanding"

    AUDIO_INPUT = "audio_input"

    AUDIO_OUTPUT = "audio_output"

    EMBEDDINGS = "embeddings"

    RERANKING = "reranking"

    MODERATION = "moderation"

    LONG_CONTEXT = "long_context"

    FUNCTION_CALLING = "function_calling"

    JSON_MODE = "json_mode"

    THINKING = "thinking"

    MCP = "mcp"

    BATCH = "batch"
