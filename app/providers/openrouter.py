from app.providers.base import BaseProvider


class OpenRouterProvider(BaseProvider):

    def __init__(self):
        super().__init__("openrouter")

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
