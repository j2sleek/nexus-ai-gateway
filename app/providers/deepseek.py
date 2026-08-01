from app.providers.base import BaseProvider


class DeepSeekProvider(BaseProvider):
    provider_name = "deepseek"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
