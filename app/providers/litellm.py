from app.providers.base import BaseProvider


class LiteLLMProvider(BaseProvider):
    provider_name = "litellm"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
