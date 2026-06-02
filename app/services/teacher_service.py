from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password
from app.core.exceptions import BusinessException, NotFoundException
from app.utils.crypto import encrypt_sensitive_data
from app.utils.teacher_id_generator import generate_teacher_id
from app.utils.common import mask_id_card
from app.db.repositories.teacher_repo import TeacherInfoRepository, UserAuthRepository
from app.db.models.teacher import TeacherInfo, UserAuth


class TeacherService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.teacher_repo = TeacherInfoRepository(session)
        self.user_repo = UserAuthRepository(session)

    async def create_teacher(self, data: dict) -> TeacherInfo:
        if data.get("id_card"):
            data["id_card"] = encrypt_sensitive_data(data["id_card"])

        password = data.pop("password")
        answers = {
            "q1": encrypt_sensitive_data(data.pop("answer1")),
            "q2": encrypt_sensitive_data(data.pop("answer2")),
            "q3": encrypt_sensitive_data(data.pop("answer3")),
        }
        data.pop("question1", None)
        data.pop("question2", None)
        data.pop("question3", None)
        role_code = data.pop("role_code", 1)

        teacher_id = await generate_teacher_id(role_code, self.session)
        data["teacher_id"] = teacher_id

        teacher = TeacherInfo(**data)
        teacher = await self.teacher_repo.create(teacher)

        auth = UserAuth(
            teacher_id=teacher_id,
            password_hash=hash_password(password),
            question1_answer=answers["q1"],
            question2_answer=answers["q2"],
            question3_answer=answers["q3"],
        )
        self.session.add(auth)

        return teacher

    async def get_teacher(self, teacher_id: str) -> dict:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")
        return self._to_response(teacher)

    async def list_teachers(self, page: int, page_size: int, department: str | None = None,
                            status: int | None = None, keyword: str | None = None) -> tuple[list, int]:
        filters = {}
        if department:
            filters["department"] = department
        if status is not None:
            filters["status"] = status

        # TODO: keyword search across name/department
        items, total = await self.teacher_repo.find_paginated(page=page, page_size=page_size, order_by="created_at", **filters)
        return [self._to_list_item(t) for t in items], total

    async def update_teacher(self, teacher_id: str, data: dict, is_admin: bool) -> TeacherInfo:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")

        if not is_admin:
            allowed = {"phone", "email", "address", "remark"}
            data = {k: v for k, v in data.items() if k in allowed}

        if data.get("id_card"):
            data["id_card"] = encrypt_sensitive_data(data["id_card"])

        if data:
            await self.teacher_repo.update(teacher_id, data, id_field="teacher_id")
        await self.session.refresh(teacher)
        return teacher

    async def delete_teacher(self, teacher_id: str) -> None:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")
        await self.teacher_repo.soft_delete_by_id(teacher_id, id_field="teacher_id")

    def _to_response(self, t: TeacherInfo) -> dict:
        return {
            "id": t.id,
            "teacher_id": t.teacher_id,
            "name": t.name,
            "gender": t.gender,
            "birth_date": str(t.birth_date) if t.birth_date else None,
            "id_card": mask_id_card(t.id_card) if t.id_card else None,
            "phone": t.phone,
            "email": t.email,
            "department": t.department,
            "title": t.title,
            "education": t.education,
            "hire_date": str(t.hire_date) if t.hire_date else None,
            "status": t.status,
            "address": t.address,
            "avatar_url": t.avatar_url,
            "remark": t.remark,
            "created_at": str(t.created_at),
        }

    def _to_list_item(self, t: TeacherInfo) -> dict:
        return {
            "id": t.id,
            "teacher_id": t.teacher_id,
            "name": t.name,
            "gender": t.gender,
            "phone": t.phone,
            "email": t.email,
            "department": t.department,
            "title": t.title,
            "status": t.status,
            "avatar_url": t.avatar_url,
            "hire_date": str(t.hire_date) if t.hire_date else None,
        }
