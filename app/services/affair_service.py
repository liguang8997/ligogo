from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, BusinessException
from app.db.repositories.affair_repo import AffairRepository
from app.db.repositories.teacher_repo import TeacherInfoRepository
from app.db.models.affair import TeacherAffair


class AffairService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AffairRepository(session)
        self.teacher_repo = TeacherInfoRepository(session)

    async def create(self, teacher_id: str, data: dict) -> TeacherAffair:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")
        data["teacher_id"] = teacher_id
        data["teacher_name"] = teacher.name
        data["status"] = 1  # 草稿
        affair = TeacherAffair(**data)
        return await self.repo.create(affair)

    async def get(self, affair_id: int) -> dict:
        affair = await self.repo.get_by_id(affair_id)
        if not affair:
            raise NotFoundException("事务不存在")
        return self._to_dict(affair)

    async def list_affairs(self, page: int, page_size: int, user_id: str, role: str, teacher_id: str | None = None,
                           status: int | None = None) -> tuple[list, int]:
        filters = {}
        if role not in ("admin", "leader"):
            filters["teacher_id"] = user_id
        elif teacher_id:
            filters["teacher_id"] = teacher_id
        if status is not None:
            filters["status"] = status
        items, total = await self.repo.find_paginated(page=page, page_size=page_size, order_by="created_at", **filters)
        return [self._to_dict(a) for a in items], total

    async def update(self, affair_id: int, teacher_id: str, data: dict) -> TeacherAffair:
        affair = await self.repo.get_by_id(affair_id)
        if not affair:
            raise NotFoundException("事务不存在")
        if affair.teacher_id != teacher_id:
            raise BusinessException("只能修改自己的事务")
        if affair.status != 1:
            raise BusinessException("仅草稿状态可编辑")
        await self.repo.update(affair_id, data)
        await self.session.refresh(affair)
        return affair

    async def submit(self, affair_id: int, teacher_id: str) -> TeacherAffair:
        affair = await self.repo.get_by_id(affair_id)
        if not affair:
            raise NotFoundException("事务不存在")
        if affair.teacher_id != teacher_id:
            raise BusinessException("只能提交自己的事务")
        if affair.status != 1:
            raise BusinessException("仅草稿状态可提交")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.repo.update(affair_id, {"status": 2, "submitted_at": now})
        await self.session.refresh(affair)
        return affair

    async def approve(self, affair_id: int, approver_id: str, approved: bool, comment: str = None) -> TeacherAffair:
        affair = await self.repo.get_by_id(affair_id)
        if not affair:
            raise NotFoundException("事务不存在")
        if affair.status != 2:
            raise BusinessException("事务不在审批中状态")
        approver = await self.teacher_repo.get_by_teacher_id(approver_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.repo.update(affair_id, {
            "status": 3 if approved else 4,
            "approver_id": approver_id,
            "approver_name": approver.name if approver else "",
            "approval_comment": comment,
            "approval_at": now,
        })
        await self.session.refresh(affair)
        return affair

    async def delete(self, affair_id: int, teacher_id: str) -> None:
        affair = await self.repo.get_by_id(affair_id)
        if not affair:
            raise NotFoundException("事务不存在")
        if affair.teacher_id != teacher_id:
            raise BusinessException("只能删除自己的事务")
        if affair.status not in (1, 5):
            raise BusinessException("仅草稿和已撤回状态可删除")
        await self.repo.soft_delete_by_id(affair_id)

    def _to_dict(self, a: TeacherAffair) -> dict:
        return {
            "id": a.id, "teacher_id": a.teacher_id, "teacher_name": a.teacher_name,
            "affair_type": a.affair_type, "title": a.title, "content": a.content,
            "start_time": str(a.start_time) if a.start_time else None,
            "end_time": str(a.end_time) if a.end_time else None,
            "attachment": a.attachment, "status": a.status,
            "submitted_at": str(a.submitted_at) if a.submitted_at else None,
            "approver_id": a.approver_id, "approver_name": a.approver_name,
            "approval_comment": a.approval_comment,
            "approval_at": str(a.approval_at) if a.approval_at else None,
            "urgency": a.urgency, "created_at": str(a.created_at),
        }
