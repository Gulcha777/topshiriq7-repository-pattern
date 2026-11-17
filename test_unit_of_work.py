from decimal import Decimal

import pytest

from app.models import Product


def new_product():
    return Product(name="P", price=Decimal("1"), stock=1)


def test_commit_persists(uow_factory):
    with uow_factory() as uow:
        pid = uow.products.create(new_product()).id
        uow.commit()
    with uow_factory() as uow:
        assert uow.products.get_by_id(pid) is not None


def test_without_commit_nothing_is_saved(uow_factory):
    with uow_factory() as uow:
        pid = uow.products.create(new_product()).id
    with uow_factory() as uow:
        assert uow.products.get_by_id(pid) is None


def test_exception_triggers_rollback_and_propagates(uow_factory, tx_events):
    with pytest.raises(RuntimeError):
        with uow_factory() as uow:
            uow.products.create(new_product())
            raise RuntimeError("xato")
    assert tx_events["commit"] == 0 and tx_events["rollback"] >= 1
    with uow_factory() as uow:
        assert uow.products.get_all() == []


def test_explicit_rollback(uow_factory):
    with uow_factory() as uow:
        uow.products.create(new_product())
        uow.rollback()
        uow.commit()
    with uow_factory() as uow:
        assert uow.products.get_all() == []


def test_repository_does_not_commit(uow_factory, tx_events):
    with uow_factory() as uow:
        uow.products.create(new_product())
    assert tx_events["commit"] == 0
