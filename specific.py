"""Entity'ga xos repositorylar (umumiy CRUD ustiga qo'shimcha so'rovlar)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Order, Product, User
from app.repository.sqlalchemy_repo import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session: Session) -> None:
        super().__init__(User, session)

    def find_by_username(self, username: str) -> User | None:
        # ORM parametrlangan so'rov hosil qiladi: SQL Injection'dan himoyalangan
        return self._session.scalars(select(User).where(User.username == username)).first()


class ProductRepository(SqlAlchemyRepository[Product]):
    def __init__(self, session: Session) -> None:
        super().__init__(Product, session)

    def get_by_id_for_update(self, product_id: int) -> Product | None:
        """Qatorni qulflab o'qiydi (PostgreSQL: SELECT ... FOR UPDATE).

        Ikki buyurtma bir vaqtda bir mahsulot qoldig'ini kamaytirganda "yo'qolgan
        yangilanish"ning oldini oladi. SQLite bu so'zni e'tiborsiz qoldiradi.
        """
        stmt = select(Product).where(Product.id == product_id).with_for_update()
        return self._session.scalars(stmt).first()


class OrderRepository(SqlAlchemyRepository[Order]):
    def __init__(self, session: Session) -> None:
        super().__init__(Order, session)


class AccountRepository(SqlAlchemyRepository[Account]):
    def __init__(self, session: Session) -> None:
        super().__init__(Account, session)

    def get_by_id_for_update(self, account_id: int) -> Account | None:
        stmt = select(Account).where(Account.id == account_id).with_for_update()
        return self._session.scalars(stmt).first()
