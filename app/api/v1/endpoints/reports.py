from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.report_service import ReportService
from app.core.exceptions import AuthorizationException

router = APIRouter(prefix="/reports", tags=["报表导出"])


@router.get("/teachers/export")
async def export_teachers(request: Request, db: AsyncSession = Depends(get_db)):
    if request.state.role not in ("admin", "leader"):
        raise AuthorizationException("权限不足")
    svc = ReportService(db)
    return await svc.export_teachers()


@router.get("/attendance/export")
async def export_attendance(request: Request, teacher_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    if request.state.role not in ("admin", "leader"):
        raise AuthorizationException("权限不足")
    svc = ReportService(db)
    return await svc.export_attendance(teacher_id)
