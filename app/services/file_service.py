import aiofiles
from pathlib import Path
from fastapi import UploadFile
from app.utils.file_utils import validate_file, generate_filename, get_upload_path


class FileService:
    async def upload_file(self, file: UploadFile, file_type: str = "attachment") -> dict:
        ext = validate_file(file, file_type)
        filename = generate_filename(ext)
        file_path = get_upload_path(file_type, filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        url = f"/uploads/{'avatars' if file_type == 'avatar' else 'attachments'}/{filename}"
        return {"filename": filename, "url": url, "size": len(content)}

    async def upload_avatar(self, file: UploadFile) -> str:
        result = await self.upload_file(file, file_type="avatar")
        return result["url"]
