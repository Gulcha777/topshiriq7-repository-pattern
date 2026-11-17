"""IRepository shartnomasi: har ikkala implementatsiya bir xil xulq-atvorni ko'rsatishi kerak."""
from decimal import Decimal

import pytest

from app.errors import EntityNotFoundError
from app.models import Product
from app.repository.base import IRepository
from app.repository.memory_repo import InMemoryRepository
from app.repository.sqlalchemy_repo import SqlAlchemyRepository


@pytest.fixture(params=["memory", "sqlalchemy"])
def repo(request, factory):
    if request.param == "memory":
        yield InMemoryRepository()
    else:
        with factory() as session:
            yield SqlAlchemyRepository(Product, session)


def product(name="A", stock=1):
    return Product(name=name, price=Decimal("10.00"), stock=stock)


def test_is_irepository(repo):
    assert isinstance(repo, IRepository)


def test_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IRepository()  # type: ignore[abstract]


def test_create_assigns_id(repo):
    p = repo.create(product())
    assert p.id is not None


def test_ids_are_unique(repo):
    a, b = repo.create(product("A")), repo.create(product("B"))
    assert a.id != b.id


def test_get_by_id_found(repo):
    p = repo.create(product("Topilgan"))
    assert repo.get_by_id(p.id).name == "Topilgan"


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id(9999) is None


def test_get_all_empty(repo):
    assert repo.get_all() == []


def test_get_all_ordered_by_id(repo):
    created = [repo.create(product(n)) for n in "CAB"]
    assert [p.id for p in repo.get_all()] == sorted(p.id for p in created)
    assert [p.name for p in repo.get_all()] == ["C", "A", "B"]


def test_update_changes_data(repo):
    p = repo.create(product(stock=1))
    p.stock = 7
    repo.update(p)
    assert repo.get_by_id(p.id).stock == 7


def test_update_missing_raises(repo):
    ghost = product()
    ghost.id = 12345
    with pytest.raises(EntityNotFoundError):
        repo.update(ghost)


def test_update_without_id_raises(repo):
    with pytest.raises(EntityNotFoundError):
        repo.update(product())


def test_delete_existing(repo):
    p = repo.create(product())
    assert repo.delete(p.id) is True
    assert repo.get_by_id(p.id) is None


def test_delete_missing_returns_false(repo):
    assert repo.delete(424242) is False


def test_delete_is_idempotent(repo):
    p = repo.create(product())
    assert repo.delete(p.id) is True
    assert repo.delete(p.id) is False
