from sqlalchemy import String, Integer, BigInteger, DateTime, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class TeacherCourse(Base):
    __tablename__ = "teacher_course"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    teacher_id: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    teacher_name: Mapped[str] = mapped_column(String(30), nullable=False)
    course_name: Mapped[str] = mapped_column(String(100), nullable=False)
    semester: Mapped[str] = mapped_column(String(20), nullable=False)
    class_group: Mapped[str | None] = mapped_column(String(100), nullable=True)
    student_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    course_type: Mapped[int] = mapped_column(SmallInteger, default=1)
    schedule_info: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
