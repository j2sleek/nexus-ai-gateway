from app.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    provider_name = "gemini"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
