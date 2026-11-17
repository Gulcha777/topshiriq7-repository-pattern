"""PostgreSQL'da haqiqiy parallel tranzaksiyalar: izolyatsiya darajalari va SQL Injection (DROP TABLE).

Ishga tushirish:  python -m app.postgres_demo        (DATABASE_URL PostgreSQL bo'lishi kerak)
Barcha jadvallar alohida `t7_demo` sxemada yaratiladi va oxirida o'chiriladi.
"""
from __future__ import annotations

import sys

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import DBAPIError, ResourceClosedError

from app.config import get_settings
from app.security.sqli_demo import PAYLOAD_DROP, insecure_find_users, secure_find_users

SCHEMA = "t7_demo"


def make_demo_engine(url: str) -> Engine:
    return create_engine(url, connect_args={"options": f"-csearch_path={SCHEMA}"})


def recreate_schema(engine: Engine) -> None:
    with engine.begin() as c:
        c.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))
        c.execute(text(f"CREATE SCHEMA {SCHEMA}"))


def drop_schema(engine: Engine) -> None:
    with engine.begin() as c:
        c.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA} CASCADE"))


def _reset_accounts(engine: Engine) -> None:
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS iso_accounts"))
        c.execute(text("CREATE TABLE iso_accounts (id int PRIMARY KEY, balance int NOT NULL)"))
        c.execute(text("INSERT INTO iso_accounts VALUES (1, 100)"))


def dirty_read(engine: Engine, level: str) -> int:
    """A tranzaksiya balansni 0 qiladi (commit yo'q). B qanday qiymat ko'radi?"""
    _reset_accounts(engine)
    with engine.connect() as a, engine.connect().execution_options(isolation_level=level) as b:
        a.execute(text("UPDATE iso_accounts SET balance = 0 WHERE id = 1"))
        seen = b.execute(text("SELECT balance FROM iso_accounts WHERE id = 1")).scalar_one()
        a.rollback()
        b.rollback()
    return seen


def non_repeatable_read(engine: Engine, level: str) -> tuple[int, int]:
    """B bir tranzaksiyada ikki marta o'qiydi, orasida A balansni 50 qilib commit qiladi."""
    _reset_accounts(engine)
    with engine.connect() as a, engine.connect().execution_options(isolation_level=level) as b:
        first = b.execute(text("SELECT balance FROM iso_accounts WHERE id = 1")).scalar_one()
        a.execute(text("UPDATE iso_accounts SET balance = 50 WHERE id = 1"))
        a.commit()
        second = b.execute(text("SELECT balance FROM iso_accounts WHERE id = 1")).scalar_one()
        b.rollback()
    return first, second


def phantom_read(engine: Engine, level: str) -> tuple[int, int]:
    """B ikki marta qatorlarni sanaydi, orasida A yangi qator qo'shib commit qiladi."""
    _reset_accounts(engine)
    with engine.connect() as a, engine.connect().execution_options(isolation_level=level) as b:
        first = b.execute(text("SELECT COUNT(*) FROM iso_accounts WHERE balance >= 0")).scalar_one()
        a.execute(text("INSERT INTO iso_accounts VALUES (2, 10)"))
        a.commit()
        second = b.execute(text("SELECT COUNT(*) FROM iso_accounts WHERE balance >= 0")).scalar_one()
        b.rollback()
    return first, second


def write_skew(engine: Engine, level: str) -> tuple[int, str | None]:
    """Ikki shifokor bir vaqtda "navbatchilikdan chiqaman" deydi. Qoida: kamida 1 ta qolsin.

    Qaytaradi: (navbatchida qolganlar soni, xatolik kodi yoki None)
    """
    with engine.begin() as c:
        c.execute(text("DROP TABLE IF EXISTS iso_doctors"))
        c.execute(text("CREATE TABLE iso_doctors (name text PRIMARY KEY, on_call boolean NOT NULL)"))
        c.execute(text("INSERT INTO iso_doctors VALUES ('alice', true), ('bob', true)"))
    error = None
    with engine.connect().execution_options(isolation_level=level) as a, \
            engine.connect().execution_options(isolation_level=level) as b:
        count_sql = text("SELECT COUNT(*) FROM iso_doctors WHERE on_call")
        assert a.execute(count_sql).scalar_one() == 2  # A: "ikkimiz ham bormiz, chiqsam bo'ladi"
        assert b.execute(count_sql).scalar_one() == 2  # B ham xuddi shunday o'ylaydi
        try:
            a.execute(text("UPDATE iso_doctors SET on_call = false WHERE name = 'alice'"))
            b.execute(text("UPDATE iso_doctors SET on_call = false WHERE name = 'bob'"))
            a.commit()
            b.commit()
        except DBAPIError as exc:
            error = getattr(exc.orig, "pgcode", None)
            b.rollback()
            a.rollback()
    with engine.connect() as c:
        left = c.execute(text("SELECT COUNT(*) FROM iso_doctors WHERE on_call")).scalar_one()
    return left, error


def sql_injection_drop(engine: Engine) -> dict:
    """PostgreSQL bir nechta buyruqni ('; DROP TABLE ...') bajaradi: zaif kod jadvalni o'chiradi."""
    out = {}
    for label, func in (("zaif", insecure_find_users), ("xavfsiz", secure_find_users)):
        with engine.begin() as c:
            c.execute(text("DROP TABLE IF EXISTS users"))
            c.execute(text("CREATE TABLE users (id int PRIMARY KEY, username text)"))
            c.execute(text("INSERT INTO users VALUES (1, 'aziz')"))
        with engine.connect() as c:
            try:
                func(c, PAYLOAD_DROP)
            except ResourceClosedError:
                pass  # oxirgi buyruq (DROP) qator qaytarmaydi
            c.commit()
        with engine.connect() as c:
            out[label] = c.execute(text("SELECT to_regclass('users') IS NOT NULL")).scalar_one()
    return out


def main() -> None:
    url = get_settings().database_url
    if not url.startswith("postgresql"):
        print("Bu demo PostgreSQL talab qiladi. .env da DATABASE_URL ni PostgreSQL ga o'zgartiring.")
        sys.exit(0)
    engine = make_demo_engine(url)
    recreate_schema(engine)
    try:
        with engine.connect() as c:
            print("Server:", c.execute(text("SHOW server_version")).scalar_one())

        print("\n1) Dirty read (A: balans 100 -> 0, commit yo'q; B nimani ko'radi?)")
        for lvl in ("READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"):
            print(f"  {lvl:<17}: B ko'rgan balans = {dirty_read(engine, lvl)}")

        print("\n2) Non-repeatable read (B ikki marta o'qiydi, orada A balansni 50 qilib commit qiladi)")
        for lvl in ("READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"):
            print(f"  {lvl:<17}: 1-o'qish, 2-o'qish = {non_repeatable_read(engine, lvl)}")

        print("\n3) Phantom read (B ikki marta sanaydi, orada A yangi qator qo'shib commit qiladi)")
        for lvl in ("READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"):
            print(f"  {lvl:<17}: 1-sanash, 2-sanash = {phantom_read(engine, lvl)}")

        print("\n4) Write skew (ikki shifokor bir vaqtda navbatchilikdan chiqadi; qoida: kamida 1 ta qolsin)")
        for lvl in ("REPEATABLE READ", "SERIALIZABLE"):
            left, err = write_skew(engine, lvl)
            print(f"  {lvl:<17}: navbatchida qolgan = {left}, xatolik kodi = {err}")

        print("\n5) SQL Injection: x'; DROP TABLE users; -- (PostgreSQL)")
        res = sql_injection_drop(engine)
        print(f"  zaif koddan keyin users jadvali bormi?    {res['zaif']}")
        print(f"  xavfsiz koddan keyin users jadvali bormi?  {res['xavfsiz']}")
    finally:
        drop_schema(engine)


if __name__ == "__main__":
    main()
