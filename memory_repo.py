"""IRepository'ning xotiradagi implementatsiyasi (testlar va prototip uchun)."""
from __future__ import annotations

from typing import Generic, TypeVar

from app.errors import EntityNotFoundError
from app.repository.base import IRepository

T = TypeVar("T")


class InMemoryRepository(IRepository[T, int], Generic[T]):
    """Ob'ektlar `id` atributiga ega bo'lishi kerak."""

    def __init__(self) -> None:
        self._items: dict[int, T] = {}
        self._next_id = 1

    def create(self, entity: T) -> T:
        if getattr(entity, "id", None) is None:
            entity.id = self._next_id  # type: ignore[attr-defined]
        self._next_id = max(self._next_id, entity.id + 1)  # type: ignore[attr-defined]
        self._items[entity.id] = entity  # type: ignore[attr-defined]
        return entity

    def get_by_id(self, entity_id: int) -> T | None:
        return self._items.get(entity_id)

    def get_all(self) -> list[T]:
        return [self._items[k] for k in sorted(self._items)]

    def update(self, entity: T) -> T:
        entity_id = getattr(entity, "id", None)
        if entity_id not in self._items:
            raise EntityNotFoundError(f"id={entity_id} topilmadi")
        self._items[entity_id] = entity
        return entity

    def delete(self, entity_id: int) -> bool:
        return self._items.pop(entity_id, None) is not None
