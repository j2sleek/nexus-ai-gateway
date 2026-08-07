from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.requests import GatewayRequest
from app.models.responses import GatewayResponse


class BaseClient(ABC):
    """
    Base transport client.

    A client is responsible only for communicating with a provider.
    Routing decisions are made elsewhere.
    """

    provider_name: str

    @abstractmethod
    async def execute(
        self,
        request: GatewayRequest,
    ) -> GatewayResponse:
        """
        Execute a normalized gateway request against the provider.
        """
        raise NotImplementedError
