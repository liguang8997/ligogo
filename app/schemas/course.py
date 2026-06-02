from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CourseCreate(BaseModel):
    teacher_id: str = Field(..., min_length=8, max_length=8)
    course_name: str = Field(..., min_length=1, max_length=100)
    semester: str = Field(..., max_length=20)
    class_group: str | None = Field(None, max_length=100)
    student_count: int | None = Field(None, ge=0, le=9999)
    course_type: int = Field(default=1, ge=1, le=3)
    schedule_info: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=100)
    remark: str | None = Field(None, max_length=300)


class CourseUpdate(BaseModel):
    course_name: str | None = None
    semester: str | None = None
    class_group: str | None = None
    student_count: int | None = None
    course_type: int | None = None
    schedule_info: str | None = None
    location: str | None = None
    remark: str | None = None


class CourseResponse(BaseModel):
    id: int
    teacher_id: str
    teacher_name: str
    course_name: str
    semester: str
    class_group: str | None
    student_count: int | None
    course_type: int
    schedule_info: str | None
    location: str | None
    remark: str | None
    created_at: datetime
