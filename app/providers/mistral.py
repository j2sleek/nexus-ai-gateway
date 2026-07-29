from app.providers.base import BaseProvider


class MistralProvider(BaseProvider):

    def __init__(self):
        super().__init__("mistral")

    async def health(self):
        raise NotImplementedError

    async def list_models(self):
        raise NotImplementedError

    async def chat(self, request):
        raise NotImplementedError
