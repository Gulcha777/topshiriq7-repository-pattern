"""Vazifa 2: servis qatlamida tranzaksiya: buyurtma yaratish (xatolikda to'liq rollback)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from app.cache import ProductCache
from app.errors import EntityNotFoundError, InsufficientStockError, InvalidInputError
from app.models import Order, OrderItem


@dataclass(frozen=True)
class OrderLine:
    product_id: int
    quantity: int


@dataclass(frozen=True)
class OrderResult:
    order_id: int
    total: Decimal
    status: str


class OrderService:
    def __init__(
        self,
        uow_factory,
        payment_gateway: Callable[[Order], None] | None = None,
        product_cache: ProductCache | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._payment = payment_gateway
        self._cache = product_cache

    def place_order(self, user_id: int, lines: list[OrderLine]) -> OrderResult:
        """Buyurtma, qatorlar, ombor qoldig'i va to'lov BITTA tranzaksiyada bajariladi.

        Istalgan bosqichda xatolik yuz bersa (qoldiq yetmasi, to'lov xatosi va h.k.),
        UnitOfWork ROLLBACK qiladi: buyurtma ham, qoldiq o'zgarishi ham saqlanmaydi.
        """
        if not lines:
            raise InvalidInputError("Buyurtma bo'sh bo'lishi mumkin emas")

        touched: set[int] = set()
        with self._uow_factory() as uow:
            if uow.users.get_by_id(user_id) is None:
                raise EntityNotFoundError(f"Foydalanuvchi id={user_id} topilmadi")

            order = uow.orders.create(Order(user_id=user_id, status="new", total=Decimal("0")))
            total = Decimal("0")
            for line in lines:
                if line.quantity <= 0:
                    raise InvalidInputError("Miqdor musbat bo'lishi kerak")
                product = uow.products.get_by_id_for_update(line.product_id)
                if product is None:
                    raise EntityNotFoundError(f"Mahsulot id={line.product_id} topilmadi")
                if product.stock < line.quantity:
                    raise InsufficientStockError(
                        f"'{product.name}': qoldiq {product.stock}, so'ralgan {line.quantity}"
                    )
                product.stock -= line.quantity          # bazaga flush qilinadi (hali commit emas)
                uow.products.update(product)
                order.items.append(
                    OrderItem(product_id=product.id, quantity=line.quantity, unit_price=product.price)
                )
                total += product.price * line.quantity
                touched.add(product.id)

            order.total = total
            uow.orders.update(order)

            if self._payment is not None:
                self._payment(order)                    # xatolik bo'lsa, hammasi rollback
                order.status = "paid"
                uow.orders.update(order)

            uow.commit()
            result = OrderResult(order_id=order.id, total=total, status=order.status)

        # Kesh faqat muvaffaqiyatli commit'dan keyin yangilanadi
        if self._cache is not None:
            for pid in touched:
                self._cache.invalidate(pid)
        return result
