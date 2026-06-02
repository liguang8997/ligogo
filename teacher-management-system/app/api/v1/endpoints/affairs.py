from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.affair_service import AffairService
from app.schemas.affair import AffairCreate, AffairUpdate, AffairApprove
from app.schemas.common import ResponseModel, PaginatedData
from app.core.exceptions import AuthorizationException

router = APIRouter(prefix="/affairs", tags=["事务管理"])


def _require_leader(request: Request):
    if request.state.role not in ("admin", "leader"):
        raise AuthorizationException("仅领导和管理员可审批")


@router.get("")
async def list_affairs(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    teacher_id: str | None = Query(None),
    status: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = AffairService(db)
    items, total = await svc.list_affairs(page, page_size, request.state.user_id, request.state.role, teacher_id, status)
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages))


@router.get("/{affair_id}")
async def get_affair(affair_id: int, db: AsyncSession = Depends(get_db)):
    svc = AffairService(db)
    data = await svc.get(affair_id)
    return ResponseModel(data=data)


@router.post("")
async def create_affair(data: AffairCreate, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AffairService(db)
    affair = await svc.create(request.state.user_id, data.model_dump())
    return ResponseModel(data={"id": affair.id}, message="事务创建成功")


@router.put("/{affair_id}")
async def update_affair(affair_id: int, data: AffairUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AffairService(db)
    await svc.update(affair_id, request.state.user_id, data.model_dump(exclude_none=True))
    return ResponseModel(message="事务更新成功")


@router.post("/{affair_id}/submit")
async def submit_affair(affair_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AffairService(db)
    await svc.submit(affair_id, request.state.user_id)
    return ResponseModel(message="事务已提交审批")


@router.post("/{affair_id}/approve")
async def approve_affair(affair_id: int, data: AffairApprove, request: Request, db: AsyncSession = Depends(get_db)):
    _require_leader(request)
    svc = AffairService(db)
    await svc.approve(affair_id, request.state.user_id, data.approved, data.comment)
    return ResponseModel(message="审批" + ("通过" if data.approved else "驳回"))


@router.delete("/{affair_id}")
async def delete_affair(affair_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    svc = AffairService(db)
    await svc.delete(affair_id, request.state.user_id)
    return ResponseModel(message="事务已删除")
