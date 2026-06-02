from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException, BusinessException
from app.db.repositories.notification_repo import NotificationRepository
from app.db.models.notification import SystemNotification


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

    async def list_notifications(self, receiver_id: str, page: int, page_size: int) -> tuple[list, int]:
        items, total = await self.repo.find_paginated(
            page=page, page_size=page_size, receiver_id=receiver_id, order_by="created_at"
        )
        return [self._to_dict(n) for n in items], total

    async def mark_read(self, notification_id: int, receiver_id: str) -> None:
        notif = await self.repo.get_by_id(notification_id)
        if not notif:
            raise NotFoundException("通知不存在")
        if notif.receiver_id != receiver_id:
            raise BusinessException("只能操作自己的通知")
        await self.repo.update(notification_id, {"is_read": 1})

    async def unread_count(self, receiver_id: str) -> int:
        return await self.repo.get_unread_count(receiver_id)

    async def delete(self, notification_id: int, receiver_id: str) -> None:
        notif = await self.repo.get_by_id(notification_id)
        if not notif:
            raise NotFoundException("通知不存在")
        if notif.receiver_id != receiver_id:
            raise BusinessException("只能删除自己的通知")
        await self.repo.soft_delete_by_id(notification_id)

    async def create_notification(self, receiver_id: str, title: str, content: str, notif_type: int, related_id: int = None) -> SystemNotification:
        notif = SystemNotification(
            receiver_id=receiver_id, title=title, content=content,
            type=notif_type, related_id=related_id,
        )
        return await self.repo.create(notif)

    def _to_dict(self, n: SystemNotification) -> dict:
        return {
            "id": n.id, "receiver_id": n.receiver_id, "title": n.title,
            "content": n.content, "type": n.type, "related_id": n.related_id,
            "is_read": n.is_read, "created_at": str(n.created_at),
        }
