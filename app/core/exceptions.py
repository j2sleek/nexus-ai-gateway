class GatewayError(Exception):
    """Base class for all gateway exceptions."""


class RoutingError(GatewayError):
    """Base class for routing-related errors."""


class ModelNotFound(RoutingError):
    """Raised when a requested model is not found."""


class CapabilityNotSupported(RoutingError):
    """Raised when no model supports the requested capability."""


class NoHealthyProvider(RoutingError):
    """Raised when no providers are healthy."""


class RoutingFailure(RoutingError):
    """Raised when routing fails."""
