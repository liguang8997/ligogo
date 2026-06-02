from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.teacher import TeacherInfo, UserAuth
from app.db.repositories.base import BaseRepository


class TeacherInfoRepository(BaseRepository[TeacherInfo]):
    model = TeacherInfo

    async def get_by_teacher_id(self, teacher_id: str) -> TeacherInfo | None:
        return await self.get_by_id(teacher_id, id_field="teacher_id")

    async def find_by_department(self, department: str) -> list[TeacherInfo]:
        return await self.find_all(department=department)


class UserAuthRepository(BaseRepository[UserAuth]):
    model = UserAuth
    soft_delete = False

    async def get_by_teacher_id(self, teacher_id: str) -> UserAuth | None:
        result = await self.session.execute(
            select(UserAuth).where(UserAuth.teacher_id == teacher_id)
        )
        return result.scalar_one_or_none()
