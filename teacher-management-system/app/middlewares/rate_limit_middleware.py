import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._clients: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        if client_ip not in self._clients:
            self._clients[client_ip] = []
        self._clients[client_ip] = [t for t in self._clients[client_ip] if t > window_start]

        if len(self._clients[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=200,
                content={"code": 429, "data": None, "message": "请求过于频繁", "error": ""},
            )

        self._clients[client_ip].append(now)
        return await call_next(request)
