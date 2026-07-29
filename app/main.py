from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    print(f"Starting {settings.app_name}")

    # TODO:
    # Initialise logging
    # Load registry
    # Discover providers
    # Start scheduler

    yield

    print(f"Stopping {settings.app_name}")

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

# Routers will be registered here in later steps.
