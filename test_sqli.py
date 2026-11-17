"""SQL Injection: zaif kod hujumga uchraydi, xavfsiz kod uchramaydi."""
import pytest
from sqlalchemy import text

from app.security.sqli_demo import (
    PAYLOAD_ALL_ROWS,
    PAYLOAD_DROP,
    PAYLOAD_UNION_LEAK,
    insecure_find_users,
    secure_find_users,
)

pytestmark = pytest.mark.usefixtures("ids")


def test_insecure_normal_query_works(engine):
    with engine.connect() as c:
        assert [r[1] for r in insecure_find_users(c, "aziz")] == ["aziz"]


def test_insecure_code_is_vulnerable_to_or_payload(engine):
    with engine.connect() as c:
        assert len(insecure_find_users(c, PAYLOAD_ALL_ROWS)) == 3  # hamma foydalanuvchi chiqdi


def test_insecure_code_leaks_password_hashes_with_union(engine):
    with engine.connect() as c:
        leaked = [r[1] for r in insecure_find_users(c, PAYLOAD_UNION_LEAK)]
    assert len(leaked) == 3 and all(h.startswith("$argon2id$") for h in leaked)


@pytest.mark.parametrize("payload", [PAYLOAD_ALL_ROWS, PAYLOAD_UNION_LEAK, PAYLOAD_DROP, "admin' --"])
def test_secure_code_returns_nothing_for_payloads(engine, payload):
    with engine.connect() as c:
        assert secure_find_users(c, payload) == []


def test_secure_code_finds_legit_user(engine):
    with engine.connect() as c:
        assert [r[1] for r in secure_find_users(c, "dilnoza")] == ["dilnoza"]


def test_secure_code_keeps_table_after_drop_payload(engine):
    with engine.connect() as c:
        secure_find_users(c, PAYLOAD_DROP)
        assert c.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 3


def test_orm_repository_is_safe(uow_factory):
    with uow_factory() as uow:
        assert uow.users.find_by_username(PAYLOAD_ALL_ROWS) is None
        assert uow.users.find_by_username("sardor").username == "sardor"


def test_insecure_drop_payload_on_sqlite_errors_but_secure_does_not(engine):
    """SQLite bitta so'rovga ruxsat beradi; PostgreSQL esa DROP'ni bajaradi (postgres_demo.py)."""
    if engine.dialect.name != "sqlite":
        pytest.skip("SQLite xususiyati")
    with engine.connect() as c:
        with pytest.raises(Exception):
            insecure_find_users(c, PAYLOAD_DROP)


def test_insecure_drop_payload_destroys_table_on_postgresql(engine):
    """Haqiqiy PostgreSQL'da zaif kod jadvalni o'chirib yuboradi."""
    if engine.dialect.name != "postgresql":
        pytest.skip("faqat PostgreSQL uchun")
    from sqlalchemy.exc import ResourceClosedError

    # users jadvaliga tashqi kalit bog'langan (shuning uchun DROP rad etiladi), bog'lanmagan
    # accounts jadvali esa o'chib ketadi: zaif kod bo'yicha injection bajariladi.
    payload = "x'; DROP TABLE accounts; --"
    with engine.connect() as c:
        try:
            insecure_find_users(c, payload)
        except ResourceClosedError:
            pass
        c.commit()
    with engine.connect() as c:
        assert c.execute(text("SELECT to_regclass('accounts') IS NULL")).scalar_one() is True
