import uuid

from starlette.types import ASGIApp, Receive, Scope, Send


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        scope["request_id"] = request_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                resp_headers = dict(message.get("headers", []))
                resp_headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(resp_headers.items())
            await send(message)

        await self.app(scope, receive, send_wrapper)
