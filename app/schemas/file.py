from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    filename: str
    url: str
    size: int


class AvatarUploadResponse(BaseModel):
    url: str
