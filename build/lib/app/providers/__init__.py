"""
Provider registry.
"""

import importlib
import pkgutil

from app.providers.base import BaseProvider


def get_providers() -> list[type[BaseProvider]]:
    """
    Dynamically discover and return all provider classes.
    """
    providers = []
    for _, name, _ in pkgutil.iter_modules(__path__):
        if name == "base":
            continue

        module = importlib.import_module(f"app.providers.{name}")
        for attr in dir(module):
            cls = getattr(module, attr)
            if isinstance(cls, type) and issubclass(cls, BaseProvider) and cls is not BaseProvider:
                providers.append(cls)
    return providers


__all__ = ["BaseProvider", "get_providers"]
