"""Vazifa 2: servis qatlamida tranzaksiya va rollback namoyishi.

Ishga tushirish:  python -m app.demo_transaction
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select

from app.demo_utils import temp_database
from app.errors import DomainError, InsufficientStockError, PaymentError
from app.models import Account, Order, OrderItem, Product
from app.seed import seed
from app.services.account_service import AccountService
from app.services.order_service import OrderLine, OrderService
from app.unit_of_work import UnitOfWork


def snapshot(factory) -> str:
    with factory() as s:
        stocks = {p.name: p.stock for p in s.scalars(select(Product).order_by(Product.id))}
        orders = s.scalar(select(func.count(Order.id)))
        items = s.scalar(select(func.count(OrderItem.id)))
    return f"qoldiq={stocks}, buyurtmalar={orders}, qatorlar={items}"


def failing_payment(order) -> None:
    raise PaymentError("To'lov tizimi javob bermadi")


def main() -> None:
    _, factory = temp_database()
    ids = seed(factory)
    uow_factory = lambda: UnitOfWork(factory)  # noqa: E731
    user = ids["users"][0]
    laptop, mouse, keyboard = ids["products"]

    print("Boshlang'ich holat:\n ", snapshot(factory))

    print("\n1) Muvaffaqiyatli buyurtma (2 ta sichqoncha + 1 ta noutbuk)")
    res = OrderService(uow_factory).place_order(
        user, [OrderLine(mouse, 2), OrderLine(laptop, 1)]
    )
    print(f"  natija: buyurtma #{res.order_id}, summa={res.total}, holat={res.status}")
    print(" ", snapshot(factory))

    print("\n2) Ikkinchi qatorda qoldiq yetmaydi (klaviatura: 1 ta bor, 5 ta so'ralgan)")
    try:
        OrderService(uow_factory).place_order(
            user, [OrderLine(mouse, 3), OrderLine(keyboard, 5)]
        )
    except InsufficientStockError as exc:
        print(f"  xatolik: {exc}")
    print("  rollback'dan keyin:", snapshot(factory))

    print("\n3) Hamma narsa tayyor bo'lgach, to'lov xato beradi")
    try:
        OrderService(uow_factory, payment_gateway=failing_payment).place_order(
            user, [OrderLine(mouse, 4)]
        )
    except PaymentError as exc:
        print(f"  xatolik: {exc}")
    print("  rollback'dan keyin:", snapshot(factory))

    print("\n4) Bank o'tkazmasi: yechib olingandan keyin xatolik (atomiklik)")
    a, b = ids["accounts"]

    def boom() -> None:
        raise RuntimeError("Server o'chib qoldi")

    def balances() -> str:
        with factory() as s:
            return str([(x.owner, str(x.balance)) for x in s.scalars(select(Account).order_by(Account.id))])

    print("  oldin :", balances())
    try:
        AccountService(uow_factory, after_debit=boom).transfer(a, b, Decimal("300"))
    except RuntimeError as exc:
        print(f"  xatolik: {exc}")
    print("  keyin :", balances(), "(pul yo'qolmadi)")
    AccountService(uow_factory).transfer(a, b, Decimal("300"))
    print("  muvaffaqiyatli o'tkazma:", balances())
    try:
        AccountService(uow_factory).transfer(a, b, Decimal("5000"))
    except DomainError as exc:
        print(f"  xatolik: {exc}")
    print("  yakuniy:", balances())


if __name__ == "__main__":
    main()
