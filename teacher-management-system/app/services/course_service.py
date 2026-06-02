from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, ConflictException
from app.db.repositories.course_repo import CourseRepository
from app.db.repositories.teacher_repo import TeacherInfoRepository
from app.db.models.course import TeacherCourse


class CourseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CourseRepository(session)
        self.teacher_repo = TeacherInfoRepository(session)

    async def create_course(self, data: dict) -> TeacherCourse:
        teacher = await self.teacher_repo.get_by_teacher_id(data["teacher_id"])
        if not teacher:
            raise NotFoundException("教师不存在")

        schedule = data.get("schedule_info", "")
        semester = data.get("semester", "")
        if schedule and semester:
            conflicts = await self.repo.find_conflicts(data["teacher_id"], schedule, semester)
            if conflicts:
                raise ConflictException(f"该教师在 {schedule}({semester}) 已有排课: {conflicts[0].course_name}")

        data["teacher_name"] = teacher.name
        course = TeacherCourse(**data)
        return await self.repo.create(course)

    async def get_course(self, course_id: int) -> dict:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("课程不存在")
        return self._to_dict(course)

    async def list_courses(self, page: int, page_size: int, teacher_id: str | None = None,
                           semester: str | None = None, user_id: str = None, role: str = "teacher") -> tuple[list, int]:
        filters = {}
        if role not in ("admin", "leader"):
            filters["teacher_id"] = user_id
        elif teacher_id:
            filters["teacher_id"] = teacher_id
        if semester:
            filters["semester"] = semester
        items, total = await self.repo.find_paginated(page=page, page_size=page_size, order_by="created_at", **filters)
        return [self._to_dict(c) for c in items], total

    async def update_course(self, course_id: int, data: dict) -> TeacherCourse:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("课程不存在")

        new_schedule = data.get("schedule_info", course.schedule_info)
        new_semester = data.get("semester", course.semester)
        if (new_schedule != course.schedule_info or new_semester != course.semester) and new_schedule:
            conflicts = await self.repo.find_conflicts(course.teacher_id, new_schedule, new_semester, exclude_id=course_id)
            if conflicts:
                raise ConflictException(f"该教师在此时间段已有排课: {conflicts[0].course_name}")

        await self.repo.update(course_id, data)
        await self.session.refresh(course)
        return course

    async def delete_course(self, course_id: int) -> None:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise NotFoundException("课程不存在")
        await self.repo.soft_delete_by_id(course_id)

    def _to_dict(self, c: TeacherCourse) -> dict:
        return {
            "id": c.id, "teacher_id": c.teacher_id, "teacher_name": c.teacher_name,
            "course_name": c.course_name, "semester": c.semester,
            "class_group": c.class_group, "student_count": c.student_count,
            "course_type": c.course_type, "schedule_info": c.schedule_info,
            "location": c.location, "remark": c.remark, "created_at": str(c.created_at),
        }
