from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    teacher_id: str = Field(..., min_length=8, max_length=8)
    password: str = Field(..., min_length=6, max_length=32)
    captcha_key: str | None = None
    captcha_answer: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    teacher_id: str
    name: str
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    teacher_id: str = Field(..., min_length=8, max_length=8)


class ResetPasswordRequest(BaseModel):
    teacher_id: str = Field(..., min_length=8, max_length=8)
    answer1: str
    answer2: str
    answer3: str
    new_password: str = Field(..., min_length=6, max_length=32)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=32)


class CaptchaResponse(BaseModel):
    captcha_key: str
    captcha_image: str  # base64
