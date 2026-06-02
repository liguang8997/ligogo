from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.core.exceptions import AuthenticationException, BusinessException
from app.utils.crypto import encrypt_sensitive_data, decrypt_sensitive_data
from app.utils.redis_client import get_redis
from app.db.repositories.teacher_repo import TeacherInfoRepository, UserAuthRepository
from loguru import logger


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserAuthRepository(session)
        self.teacher_repo = TeacherInfoRepository(session)

    async def login(self, teacher_id: str, password: str) -> dict:
        user = await self.user_repo.get_by_teacher_id(teacher_id)
        if not user:
            raise AuthenticationException("账号或密码错误")

        if user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
            raise AuthenticationException("账号已被锁定，请稍后再试")

        if not verify_password(password, user.password_hash):
            user.failed_attempts += 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
                user.failed_attempts = 0
            raise AuthenticationException("账号或密码错误")

        user.failed_attempts = 0
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)

        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise BusinessException("教师信息不存在")

        role = self._get_role(teacher_id)
        token_data = {"sub": teacher_id, "role": role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        try:
            redis = await get_redis()
            await redis.setex(f"auth:refresh:{teacher_id}", 86400 * 7, refresh_token)
        except Exception:
            logger.warning("Redis unavailable, refresh token not cached")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "teacher_id": teacher_id,
            "name": teacher.name,
            "role": role,
        }

    async def refresh_token(self, token: str) -> dict:
        try:
            payload = decode_refresh_token(token)
        except Exception:
            raise AuthenticationException("无效的刷新令牌")

        teacher_id = payload.get("sub")
        try:
            redis = await get_redis()
            stored_token = await redis.get(f"auth:refresh:{teacher_id}")
            if stored_token and stored_token != token:
                raise AuthenticationException("令牌已失效")
            role = self._get_role(teacher_id)
            new_access = create_access_token({"sub": teacher_id, "role": role})
            new_refresh = create_refresh_token({"sub": teacher_id, "role": role})
            await redis.setex(f"auth:refresh:{teacher_id}", 86400 * 7, new_refresh)
        except AuthenticationException:
            raise
        except Exception:
            logger.warning("Redis unavailable during token refresh")
            role = self._get_role(teacher_id)
            new_access = create_access_token({"sub": teacher_id, "role": role})
            new_refresh = token
        return {"access_token": new_access, "refresh_token": new_refresh}

    async def logout(self, teacher_id: str):
        try:
            redis = await get_redis()
            await redis.delete(f"auth:refresh:{teacher_id}")
        except Exception:
            logger.warning("Redis unavailable during logout")

    async def reset_password(self, teacher_id: str, answer1: str, answer2: str, answer3: str, new_password: str) -> None:
        user = await self.user_repo.get_by_teacher_id(teacher_id)
        if not user:
            raise BusinessException("账号不存在")

        try:
            stored_a1 = decrypt_sensitive_data(user.question1_answer)
            stored_a2 = decrypt_sensitive_data(user.question2_answer)
            stored_a3 = decrypt_sensitive_data(user.question3_answer)
        except Exception:
            raise BusinessException("密保验证失败")

        if answer1 != stored_a1 or answer2 != stored_a2 or answer3 != stored_a3:
            raise BusinessException("密保答案不正确")

        user.password_hash = hash_password(new_password)
        user.failed_attempts = 0
        user.locked_until = None

    async def change_password(self, teacher_id: str, old_password: str, new_password: str) -> None:
        user = await self.user_repo.get_by_teacher_id(teacher_id)
        if not user:
            raise BusinessException("账号不存在")
        if not verify_password(old_password, user.password_hash):
            raise BusinessException("原密码不正确")
        user.password_hash = hash_password(new_password)

    def _get_role(self, teacher_id: str) -> str:
        code = teacher_id[0]
        if code == "3":
            return "admin"
        elif code == "2":
            return "leader"
        return "teacher"
