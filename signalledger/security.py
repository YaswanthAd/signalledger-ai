"""Small local-demo boundary: body budget, optional bearer token, safe defaults."""
import hmac
import os
from starlette.responses import JSONResponse


class Boundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        token = os.environ.get("APP_TOKEN", "")
        if token and scope["path"].startswith("/api/") and scope["path"] != "/api/health":
            if not hmac.compare_digest(headers.get(b"authorization", b""), ("Bearer " + token).encode()):
                return await JSONResponse({"detail": "Bearer token required"}, status_code=401)(scope, receive, send)
        # Read at most 2 MiB, including chunked requests, before model validation.
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > 2_097_152:
                return await JSONResponse({"detail": "Request exceeds 2 MiB"}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        consumed = False
        async def replay():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()
        async def secured(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).extend([
                    (b"x-content-type-options", b"nosniff"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'"),
                    (b"referrer-policy", b"no-referrer")])
            await send(message)
        await self.app(scope, replay, secured)
