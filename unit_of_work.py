"""Unit of Work: bitta tranzaksiya chegarasi va repositorylar to'plami."""
from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from app.repository.specific import (
    AccountRepository,
    OrderRepository,
    ProductRepository,
    UserRepository,
)


class UnitOfWork:
    """with UnitOfWork(factory) as uow: ...; uow.commit()

    - blok xatolik bilan tugasa, avtomatik ROLLBACK qilinadi;
    - commit() chaqirilmasa, o'zgarishlar saqlanmaydi (sessiya yopilganda bekor bo'ladi).
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "UnitOfWork":
        self.session = self._session_factory()
        self.users = UserRepository(self.session)
        self.products = ProductRepository(self.session)
        self.orders = OrderRepository(self.session)
        self.accounts = AccountRepository(self.session)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is not None:
                self.session.rollback()
        finally:
            self.session.close()
        return False  # xatolikni yutib yubormaymiz

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
