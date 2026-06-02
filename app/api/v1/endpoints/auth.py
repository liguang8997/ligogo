from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest, CaptchaResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    data = await svc.login(req.teacher_id, req.password)
    return ResponseModel(data=LoginResponse(**data), message="登录成功")


@router.post("/refresh", response_model=ResponseModel[RefreshResponse])
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    data = await svc.refresh_token(req.refresh_token)
    return ResponseModel(data=RefreshResponse(**data), message="令牌刷新成功")


@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    await svc.logout(request.state.user_id)
    return ResponseModel(message="登出成功")


@router.get("/captcha", response_model=ResponseModel[CaptchaResponse])
async def captcha():
    return ResponseModel(message="验证码功能待实现")


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest):
    questions = ["你父亲的名字是？", "你母亲的名字是？", "你的出生地是？"]
    return ResponseModel(message="请在下一步提供密保答案", data={"questions": questions})


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    await svc.reset_password(req.teacher_id, req.answer1, req.answer2, req.answer3, req.new_password)
    return ResponseModel(message="密码重置成功")


@router.put("/password")
async def change_password(req: ChangePasswordRequest, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    await svc.change_password(request.state.user_id, req.old_password, req.new_password)
    return ResponseModel(message="密码修改成功")
