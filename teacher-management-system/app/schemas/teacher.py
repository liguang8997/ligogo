from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class TeacherCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    role_code: int = Field(..., ge=1, le=3, description="1-普通教师,2-领导,3-管理员")
    gender: int = Field(default=0, ge=0, le=2)
    birth_date: date | None = None
    id_card: str | None = Field(None, max_length=18)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=50)
    department: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=20)
    education: str | None = Field(None, max_length=20)
    hire_date: date | None = None
    status: int = Field(default=1, ge=1, le=4)
    address: str | None = Field(None, max_length=200)
    remark: str | None = Field(None, max_length=500)
    password: str = Field(..., min_length=6, max_length=32)
    question1: str = Field(..., max_length=100)
    answer1: str = Field(..., max_length=100)
    question2: str = Field(..., max_length=100)
    answer2: str = Field(..., max_length=100)
    question3: str = Field(..., max_length=100)
    answer3: str = Field(..., max_length=100)


class TeacherUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=30)
    gender: int | None = Field(None, ge=0, le=2)
    birth_date: date | None = None
    id_card: str | None = Field(None, max_length=18)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=50)
    department: str | None = Field(None, max_length=50)
    title: str | None = Field(None, max_length=20)
    education: str | None = Field(None, max_length=20)
    hire_date: date | None = None
    status: int | None = Field(None, ge=1, le=4)
    address: str | None = Field(None, max_length=200)
    remark: str | None = Field(None, max_length=500)


class TeacherSelfUpdate(BaseModel):
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=200)
    remark: str | None = Field(None, max_length=500)


class TeacherResponse(BaseModel):
    id: int
    teacher_id: str
    name: str
    gender: int
    birth_date: date | None
    phone: str | None
    email: str | None
    department: str | None
    title: str | None
    education: str | None
    hire_date: date | None
    status: int
    address: str | None
    avatar_url: str | None
    remark: str | None
    created_at: datetime


class TeacherListResponse(BaseModel):
    id: int
    teacher_id: str
    name: str
    gender: int
    phone: str | None
    email: str | None
    department: str | None
    title: str | None
    status: int
    avatar_url: str | None
    hire_date: date | None
