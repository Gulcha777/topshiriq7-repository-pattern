"""Vazifa 3: SQL Injection'ni namoyish etish va xavfsiz variant, parol hash'lari.

Ishga tushirish:  python -m app.demo_sqli
"""
from __future__ import annotations

from sqlalchemy import text

from app.demo_utils import temp_database
from app.security.sqli_demo import (
    PAYLOAD_ALL_ROWS,
    PAYLOAD_DROP,
    PAYLOAD_UNION_LEAK,
    insecure_find_users,
    secure_find_users,
)
from app.seed import DEMO_PASSWORD, seed
from app.services.auth_service import AuthService
from app.unit_of_work import UnitOfWork


def short(rows):
    return [(r[0], (str(r[1])[:34] + "...") if len(str(r[1])) > 34 else r[1]) for r in rows]


def main() -> None:
    engine, factory = temp_database()
    seed(factory)

    print("Bazadagi parollar (Argon2 hash, ochiq parol emas):")
    with engine.connect() as conn:
        for row in conn.execute(text("SELECT username, password_hash FROM users ORDER BY id")):
            print(f"  {row[0]:<8} {row[1][:48]}...")

    attacks = [
        ("Oddiy so'rov", "aziz"),
        ("Hujum 1: hamma qatorni olish", PAYLOAD_ALL_ROWS),
        ("Hujum 2: UNION bilan hash'larni o'g'irlash", PAYLOAD_UNION_LEAK),
    ]
    print("\nZAIF kod (SQL matniga qo'shish):")
    with engine.connect() as conn:
        for title, payload in attacks:
            print(f"  {title}\n    kirish: {payload!r}\n    natija: {short(insecure_find_users(conn, payload))}")

    print("\nXAVFSIZ kod (parametrli so'rov):")
    with engine.connect() as conn:
        for title, payload in attacks + [("Hujum 3: DROP TABLE", PAYLOAD_DROP)]:
            print(f"  {title}\n    kirish: {payload!r}\n    natija: {short(secure_find_users(conn, payload))}")

    print("\nXavfsiz kirish (AuthService, ORM + Argon2):")
    auth = AuthService(lambda: UnitOfWork(factory))
    print(f"  to'g'ri parol            : {auth.login('aziz', DEMO_PASSWORD)}")
    print(f"  noto'g'ri parol          : {auth.login('aziz', 'boshqa-parol')}")
    print(f"  login = {PAYLOAD_ALL_ROWS!r}: {auth.login(PAYLOAD_ALL_ROWS, 'x')}")
    print(f"  login = \"admin' --\"      : {auth.login(chr(97)+'dmin'+chr(39)+' --', 'x')}")
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM users")).scalar_one()
    print(f"  users jadvali saqlangan  : {n} ta foydalanuvchi")


if __name__ == "__main__":
    main()
