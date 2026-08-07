import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.openai import router as openai_router
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.model_registry import ModelRegistry
from app.core.registry import ProviderRegistry
from app.discovery.manager import DiscoveryManager
from app.providers import get_providers
from app.routing.engine import RouteResolver

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    logger.info("Starting %s", settings.app_name)

    # Initialize components
    provider_registry = ProviderRegistry()
    model_registry = ModelRegistry()

    # Register providers
    for provider_cls in get_providers():
        await provider_registry.register(provider_cls())

    discovery_manager = DiscoveryManager(
        provider_registry=provider_registry,
        model_registry=model_registry,
        config_path=settings.providers_config,
    )

    # Discover providers
    try:
        summary = await discovery_manager.discover()
        logger.info("Discovery complete: %s", summary)
    except Exception as e:
        logger.exception("Failed to initialize providers: %s", e)
        raise

    # Store in app state for dependency injection
    app.state.provider_registry = provider_registry
    app.state.model_registry = model_registry
    app.state.route_resolver = RouteResolver(provider_registry, model_registry)

    yield

    logger.info("Stopping %s", settings.app_name)

    # Shutdown
    provider_registry.clear()
    model_registry.clear()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Intelligent AI Gateway with dynamic provider discovery and capability-based routing."
    ),
    lifespan=lifespan,
)

app.include_router(api_router)
app.include_router(openai_router)
