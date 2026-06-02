from typing import Any, Generic, TypeVar
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: type[ModelType]
    soft_delete: bool = True

    def __init__(self, session: AsyncSession):
        self.session = session

    def _apply_filters(self, stmt: Select, **kwargs) -> Select:
        if self.soft_delete and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == 0)
        for field, value in kwargs.items():
            if value is not None and hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        return stmt

    async def get_by_id(self, id_value: Any, id_field: str = "id") -> ModelType | None:
        stmt = select(self.model).where(getattr(self.model, id_field) == id_value)
        if self.soft_delete and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == 0)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_all(self, **kwargs) -> list[ModelType]:
        stmt = self._apply_filters(select(self.model), **kwargs)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_paginated(
        self, page: int = 1, page_size: int = 10, order_by: str = None, **kwargs
    ) -> tuple[list[ModelType], int]:
        stmt = self._apply_filters(select(self.model), **kwargs)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        if order_by and hasattr(self.model, order_by):
            stmt = stmt.order_by(getattr(self.model, order_by).desc())

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, id_value: Any, update_data: dict, id_field: str = "id") -> int:
        stmt = (
            update(self.model)
            .where(getattr(self.model, id_field) == id_value)
            .values(**update_data)
        )
        if self.soft_delete and hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted == 0)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def soft_delete_by_id(self, id_value: Any, id_field: str = "id") -> int:
        stmt = (
            update(self.model)
            .where(getattr(self.model, id_field) == id_value)
            .values(is_deleted=1)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def hard_delete(self, id_value: Any, id_field: str = "id") -> int:
        stmt = delete(self.model).where(getattr(self.model, id_field) == id_value)
        result = await self.session.execute(stmt)
        return result.rowcount
