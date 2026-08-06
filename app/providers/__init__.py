"""
Provider registry.
"""

from app.providers.base import BaseProvider
from app.providers.dashscope import DashScopeProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.gemini import GeminiProvider
from app.providers.litellm import LiteLLMProvider
from app.providers.mistral import MistralProvider
from app.providers.ollama import OllamaProvider
from app.providers.openrouter import OpenRouterProvider

__all__ = [
    "BaseProvider",
    "DashScopeProvider",
    "DeepSeekProvider",
    "GeminiProvider",
    "LiteLLMProvider",
    "MistralProvider",
    "OllamaProvider",
    "OpenRouterProvider",
]
