"""Mahsulotlarni keshlab o'qish (cache-aside) va yangilashda keshni bekor qilish."""
from __future__ import annotations

from decimal import Decimal

from app.cache import ProductCache, product_to_dict
from app.errors import EntityNotFoundError, InvalidInputError


class ProductService:
    def __init__(self, uow_factory, cache: ProductCache) -> None:
        self._uow_factory = uow_factory
        self._cache = cache
        self.cache_hits = 0
        self.cache_misses = 0

    def get_product(self, product_id: int) -> dict:
        cached = self._cache.get(product_id)
        if cached is not None:
            self.cache_hits += 1
            return cached
        self.cache_misses += 1
        with self._uow_factory() as uow:
            product = uow.products.get_by_id(product_id)
            if product is None:
                raise EntityNotFoundError(f"Mahsulot id={product_id} topilmadi")
            data = product_to_dict(product)
        self._cache.set(product_id, data)
        return data

    def update_price(self, product_id: int, new_price: Decimal) -> dict:
        if Decimal(new_price) < 0:
            raise InvalidInputError("Narx manfiy bo'lishi mumkin emas")
        with self._uow_factory() as uow:
            product = uow.products.get_by_id(product_id)
            if product is None:
                raise EntityNotFoundError(f"Mahsulot id={product_id} topilmadi")
            product.price = Decimal(new_price)
            uow.products.update(product)
            uow.commit()
            data = product_to_dict(product)
        # Bazaga commit muvaffaqiyatli bo'lgandan keyingina kesh bekor qilinadi
        self._cache.invalidate(product_id)
        return data
