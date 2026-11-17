"""IRepository'ning ORM (SQLAlchemy) asosidagi implementatsiyasi."""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import EntityNotFoundError
from app.repository.base import IRepository

T = TypeVar("T")


class SqlAlchemyRepository(IRepository[T, int], Generic[T]):
    """Repository commit qilmaydi: tranzaksiyani UnitOfWork/servis boshqaradi.

    Faqat flush() qiladi, shunda o'zgarishlar bazaga yuboriladi (id olinadi),
    lekin tranzaksiya yakunlanmaguncha rollback qilish mumkin.
    """

    def __init__(self, model: type[T], session: Session) -> None:
        self._model = model
        self._session = session

    def create(self, entity: T) -> T:
        self._session.add(entity)
        self._session.flush()
        return entity

    def get_by_id(self, entity_id: int) -> T | None:
        return self._session.get(self._model, entity_id)

    def get_all(self) -> list[T]:
        stmt = select(self._model).order_by(self._model.id)  # type: ignore[attr-defined]
        return list(self._session.scalars(stmt).all())

    def update(self, entity: T) -> T:
        entity_id = getattr(entity, "id", None)
        if entity_id is None or self._session.get(self._model, entity_id) is None:
            raise EntityNotFoundError(f"{self._model.__name__} id={entity_id} topilmadi")
        merged = self._session.merge(entity)
        self._session.flush()
        return merged

    def delete(self, entity_id: int) -> bool:
        obj = self._session.get(self._model, entity_id)
        if obj is None:
            return False
        self._session.delete(obj)
        self._session.flush()
        return True
