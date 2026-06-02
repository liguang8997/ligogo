from sqlalchemy import String, Integer, DateTime, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class LanternRiddle(Base):
    __tablename__ = "lantern_riddles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    riddle: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(String(100), nullable=False)
    hint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
