from app.providers.base import BaseProvider


class OllamaProvider(BaseProvider):

    def __init__(self):
        super().__init__("ollama")

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
