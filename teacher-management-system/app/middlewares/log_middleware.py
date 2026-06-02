import json
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models.log import OperationLog


class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        user_id = getattr(request.state, "user_id", None)
        if user_id and request.url.path.startswith("/api/v1") and request.method != "GET":
            try:
                async with async_session() as session:
                    log_entry = OperationLog(
                        operator_id=user_id,
                        action=f"{request.method} {request.url.path}",
                        target_type=request.url.path.split("/")[3] if len(request.url.path.split("/")) > 3 else None,
                        ip_address=request.client.host if request.client else None,
                        result="SUCCESS" if response.status_code < 400 else "FAILURE",
                        detail=json.dumps({"method": request.method, "path": request.url.path, "duration_ms": round(duration * 1000)}),
                    )
                    session.add(log_entry)
                    await session.commit()
            except Exception:
                pass

        return response
