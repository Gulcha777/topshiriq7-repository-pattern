"""Vazifa 2: servis qatlamidagi tranzaksiya. Xatolikda hamma o'zgarish rollback bo'lishi isboti."""
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.errors import (
    EntityNotFoundError,
    InsufficientStockError,
    InvalidInputError,
    PaymentError,
)
from app.models import Order, OrderItem, Product
from app.services.order_service import OrderLine, OrderService


def state(factory):
    with factory() as s:
        return {
            "stocks": {p.id: p.stock for p in s.scalars(select(Product).order_by(Product.id))},
            "orders": s.scalar(select(func.count(Order.id))),
            "items": s.scalar(select(func.count(OrderItem.id))),
        }


def failing_payment(order):
    raise PaymentError("to'lov rad etildi")


def test_successful_order(uow_factory, factory, ids):
    laptop, mouse, _ = ids["products"]
    res = OrderService(uow_factory).place_order(ids["users"][0], [OrderLine(mouse, 2), OrderLine(laptop, 1)])
    assert res.total == Decimal("7740000.00") and res.status == "new"
    st = state(factory)
    assert st["stocks"][mouse] == 18 and st["stocks"][laptop] == 4
    assert st["orders"] == 1 and st["items"] == 2
    with factory() as s:
        order = s.get(Order, res.order_id)
        assert order.total == res.total and len(order.items) == 2


def test_order_with_payment_is_paid(uow_factory, factory, ids):
    res = OrderService(uow_factory, payment_gateway=lambda o: None).place_order(
        ids["users"][0], [OrderLine(ids["products"][1], 1)]
    )
    assert res.status == "paid"
    with factory() as s:
        assert s.get(Order, res.order_id).status == "paid"


def test_insufficient_stock_rolls_back_everything(uow_factory, factory, ids, tx_events):
    """1-qator (noutbuk) bazaga yozilib bo'lgan, 2-qatorda qoldiq yetmaydi: hammasi bekor bo'ladi."""
    laptop, mouse, keyboard = ids["products"]
    before = state(factory)
    commits_before = tx_events["commit"]
    with pytest.raises(InsufficientStockError):
        OrderService(uow_factory).place_order(
            ids["users"][0], [OrderLine(laptop, 2), OrderLine(keyboard, 5)]
        )
    assert state(factory) == before                       # qoldiq ham, buyurtma ham o'zgarmagan
    assert tx_events["commit"] == commits_before          # commit umuman bo'lmagan
    assert tx_events["rollback"] >= 1                     # ROLLBACK bajarilgan


def test_payment_failure_rolls_back_everything(uow_factory, factory, ids):
    laptop, mouse, _ = ids["products"]
    before = state(factory)
    with pytest.raises(PaymentError):
        OrderService(uow_factory, payment_gateway=failing_payment).place_order(
            ids["users"][0], [OrderLine(laptop, 1), OrderLine(mouse, 3)]
        )
    assert state(factory) == before


def test_unknown_product_rolls_back_previous_lines(uow_factory, factory, ids):
    before = state(factory)
    with pytest.raises(EntityNotFoundError):
        OrderService(uow_factory).place_order(
            ids["users"][0], [OrderLine(ids["products"][0], 1), OrderLine(99999, 1)]
        )
    assert state(factory) == before


def test_unknown_user(uow_factory, factory, ids):
    before = state(factory)
    with pytest.raises(EntityNotFoundError):
        OrderService(uow_factory).place_order(424242, [OrderLine(ids["products"][0], 1)])
    assert state(factory) == before


def test_empty_order_rejected(uow_factory, ids):
    with pytest.raises(InvalidInputError):
        OrderService(uow_factory).place_order(ids["users"][0], [])


@pytest.mark.parametrize("qty", [0, -3])
def test_non_positive_quantity_rolls_back(uow_factory, factory, ids, qty):
    before = state(factory)
    with pytest.raises(InvalidInputError):
        OrderService(uow_factory).place_order(
            ids["users"][0], [OrderLine(ids["products"][0], 1), OrderLine(ids["products"][1], qty)]
        )
    assert state(factory) == before


def test_same_product_twice_cannot_exceed_stock(uow_factory, factory, ids):
    keyboard = ids["products"][2]  # qoldiq: 1
    before = state(factory)
    with pytest.raises(InsufficientStockError):
        OrderService(uow_factory).place_order(
            ids["users"][0], [OrderLine(keyboard, 1), OrderLine(keyboard, 1)]
        )
    assert state(factory) == before


def test_stock_is_depleted_exactly_then_fails(uow_factory, factory, ids):
    keyboard = ids["products"][2]
    svc = OrderService(uow_factory)
    svc.place_order(ids["users"][0], [OrderLine(keyboard, 1)])
    assert state(factory)["stocks"][keyboard] == 0
    with pytest.raises(InsufficientStockError):
        svc.place_order(ids["users"][1], [OrderLine(keyboard, 1)])
    assert state(factory)["stocks"][keyboard] == 0
    assert state(factory)["orders"] == 1


def test_cache_invalidated_only_after_successful_commit(uow_factory, ids, cache):
    laptop = ids["products"][0]
    cache.set(laptop, {"id": laptop, "stock": 5})
    svc = OrderService(uow_factory, payment_gateway=failing_payment, product_cache=cache)
    with pytest.raises(PaymentError):
        svc.place_order(ids["users"][0], [OrderLine(laptop, 1)])
    assert cache.get(laptop) is not None                 # xatolikda kesh tegilmagan
    OrderService(uow_factory, product_cache=cache).place_order(ids["users"][0], [OrderLine(laptop, 1)])
    assert cache.get(laptop) is None                     # muvaffaqiyatda bekor qilingan
