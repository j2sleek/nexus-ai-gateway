import pytest

from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.manager import DiscoveryManager
from app.routing.engine import RouteResolver


@pytest.fixture
def provider_registry():
    return ProviderRegistry()


@pytest.fixture
def model_registry():
    return ModelRegistry()


@pytest.fixture
def discovery_manager(provider_registry, model_registry):
    return DiscoveryManager(provider_registry, model_registry)


@pytest.fixture
def route_resolver(provider_registry, model_registry):
    return RouteResolver(provider_registry, model_registry)
