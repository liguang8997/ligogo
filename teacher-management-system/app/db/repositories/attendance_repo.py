from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.attendance import AttendanceRecord
from app.db.repositories.base import BaseRepository
from datetime import date


class AttendanceRepository(BaseRepository[AttendanceRecord]):
    model = AttendanceRecord

    async def get_by_teacher_date(self, teacher_id: str, check_date: date) -> AttendanceRecord | None:
        stmt = select(AttendanceRecord).where(
            and_(
                AttendanceRecord.teacher_id == teacher_id,
                AttendanceRecord.check_date == check_date,
                AttendanceRecord.is_deleted == 0,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
