from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.base import BaseRepository
from app.db.models.log import OperationLog
from app.schemas.common import ResponseModel, PaginatedData
from app.core.exceptions import AuthorizationException

router = APIRouter(prefix="/logs", tags=["操作日志"])


@router.get("")
async def list_logs(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    operator_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if request.state.role != "admin":
        raise AuthorizationException("仅管理员可查看操作日志")
    repo = BaseRepository[OperationLog](db)
    repo.model = OperationLog
    repo.soft_delete = False
    filters = {}
    if operator_id:
        filters["operator_id"] = operator_id
    items, total = await repo.find_paginated(page=page, page_size=page_size, order_by="created_at", **filters)
    data = [{"id": l.id, "operator_id": l.operator_id, "action": l.action,
             "target_type": l.target_type, "target_id": l.target_id,
             "detail": l.detail, "ip_address": l.ip_address,
             "result": l.result, "created_at": str(l.created_at)} for l in items]
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(items=data, total=total, page=page, page_size=page_size, total_pages=total_pages))
