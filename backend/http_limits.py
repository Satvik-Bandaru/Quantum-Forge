"""Bound the received request body before JSON parsing, including chunked bodies."""
from starlette.responses import JSONResponse


class RequestBodyLimit:
    def __init__(self, app, limit=256_000):
        self.app = app
        self.limit = limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        lengths = [value for name, value in scope.get('headers', []) if name.lower() == b'content-length']
        if lengths:
            try:
                text = lengths[0].decode('ascii')
                if len(lengths) != 1 or not text.isdecimal():
                    raise ValueError()
                length = int(text)
            except (ValueError, UnicodeError):
                response = JSONResponse({'detail': 'Invalid Content-Length header.'}, status_code=400)
                return await response(scope, receive, send)
            if length > self.limit:
                response = JSONResponse({'detail': 'Request exceeds the 256 KB limit.'}, status_code=413)
                return await response(scope, receive, send)

        chunks = []
        size = 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > self.limit:
                response = JSONResponse({'detail': 'Request exceeds the 256 KB limit.'}, status_code=413)
                return await response(scope, receive, send)
            chunks.append(chunk)
            if not message.get('more_body', False):
                break

        body = b''.join(chunks)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()

        await self.app(scope, replay, send)
