"""Vazifa 1: Repository pattern namoyishi (ORM va xotiradagi implementatsiya bir xil interfeysda).

Ishga tushirish:  python -m app.demo_repository
"""
from __future__ import annotations

from decimal import Decimal

from app.demo_utils import temp_database
from app.models import Product
from app.repository.base import IRepository
from app.repository.memory_repo import InMemoryRepository
from app.repository.sqlalchemy_repo import SqlAlchemyRepository


def crud_scenario(repo: IRepository[Product, int]) -> None:
    """Faqat IRepository interfeysiga tayanadi: qaysi implementatsiya ekanini bilmaydi."""
    p = repo.create(Product(name="Noutbuk", price=Decimal("7500000"), stock=5))
    repo.create(Product(name="Sichqoncha", price=Decimal("120000"), stock=20))
    print(f"  create      : id={p.id}, name={p.name}")
    print(f"  get_by_id   : {repo.get_by_id(p.id).name}")
    print(f"  get_all     : {[x.name for x in repo.get_all()]}")
    p.stock = 4
    print(f"  update      : stock={repo.update(p).stock}")
    print(f"  delete      : {repo.delete(p.id)} (qayta: {repo.delete(p.id)})")
    print(f"  get_by_id   : {repo.get_by_id(p.id)}")


def main() -> None:
    print("1) InMemoryRepository")
    crud_scenario(InMemoryRepository[Product]())

    print("2) SqlAlchemyRepository (ORM)")
    _, factory = temp_database()
    with factory() as session:
        crud_scenario(SqlAlchemyRepository(Product, session))
        session.commit()


if __name__ == "__main__":
    main()
