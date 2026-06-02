from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import BaseException
from loguru import logger


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseException)
    async def base_exception_handler(request: Request, exc: BaseException):
        return JSONResponse(
            status_code=200,
            content={
                "code": exc.code,
                "data": None,
                "message": exc.message,
                "error": str(exc),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未捕获异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "code": 500,
                "data": None,
                "message": "服务器内部错误",
                "error": "系统繁忙，请稍后再试",
            },
        )
