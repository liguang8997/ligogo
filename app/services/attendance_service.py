from datetime import datetime, date, time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.exceptions import NotFoundException, BusinessException
from app.db.repositories.attendance_repo import AttendanceRepository
from app.db.repositories.teacher_repo import TeacherInfoRepository
from app.db.models.attendance import AttendanceRecord

settings = get_settings()


class AttendanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AttendanceRepository(session)
        self.teacher_repo = TeacherInfoRepository(session)

    async def check_in(self, teacher_id: str) -> dict:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")

        today = date.today()
        existing = await self.repo.get_by_teacher_date(teacher_id, today)
        if existing:
            raise BusinessException("今日已打卡，请勿重复操作")

        now = datetime.now()
        check_in_time = now
        status = 1  # 正常
        remark = None

        check_in_end = self._parse_time(settings.CHECK_IN_END)
        if now.time() > check_in_end:
            status = 2  # 迟到
            remark = "迟到"

        record = AttendanceRecord(
            teacher_id=teacher_id,
            teacher_name=teacher.name,
            check_date=today,
            check_in_time=check_in_time,
            status=status,
            remark=remark,
        )
        await self.repo.create(record)
        return {"check_in_time": str(check_in_time), "status": status, "remark": remark}

    async def check_out(self, teacher_id: str) -> dict:
        teacher = await self.teacher_repo.get_by_teacher_id(teacher_id)
        if not teacher:
            raise NotFoundException("教师不存在")

        today = date.today()
        record = await self.repo.get_by_teacher_date(teacher_id, today)
        if not record:
            raise BusinessException("请先完成上班打卡")

        if record.check_out_time:
            raise BusinessException("今日已签退")

        now = datetime.now()
        check_out_start = self._parse_time(settings.CHECK_OUT_START)
        if now.time() < check_out_start:
            record.status = 3  # 早退
            if not record.remark:
                record.remark = "早退"

        record.check_out_time = now
        return {"check_out_time": str(now), "status": record.status, "remark": record.remark}

    async def list_records(self, page: int, page_size: int, user_id: str, role: str,
                           teacher_id: str | None = None, month: str | None = None) -> tuple[list, int]:
        filters = {}
        if role not in ("admin", "leader"):
            filters["teacher_id"] = user_id
        elif teacher_id:
            filters["teacher_id"] = teacher_id
        items, total = await self.repo.find_paginated(page=page, page_size=page_size, order_by="check_date", **filters)
        records = [self._to_dict(r) for r in items]
        if month:
            records = [r for r in records if r["check_date"].startswith(month)]
        return records, total

    async def get_today_record(self, teacher_id: str) -> dict | None:
        today = date.today()
        record = await self.repo.get_by_teacher_date(teacher_id, today)
        return self._to_dict(record) if record else None

    def _to_dict(self, r: AttendanceRecord) -> dict:
        return {
            "id": r.id, "teacher_id": r.teacher_id, "teacher_name": r.teacher_name,
            "check_date": str(r.check_date),
            "check_in_time": str(r.check_in_time) if r.check_in_time else None,
            "check_out_time": str(r.check_out_time) if r.check_out_time else None,
            "status": r.status, "remark": r.remark, "created_at": str(r.created_at),
        }

    def _parse_time(self, t: str) -> time:
        h, m = t.split(":")
        return time(int(h), int(m))
