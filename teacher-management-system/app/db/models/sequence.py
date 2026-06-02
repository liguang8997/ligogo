from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class TeacherSeq(Base):
    __tablename__ = "teacher_seq"

    prefix: Mapped[str] = mapped_column(String(6), primary_key=True)
    current_seq: Mapped[int] = mapped_column(Integer, default=0)
