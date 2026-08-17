from __future__ import annotations

import logging
from typing import Any

from app.models.capability import Capability

logger = logging.getLogger(__name__)


def normalize_capabilities(raw_capabilities: Any) -> frozenset[Capability]:
    """
    Normalize provider-native capability representations into canonical Capability enums.

    - Handles Capability enums, strings, lists, sets, tuples, or frozensets.
    - Case-insensitive matching against Capability enum values and common aliases.
    - Safely ignores unknown capabilities without crashing.
    - Deduplicates capabilities.
    - Handles malformed metadata gracefully.
    """
    if raw_capabilities is None:
        return frozenset()

    if isinstance(raw_capabilities, Capability):
        return frozenset([raw_capabilities])

    if isinstance(raw_capabilities, str):
        raw_items = [raw_capabilities]
    elif isinstance(raw_capabilities, (list, set, tuple, frozenset)):
        raw_items = list(raw_capabilities)
    else:
        logger.warning("Unexpected capability metadata type: %s", type(raw_capabilities))
        return frozenset()

    normalized: set[Capability] = set()
    valid_values = {c.value: c for c in Capability}
    aliases = {
        "embedding": Capability.EMBEDDINGS,
        "chat_completion": Capability.CHAT,
        "chat-completion": Capability.CHAT,
    }

    for item in raw_items:
        if isinstance(item, Capability):
            normalized.add(item)
            continue

        if not isinstance(item, str):
            logger.debug("Skipping non-string capability item: %s", item)
            continue

        cleaned = item.strip().lower()
        if cleaned in valid_values:
            normalized.add(valid_values[cleaned])
        elif cleaned in aliases:
            normalized.add(aliases[cleaned])
        else:
            logger.debug("Ignored unknown provider capability: %s", item)

    return frozenset(normalized)
