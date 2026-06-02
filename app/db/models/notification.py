from sqlalchemy import String, Integer, BigInteger, DateTime, Text, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class SystemNotification(Base):
    __tablename__ = "system_notification"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    receiver_id: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    related_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_read: Mapped[int] = mapped_column(SmallInteger, default=0)
    is_deleted: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
