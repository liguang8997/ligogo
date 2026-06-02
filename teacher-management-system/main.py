from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.events import register_exception_handlers
from app.middlewares.auth_middleware import AuthMiddleware
from app.middlewares.log_middleware import LogMiddleware
from app.middlewares.rate_limit_middleware import RateLimitMiddleware
from app.utils.redis_client import get_redis, close_redis
from app.utils.milvus_client import disconnect_milvus
from app.utils.file_utils import ensure_upload_dirs

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_dirs()
    await get_redis()
    yield
    await close_redis()
    disconnect_milvus()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(AuthMiddleware)
app.add_middleware(LogMiddleware)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.APP_DEBUG)
