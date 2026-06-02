from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.notification_service import NotificationService
from app.schemas.common import ResponseModel, PaginatedData

router = APIRouter(prefix="/notifications", tags=["消息通知"])


@router.get("")
async def list_notifications(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    items, total = await svc.list_notifications(request.state.user_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages))


@router.put("/{notification_id}/read")
async def mark_read(notification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    svc = NotificationService(db)
    await svc.mark_read(notification_id, request.state.user_id)
    return ResponseModel(message="已标记为已读")


@router.get("/unread-count")
async def unread_count(request: Request, db: AsyncSession = Depends(get_db)):
    svc = NotificationService(db)
    count = await svc.unread_count(request.state.user_id)
    return ResponseModel(data={"count": count})


@router.delete("/{notification_id}")
async def delete_notification(notification_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    svc = NotificationService(db)
    await svc.delete(notification_id, request.state.user_id)
    return ResponseModel(message="通知已删除")
