from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
