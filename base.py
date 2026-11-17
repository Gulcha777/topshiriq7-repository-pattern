"""Vazifa 1: generik IRepository interfeysi (Create, GetById, GetAll, Update, Delete)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class IRepository(ABC, Generic[T, ID]):
    """Ma'lumotlar manbasidan mustaqil CRUD shartnomasi.

    Servis qatlami faqat shu interfeysga tayanadi; qaysi saqlash usuli (ORM, xotira,
    boshqa baza) ishlatilishini bilmaydi.
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Yangi ob'ektni saqlaydi va identifikatori berilgan holda qaytaradi."""

    @abstractmethod
    def get_by_id(self, entity_id: ID) -> T | None:
        """Identifikator bo'yicha ob'ektni qaytaradi, topilmasa None."""

    @abstractmethod
    def get_all(self) -> list[T]:
        """Barcha ob'ektlarni identifikator tartibida qaytaradi."""

    @abstractmethod
    def update(self, entity: T) -> T:
        """Mavjud ob'ektni yangilaydi; yo'q bo'lsa EntityNotFoundError."""

    @abstractmethod
    def delete(self, entity_id: ID) -> bool:
        """Ob'ektni o'chiradi; o'chirilgan bo'lsa True, topilmasa False."""
