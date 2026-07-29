from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings

from app.core.logging import configure_logging

import logging

from app.api.router import api_router

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    logger.info("Starting %s", settings.app_name)

    # TODO:
    # Initialise logging
    # Load registry
    # Discover providers
    # Start scheduler

    yield

    logger.info("Stopping %s", settings.app_name)

    # TODO:
    # Stop scheduler
    # Flush logs
    # Save registry


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Intelligent AI Gateway with dynamic provider discovery and capability-based routing.",
    lifespan=lifespan,
)

app.include_router(api_router)
