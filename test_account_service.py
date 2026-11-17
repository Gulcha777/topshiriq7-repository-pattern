from decimal import Decimal

import pytest
from sqlalchemy import select

from app.errors import EntityNotFoundError, InsufficientFundsError, InvalidInputError
from app.models import Account
from app.services.account_service import AccountService


def balances(factory):
    with factory() as s:
        return [a.balance for a in s.scalars(select(Account).order_by(Account.id))]


def test_transfer_moves_money(uow_factory, factory, ids):
    a, b = ids["accounts"]
    AccountService(uow_factory).transfer(a, b, Decimal("300"))
    assert balances(factory) == [Decimal("700.00"), Decimal("800.00")]


def test_total_money_is_conserved(uow_factory, factory, ids):
    a, b = ids["accounts"]
    svc = AccountService(uow_factory)
    svc.transfer(a, b, Decimal("123.45"))
    svc.transfer(b, a, Decimal("50.10"))
    assert sum(balances(factory)) == Decimal("1500.00")


def test_failure_after_debit_rolls_back_atomically(uow_factory, factory, ids):
    a, b = ids["accounts"]

    def crash():
        raise RuntimeError("server o'chdi")

    with pytest.raises(RuntimeError):
        AccountService(uow_factory, after_debit=crash).transfer(a, b, Decimal("300"))
    assert balances(factory) == [Decimal("1000.00"), Decimal("500.00")]


def test_insufficient_funds(uow_factory, factory, ids):
    a, b = ids["accounts"]
    with pytest.raises(InsufficientFundsError):
        AccountService(uow_factory).transfer(a, b, Decimal("1000.01"))
    assert balances(factory) == [Decimal("1000.00"), Decimal("500.00")]


def test_transfer_entire_balance(uow_factory, factory, ids):
    a, b = ids["accounts"]
    AccountService(uow_factory).transfer(a, b, Decimal("1000"))
    assert balances(factory) == [Decimal("0.00"), Decimal("1500.00")]


@pytest.mark.parametrize("amount", ["0", "-5"])
def test_invalid_amount(uow_factory, ids, amount):
    a, b = ids["accounts"]
    with pytest.raises(InvalidInputError):
        AccountService(uow_factory).transfer(a, b, Decimal(amount))


def test_same_account_rejected(uow_factory, ids):
    a, _ = ids["accounts"]
    with pytest.raises(InvalidInputError):
        AccountService(uow_factory).transfer(a, a, Decimal("1"))


def test_missing_account(uow_factory, factory, ids):
    a, _ = ids["accounts"]
    with pytest.raises(EntityNotFoundError):
        AccountService(uow_factory).transfer(a, 9999, Decimal("1"))
    assert balances(factory)[0] == Decimal("1000.00")
