from fastapi import APIRouter, UploadFile, File, Query
from app.services.file_service import FileService
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/files", tags=["文件上传"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Query(default="attachment", pattern="^(avatar|attachment)$"),
):
    svc = FileService()
    result = await svc.upload_file(file, file_type)
    return ResponseModel(data=result, message="上传成功")
