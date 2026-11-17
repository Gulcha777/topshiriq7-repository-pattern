"""SQL Injection: zaif (faqat namoyish uchun) va xavfsiz variantlar.

DIQQAT: insecure_* funksiyalarni haqiqiy loyihada ishlatmang!
"""
from __future__ import annotations

from sqlalchemy import Connection, text


def insecure_find_users(conn: Connection, name: str) -> list[tuple]:
    """ZAIF: foydalanuvchi matni SQL ichiga to'g'ridan-to'g'ri qo'shiladi."""
    sql = "SELECT id, username FROM users WHERE username = '" + name + "'"
    return [tuple(r) for r in conn.exec_driver_sql(sql).fetchall()]


def secure_find_users(conn: Connection, name: str) -> list[tuple]:
    """XAVFSIZ: qiymat alohida parametr sifatida yuboriladi, SQL matniga qo'shilmaydi."""
    stmt = text("SELECT id, username FROM users WHERE username = :name")
    return [tuple(r) for r in conn.execute(stmt, {"name": name}).fetchall()]


# Hujum namunalari
PAYLOAD_ALL_ROWS = "' OR '1'='1"
PAYLOAD_UNION_LEAK = "' UNION SELECT id, password_hash FROM users --"
PAYLOAD_DROP = "x'; DROP TABLE users; --"
