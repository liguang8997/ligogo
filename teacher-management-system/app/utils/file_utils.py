import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import get_settings
from app.core.exceptions import FileUploadException

settings = get_settings()


def validate_file(file: UploadFile, file_type: str = "attachment") -> str:
    """
    校验文件类型和大小，返回文件扩展名。
    file_type: 'avatar' 或 'attachment'
    """
    if not file.filename:
        raise FileUploadException("文件名不能为空")

    ext = Path(file.filename).suffix.lower().lstrip(".")
    if not ext:
        raise FileUploadException("无法识别文件类型")

    if file_type == "avatar":
        if ext not in settings.allowed_image_extensions:
            raise FileUploadException(f"头像仅支持图片格式: {settings.ALLOWED_IMAGE_TYPES}")
        max_size = settings.MAX_AVATAR_SIZE
    else:
        if ext not in settings.allowed_extensions:
            raise FileUploadException(
                f"不支持的文件类型，允许: {settings.ALLOWED_IMAGE_TYPES},{settings.ALLOWED_DOC_TYPES}"
            )
        max_size = settings.MAX_ATTACHMENT_SIZE

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > max_size:
        max_mb = max_size / 1024 / 1024
        raise FileUploadException(f"文件大小不能超过{max_mb:.0f}MB")

    return ext


def generate_filename(ext: str) -> str:
    return f"{uuid.uuid4().hex}.{ext}"


def get_upload_path(file_type: str, filename: str) -> Path:
    sub_dir = "avatars" if file_type == "avatar" else "attachments"
    return Path(settings.UPLOAD_DIR) / sub_dir / filename


def ensure_upload_dirs():
    (Path(settings.UPLOAD_DIR) / "avatars").mkdir(parents=True, exist_ok=True)
    (Path(settings.UPLOAD_DIR) / "attachments").mkdir(parents=True, exist_ok=True)
