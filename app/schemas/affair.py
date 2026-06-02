from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class AffairCreate(BaseModel):
    affair_type: int = Field(..., ge=1, le=6, description="1-事假,2-病假,3-调课,4-出差,5-报销,6-反馈")
    title: str = Field(..., min_length=1, max_length=100)
    content: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    attachment: str | None = Field(None, max_length=500)
    urgency: int = Field(default=0, ge=0, le=1)


class AffairUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    attachment: str | None = None
    urgency: int | None = None


class AffairApprove(BaseModel):
    approved: bool = Field(...)
    comment: str | None = Field(None, max_length=500)


class AffairResponse(BaseModel):
    id: int
    teacher_id: str
    teacher_name: str
    affair_type: int
    title: str
    content: str | None
    start_time: str | None
    end_time: str | None
    attachment: str | None
    status: int
    submitted_at: str | None
    approver_id: str | None
    approver_name: str | None
    approval_comment: str | None
    approval_at: str | None
    urgency: int
    created_at: str
