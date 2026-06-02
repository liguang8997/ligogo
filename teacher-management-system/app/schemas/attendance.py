from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class AttendanceResponse(BaseModel):
    id: int
    teacher_id: str
    teacher_name: str
    check_date: str
    check_in_time: str | None
    check_out_time: str | None
    status: int
    remark: str | None
    created_at: str


class CheckInResponse(BaseModel):
    check_in_time: str
    status: int
    remark: str | None


class CheckOutResponse(BaseModel):
    check_out_time: str
    status: int
    remark: str | None
