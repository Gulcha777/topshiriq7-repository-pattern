"""Namunaviy ma'lumotlar (demo va qo'lda sinash uchun)."""
from __future__ import annotations

from decimal import Decimal

from app.database import init_db, make_engine, make_session_factory
from app.models import Account, Product
from app.security.passwords import PasswordService
from app.services.auth_service import AuthService
from app.unit_of_work import UnitOfWork

DEMO_PASSWORD = "Parol12345"


def seed(factory, passwords: PasswordService | None = None) -> dict:
    """Bo'sh bazani to'ldiradi va yaratilgan identifikatorlarni qaytaradi."""
    uow_factory = lambda: UnitOfWork(factory)  # noqa: E731
    auth = AuthService(uow_factory, passwords)
    ids = {"users": [auth.register(n, DEMO_PASSWORD) for n in ("aziz", "dilnoza", "sardor")]}
    with uow_factory() as uow:
        prods = [
            uow.products.create(Product(name=n, price=Decimal(p), stock=s))
            for n, p, s in [
                ("Noutbuk", "7500000.00", 5),
                ("Sichqoncha", "120000.00", 20),
                ("Klaviatura", "210000.00", 1),
            ]
        ]
        accs = [
            uow.accounts.create(Account(owner=o, balance=Decimal(b)))
            for o, b in [("Aziz", "1000.00"), ("Dilnoza", "500.00")]
        ]
        uow.commit()
        ids["products"] = [p.id for p in prods]
        ids["accounts"] = [a.id for a in accs]
    return ids


def main() -> None:
    engine = make_engine()
    init_db(engine)
    factory = make_session_factory(engine)
    with UnitOfWork(factory) as uow:
        empty = not uow.users.get_all()
    if empty:
        print("Seed:", seed(factory))
    else:
        print("Baza bo'sh emas, seed o'tkazib yuborildi.")


if __name__ == "__main__":
    main()
