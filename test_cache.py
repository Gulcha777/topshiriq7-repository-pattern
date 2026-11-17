import time
from decimal import Decimal

import pytest
from sqlalchemy import event

from app.cache import ProductCache
from app.errors import EntityNotFoundError, InvalidInputError
from app.services.product_service import ProductService


@pytest.fixture()
def svc(uow_factory, cache, ids):
    return ProductService(uow_factory, cache)


@pytest.fixture()
def sql_log(engine):
    queries = []
    event.listen(engine, "before_cursor_execute", lambda conn, cur, stmt, *a: queries.append(stmt))
    return queries


def test_first_read_hits_db_next_reads_hit_cache(svc, ids, sql_log):
    pid = ids["products"][0]
    svc.get_product(pid)
    after_first = len(sql_log)
    assert after_first >= 1
    for _ in range(5):
        assert svc.get_product(pid)["name"] == "Noutbuk"
    assert len(sql_log) == after_first          # keyingi 5 o'qishda SQL so'rov yo'q
    assert (svc.cache_hits, svc.cache_misses) == (5, 1)


def test_cached_value_has_ttl(svc, cache, ids):
    pid = ids["products"][0]
    svc.get_product(pid)
    assert 0 < cache.ttl(pid) <= 60


def test_update_invalidates_cache_and_serves_fresh_data(svc, cache, ids):
    pid = ids["products"][0]
    svc.get_product(pid)
    svc.update_price(pid, Decimal("1234.50"))
    assert cache.get(pid) is None
    assert svc.get_product(pid)["price"] == "1234.50"


def test_missing_product_raises_and_is_not_cached(svc, cache):
    with pytest.raises(EntityNotFoundError):
        svc.get_product(777)
    assert cache.get(777) is None


def test_negative_price_rejected_and_cache_kept(svc, cache, ids):
    pid = ids["products"][0]
    svc.get_product(pid)
    with pytest.raises(InvalidInputError):
        svc.update_price(pid, Decimal("-1"))
    assert cache.get(pid) is not None


def test_cache_entry_expires(redis_client, uow_factory, ids):
    short = ProductCache(redis_client, ttl_seconds=1, prefix="exp-test")
    svc = ProductService(uow_factory, short)
    pid = ids["products"][0]
    svc.get_product(pid)
    assert short.get(pid) is not None
    time.sleep(1.3)
    assert short.get(pid) is None


def test_cache_roundtrip_json(cache):
    cache.set(5, {"id": 5, "name": "O'zbek", "price": "1.00", "stock": 2})
    assert cache.get(5) == {"id": 5, "name": "O'zbek", "price": "1.00", "stock": 2}
    cache.invalidate(5)
    assert cache.get(5) is None
