from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import TeacherCourse
from app.db.repositories.base import BaseRepository


class CourseRepository(BaseRepository[TeacherCourse]):
    model = TeacherCourse

    async def find_conflicts(self, teacher_id: str, schedule_info: str, semester: str, exclude_id: int = None) -> list[TeacherCourse]:
        stmt = (
            select(TeacherCourse)
            .where(
                and_(
                    TeacherCourse.teacher_id == teacher_id,
                    TeacherCourse.schedule_info == schedule_info,
                    TeacherCourse.semester == semester,
                    TeacherCourse.is_deleted == 0,
                )
            )
        )
        if exclude_id:
            stmt = stmt.where(TeacherCourse.id != exclude_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_teacher(self, teacher_id: str) -> list[TeacherCourse]:
        return await self.find_all(teacher_id=teacher_id)
