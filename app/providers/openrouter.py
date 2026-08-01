from app.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):
    provider_name = "openrouter"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
