from sqlalchemy import String, Integer, BigInteger, DateTime, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class TeacherAffair(Base):
    __tablename__ = "teacher_affair"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    teacher_id: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    teacher_name: Mapped[str] = mapped_column(String(30), nullable=False)
    affair_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attachment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approver_id: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    approver_name: Mapped[str | None] = mapped_column(String(30), nullable=True)
    approval_comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    approval_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    urgency: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
