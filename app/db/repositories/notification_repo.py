from sqlalchemy import select, func
from app.db.models.notification import SystemNotification
from app.db.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[SystemNotification]):
    model = SystemNotification

    async def get_unread_count(self, receiver_id: str) -> int:
        stmt = select(func.count()).select_from(SystemNotification).where(
            SystemNotification.receiver_id == receiver_id,
            SystemNotification.is_read == 0,
            SystemNotification.is_deleted == 0,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
