"""Vazifa 3: Redis asosidagi kesh (cache-aside)."""
from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import redis


def make_redis(url: str | None = None, allow_fake: bool = False):
    """Redis klientini qaytaradi. Ulanib bo'lmasa va allow_fake=True bo'lsa, fakeredis."""
    from app.config import get_settings

    url = url or get_settings().redis_url
    client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
    try:
        client.ping()
        return client, "redis"
    except redis.exceptions.RedisError:
        if not allow_fake:
            raise
        import fakeredis

        return fakeredis.FakeRedis(decode_responses=True), "fakeredis"


class ProductCache:
    """Mahsulot ma'lumotini Redis'da JSON ko'rinishida TTL bilan saqlaydi."""

    def __init__(self, client, ttl_seconds: int = 60, prefix: str = "product") -> None:
        self._client = client
        self._ttl = ttl_seconds
        self._prefix = prefix

    def _key(self, product_id: int) -> str:
        return f"{self._prefix}:{product_id}"

    def get(self, product_id: int) -> dict[str, Any] | None:
        raw = self._client.get(self._key(product_id))
        return json.loads(raw) if raw else None

    def set(self, product_id: int, data: dict[str, Any]) -> None:
        self._client.set(self._key(product_id), json.dumps(data, default=str), ex=self._ttl)

    def invalidate(self, product_id: int) -> None:
        self._client.delete(self._key(product_id))

    def ttl(self, product_id: int) -> int:
        return self._client.ttl(self._key(product_id))


def product_to_dict(product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "price": str(Decimal(product.price)),
        "stock": product.stock,
    }
