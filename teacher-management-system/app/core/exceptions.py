class BaseException(Exception):
    code: int = 500
    message: str = "服务器内部错误"

    def __init__(self, message: str = None, code: int = None):
        if message:
            self.message = message
        if code:
            self.code = code


class BusinessException(BaseException):
    code = 400
    message = "业务异常"


class AuthenticationException(BaseException):
    code = 401
    message = "认证失败"


class AuthorizationException(BaseException):
    code = 403
    message = "权限不足"


class NotFoundException(BaseException):
    code = 404
    message = "资源不存在"


class ConflictException(BaseException):
    code = 409
    message = "资源冲突"


class RateLimitException(BaseException):
    code = 429
    message = "请求过于频繁"


class FileUploadException(BaseException):
    code = 400
    message = "文件上传失败"
