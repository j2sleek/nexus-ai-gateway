"""
Provider registry.

This module exports all built-in providers and exposes the PROVIDERS
mapping used by the DiscoveryManager.
"""

from app.providers.base import BaseProvider
from app.providers.dashscope import DashScopeProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.litellm import LiteLLMProvider
from app.providers.mistral import MistralProvider
from app.providers.ollama import OllamaProvider
from app.providers.openrouter import OpenRouterProvider

PROVIDERS: dict[str, type[BaseProvider]] = {
    provider.provider_name: provider
    for provider in (
        LiteLLMProvider,
        DashScopeProvider,
        GeminiProvider,
        DeepSeekProvider,
        MistralProvider,
        OpenRouterProvider,
        OllamaProvider,
    )
}

__all__ = [
    "BaseProvider",
    "PROVIDERS",
    "LiteLLMProvider",
    "DashScopeProvider",
    "GeminiProvider",
    "DeepSeekProvider",
    "MistralProvider",
    "OpenRouterProvider",
    "OllamaProvider",
]
