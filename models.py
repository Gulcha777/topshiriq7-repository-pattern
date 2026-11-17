"""ORM modellar."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    # Parol ochiq holda emas, Argon2 hash ko'rinishida saqlanadi
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(default=0)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="new")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int]
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="items")


class Account(Base):
    """Bank hisobi: tranzaksiya (ACID) namoyishi uchun."""

    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("balance >= 0", name="ck_accounts_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(100))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
