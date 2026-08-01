from app.providers.base import BaseProvider


class MistralProvider(BaseProvider):
    provider_name = "mistral"

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
