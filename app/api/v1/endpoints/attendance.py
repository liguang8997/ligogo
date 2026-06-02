from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.attendance_service import AttendanceService
from app.schemas.attendance import CheckInResponse, CheckOutResponse
from app.schemas.common import ResponseModel, PaginatedData

router = APIRouter(prefix="/attendance", tags=["考勤打卡"])


@router.post("/check-in", response_model=ResponseModel[CheckInResponse])
async def check_in(request: Request, db: AsyncSession = Depends(get_db)):
    svc = AttendanceService(db)
    result = await svc.check_in(request.state.user_id)
    return ResponseModel(data=CheckInResponse(**result), message="打卡成功")


@router.post("/check-out", response_model=ResponseModel[CheckOutResponse])
async def check_out(request: Request, db: AsyncSession = Depends(get_db)):
    svc = AttendanceService(db)
    result = await svc.check_out(request.state.user_id)
    return ResponseModel(data=CheckOutResponse(**result), message="签退成功")


@router.get("")
async def list_records(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    teacher_id: str | None = Query(None),
    month: str | None = Query(None, description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
):
    svc = AttendanceService(db)
    items, total = await svc.list_records(page, page_size, request.state.user_id, request.state.role, teacher_id, month)
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages))
