from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.course_service import CourseService
from app.schemas.course import CourseCreate, CourseUpdate
from app.schemas.common import ResponseModel, PaginatedData
from app.core.exceptions import AuthorizationException

router = APIRouter(prefix="/courses", tags=["课程管理"])


def _require_leader(request: Request):
    if request.state.role not in ("admin", "leader"):
        raise AuthorizationException("仅领导和管理员可操作")


@router.get("")
async def list_courses(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    teacher_id: str | None = Query(None),
    semester: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = CourseService(db)
    items, total = await svc.list_courses(page, page_size, teacher_id, semester, request.state.user_id, request.state.role)
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(data=PaginatedData(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages))


@router.get("/{course_id}")
async def get_course(course_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    svc = CourseService(db)
    data = await svc.get_course(course_id)
    return ResponseModel(data=data)


@router.post("")
async def create_course(data: CourseCreate, request: Request, db: AsyncSession = Depends(get_db)):
    _require_leader(request)
    svc = CourseService(db)
    course = await svc.create_course(data.model_dump())
    return ResponseModel(data={"id": course.id}, message="课程创建成功")


@router.put("/{course_id}")
async def update_course(course_id: int, data: CourseUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    _require_leader(request)
    svc = CourseService(db)
    await svc.update_course(course_id, data.model_dump(exclude_none=True))
    return ResponseModel(message="课程更新成功")


@router.delete("/{course_id}")
async def delete_course(course_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    _require_leader(request)
    svc = CourseService(db)
    await svc.delete_course(course_id)
    return ResponseModel(message="课程已删除")
