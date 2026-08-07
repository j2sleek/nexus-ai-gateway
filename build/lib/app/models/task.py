from enum import StrEnum


class TaskType(StrEnum):
    CHAT = "chat"

    EMBEDDINGS = "embeddings"

    IMAGE_GENERATION = "image_generation"

    IMAGE_UNDERSTANDING = "image_understanding"

    AUDIO = "audio"

    MODERATION = "moderation"

    RERANKING = "reranking"

    BATCH = "batch"
