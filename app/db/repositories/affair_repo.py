from app.db.models.affair import TeacherAffair
from app.db.repositories.base import BaseRepository


class AffairRepository(BaseRepository[TeacherAffair]):
    model = TeacherAffair

    async def find_by_teacher(self, teacher_id: str) -> list[TeacherAffair]:
        return await self.find_all(teacher_id=teacher_id)

    async def find_pending_approval(self, approver_id: str) -> list[TeacherAffair]:
        return await self.find_all(approver_id=approver_id, status=2)
