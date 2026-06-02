from fastapi import APIRouter, Depends, Request, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.teacher_service import TeacherService
from app.services.file_service import FileService
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherSelfUpdate
from app.schemas.common import ResponseModel, PaginatedData
from app.core.exceptions import AuthorizationException

router = APIRouter(prefix="/teachers", tags=["教师管理"])


def _check_permission(request: Request, target_teacher_id: str = None):
    role = request.state.role
    user_id = request.state.user_id
    if role in ("admin", "leader"):
        return
    if target_teacher_id and user_id == target_teacher_id:
        return
    raise AuthorizationException("权限不足")


@router.get("")
async def list_teachers(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    department: str | None = Query(None),
    status: int | None = Query(None),
    keyword: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    _check_permission(request)
    svc = TeacherService(db)
    items, total = await svc.list_teachers(page, page_size, department, status, keyword)
    total_pages = (total + page_size - 1) // page_size
    return ResponseModel(
        data=PaginatedData(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages),
        message="success",
    )


@router.get("/{teacher_id}")
async def get_teacher(teacher_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    _check_permission(request, teacher_id)
    svc = TeacherService(db)
    data = await svc.get_teacher(teacher_id)
    return ResponseModel(data=data)


@router.post("")
async def create_teacher(data: TeacherCreate, request: Request, db: AsyncSession = Depends(get_db)):
    _check_permission(request)
    svc = TeacherService(db)
    teacher = await svc.create_teacher(data.model_dump())
    return ResponseModel(data={"teacher_id": teacher.teacher_id}, message="教师创建成功")


@router.put("/{teacher_id}")
async def update_teacher(teacher_id: str, data: TeacherUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    role = request.state.role
    is_admin = role in ("admin", "leader")
    if not is_admin:
        _check_permission(request, teacher_id)
        self_data = TeacherSelfUpdate(**data.model_dump(exclude_none=True))
        data = self_data
    svc = TeacherService(db)
    teacher = await svc.update_teacher(teacher_id, data.model_dump(exclude_none=True), is_admin)
    return ResponseModel(message="教师信息更新成功")


@router.delete("/{teacher_id}")
async def delete_teacher(teacher_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    if request.state.role != "admin":
        raise AuthorizationException("仅管理员可删除教师")
    svc = TeacherService(db)
    await svc.delete_teacher(teacher_id)
    return ResponseModel(message="教师已删除")


@router.post("/{teacher_id}/avatar")
async def upload_avatar(teacher_id: str, file: UploadFile = File(...), request: Request = None, db: AsyncSession = Depends(get_db)):
    _check_permission(request, teacher_id)
    file_svc = FileService()
    url = await file_svc.upload_avatar(file)
    svc = TeacherService(db)
    await svc.update_teacher(teacher_id, {"avatar_url": url}, is_admin=True)
    return ResponseModel(data={"url": url}, message="头像上传成功")
