from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Abstract base class for AI providers.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def health(self) -> bool:
        """
        Check whether the provider is reachable.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """
        Return all available models.
        """
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a chat request.
        """
        raise NotImplementedError
