from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.model_info import ModelInfo


class BaseProvider(ABC):
    """
    Base interface implemented by every AI provider.
    """

    provider_name: str

    def __init__(self) -> None:
        self.name = self.provider_name

    @abstractmethod
    async def health(self) -> bool:
        """
        Return True if the provider is reachable.
        """
        raise NotImplementedError

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """
        Return the models exposed by this provider.
        """
        raise NotImplementedError

    @abstractmethod
    async def chat(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute a chat completion request.
        """
        raise NotImplementedError
