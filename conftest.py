"""Test muhiti.

Standart: SQLite (vaqtinchalik fayl) va fakeredis.
Haqiqiy xizmatlar bilan ham ishlatish mumkin (o'zgaruvchilar berilsa, testlar ikkala muhitda ham o'tadi):
  TEST_POSTGRES_URL=postgresql+psycopg2://shop:parol@localhost:5432/shop_db
  TEST_REDIS_URL=redis://localhost:6379/15
"""
import os
import sys
import uuid
from pathlib import Path

import fakeredis
import pytest
import redis
from argon2 import PasswordHasher
from sqlalchemy import create_engine, event, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.cache import ProductCache  # noqa: E402
from app.database import init_db, make_engine, make_session_factory  # noqa: E402
from app.security.passwords import PasswordService  # noqa: E402
from app.seed import seed  # noqa: E402
from app.unit_of_work import UnitOfWork  # noqa: E402

PG_URL = os.getenv("TEST_POSTGRES_URL")
REDIS_URL = os.getenv("TEST_REDIS_URL")

# Testlarni tezlashtirish uchun yengil Argon2 parametrlari (production'da standart parametrlar)
FAST_PASSWORDS = PasswordService(PasswordHasher(time_cost=1, memory_cost=8, parallelism=1))


@pytest.fixture(params=["sqlite"] + (["postgresql"] if PG_URL else []))
def engine(request, tmp_path):
    if request.param == "sqlite":
        eng = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
        init_db(eng)
        yield eng
        eng.dispose()
    else:
        schema = f"t7_{uuid.uuid4().hex[:10]}"
        admin = create_engine(PG_URL)
        with admin.begin() as c:
            c.execute(text(f"CREATE SCHEMA {schema}"))
        eng = make_engine(PG_URL, connect_args={"options": f"-csearch_path={schema}"})
        init_db(eng)
        yield eng
        eng.dispose()
        with admin.begin() as c:
            c.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        admin.dispose()


@pytest.fixture()
def factory(engine):
    return make_session_factory(engine)


@pytest.fixture()
def uow_factory(factory):
    return lambda: UnitOfWork(factory)


@pytest.fixture()
def ids(factory):
    return seed(factory, FAST_PASSWORDS)


@pytest.fixture()
def tx_events(engine):
    """Dvigatel darajasidagi commit/rollback hodisalarini sanaydi."""
    counts = {"commit": 0, "rollback": 0}
    event.listen(engine, "commit", lambda conn: counts.__setitem__("commit", counts["commit"] + 1))
    event.listen(engine, "rollback", lambda conn: counts.__setitem__("rollback", counts["rollback"] + 1))
    return counts


@pytest.fixture(params=["fakeredis"] + (["redis"] if REDIS_URL else []))
def redis_client(request):
    if request.param == "fakeredis":
        yield fakeredis.FakeRedis(decode_responses=True)
    else:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        client.flushdb()
        yield client
        client.flushdb()


@pytest.fixture()
def cache(redis_client):
    return ProductCache(redis_client, ttl_seconds=60, prefix=f"t-{uuid.uuid4().hex[:6]}")
