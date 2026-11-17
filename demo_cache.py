"""Vazifa 3: Redis kesh (cache-aside) namoyishi.

Ishga tushirish:  python -m app.demo_cache
REDIS_URL dagi Redis ishlamasa, xotiradagi fakeredis ishlatiladi (bu haqda xabar beriladi).
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import event

from app.cache import ProductCache, make_redis
from app.demo_utils import temp_database
from app.seed import seed
from app.services.product_service import ProductService
from app.unit_of_work import UnitOfWork


def main() -> None:
    client, kind = make_redis(allow_fake=True)
    print(f"Kesh serveri: {kind}")

    engine, factory = temp_database()
    ids = seed(factory)
    queries = []
    event.listen(engine, "before_cursor_execute", lambda *a: queries.append(a[2]))

    cache = ProductCache(client, ttl_seconds=60, prefix="demo-product")
    service = ProductService(lambda: UnitOfWork(factory), cache)
    pid = ids["products"][0]
    cache.invalidate(pid)

    def step(title: str, func) -> None:
        before = len(queries)
        result = func()
        print(f"  {title:<34}: SQL so'rovlar={len(queries) - before}, natija={result}")

    print("Cache-aside:")
    step("1-o'qish (keshda yo'q)", lambda: service.get_product(pid)["name"])
    step("2-o'qish (keshdan)", lambda: service.get_product(pid)["name"])
    step("3-o'qish (keshdan)", lambda: service.get_product(pid)["name"])
    print(f"  keshda yashash vaqti (TTL)       : {cache.ttl(pid)} soniya")
    print(f"  hit/miss                          : {service.cache_hits}/{service.cache_misses}")
    step("Narxni yangilash (kesh bekor)", lambda: service.update_price(pid, Decimal("7000000"))["price"])
    step("Yangilangandan keyingi o'qish", lambda: service.get_product(pid)["price"])
    step("Yana o'qish (keshdan)", lambda: service.get_product(pid)["price"])
    print(f"  hit/miss                          : {service.cache_hits}/{service.cache_misses}")
    cache.invalidate(pid)


if __name__ == "__main__":
    main()
