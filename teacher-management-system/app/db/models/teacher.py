from sqlalchemy import String, Integer, BigInteger, Date, DateTime, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class TeacherInfo(Base):
    __tablename__ = "teacher_info"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    teacher_id: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    gender: Mapped[int] = mapped_column(SmallInteger, default=0)
    birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    id_card: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str | None] = mapped_column(String(20), nullable=True)
    education: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hire_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class UserAuth(Base):
    __tablename__ = "user_auth"

    teacher_id: Mapped[str] = mapped_column(String(8), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    question1_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    question2_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    question3_answer: Mapped[str] = mapped_column(String(200), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(SmallInteger, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
