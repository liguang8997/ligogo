from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token

PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/captcha",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/refresh",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            return await call_next(request)

        if path.startswith("/uploads/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return await self._unauthorized(f"未提供认证令牌 (path={path}, auth={'Yes' if auth_header else 'No'}, len={len(auth_header)})")

        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            request.state.user_id = payload.get("sub")
            request.state.role = payload.get("role")
        except Exception:
            return await self._unauthorized("令牌无效或已过期")

        return await call_next(request)

    async def _unauthorized(self, message: str):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={"code": 401, "data": None, "message": message, "error": ""},
        )
