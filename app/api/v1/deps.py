from fastapi import Request
from app.core.exceptions import AuthenticationException


def get_current_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise AuthenticationException("未登录")
    return user_id


def get_current_role(request: Request) -> str:
    role = getattr(request.state, "role", None)
    if not role:
        raise AuthenticationException("未登录")
    return role
