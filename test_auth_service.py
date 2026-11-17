import pytest
from argon2 import PasswordHasher
from sqlalchemy import select, text

from app.errors import DuplicateUserError, InvalidInputError, WeakPasswordError
from app.models import User
from app.security.passwords import PasswordService
from app.services.auth_service import AuthService
from tests.conftest import FAST_PASSWORDS


@pytest.fixture()
def auth(uow_factory):
    return AuthService(uow_factory, FAST_PASSWORDS)


def stored_hash(factory, username):
    with factory() as s:
        return s.scalars(select(User).where(User.username == username)).one().password_hash


def test_password_is_hashed_not_plain(auth, factory):
    auth.register("gulruh", "SirliParol123")
    h = stored_hash(factory, "gulruh")
    assert h != "SirliParol123" and "SirliParol123" not in h
    assert h.startswith("$argon2id$")


def test_plain_password_not_found_anywhere_in_db(auth, factory, engine):
    auth.register("gulruh", "SirliParol123")
    with engine.connect() as c:
        rows = c.execute(text("SELECT username, password_hash FROM users")).fetchall()
    assert all("SirliParol123" not in str(v) for r in rows for v in r)


def test_same_password_gives_different_hashes(auth, factory):
    auth.register("user_a", "BirXilParol1")
    auth.register("user_b", "BirXilParol1")
    assert stored_hash(factory, "user_a") != stored_hash(factory, "user_b")  # tasodifiy tuz


def test_login_success_and_failure(auth):
    auth.register("gulruh", "SirliParol123")
    assert auth.login("gulruh", "SirliParol123") is True
    assert auth.login("gulruh", "boshqaParol999") is False


def test_login_unknown_user(auth):
    assert auth.login("yoq_odam", "SirliParol123") is False


@pytest.mark.parametrize("payload", ["' OR '1'='1", "admin' --", "x'; DROP TABLE users; --", "' UNION SELECT 1,2 --"])
def test_sql_injection_in_login_fails(auth, factory, payload):
    auth.register("gulruh", "SirliParol123")
    assert auth.login(payload, "x") is False
    assert auth.login(payload, payload) is False
    assert stored_hash(factory, "gulruh")  # jadval saqlangan


def test_weak_password_rejected(auth):
    with pytest.raises(WeakPasswordError):
        auth.register("gulruh", "qisqa")


@pytest.mark.parametrize("name", ["", "ab", "has space", "o'rmon", "a" * 51, "x;--", "a'b"])
def test_invalid_username_rejected(auth, name):
    with pytest.raises(InvalidInputError):
        auth.register(name, "YaxshiParol123")


def test_duplicate_username(auth):
    auth.register("gulruh", "SirliParol123")
    with pytest.raises(DuplicateUserError):
        auth.register("gulruh", "BoshqaParol123")


def test_register_returns_id(auth):
    assert isinstance(auth.register("gulruh", "SirliParol123"), int)


def test_rehash_on_login_when_parameters_are_outdated(uow_factory, factory):
    weak = PasswordService(PasswordHasher(time_cost=1, memory_cost=8, parallelism=1))
    AuthService(uow_factory, weak).register("gulruh", "SirliParol123")
    old = stored_hash(factory, "gulruh")
    stronger = PasswordService(PasswordHasher(time_cost=2, memory_cost=16, parallelism=1))
    assert AuthService(uow_factory, stronger).login("gulruh", "SirliParol123") is True
    new = stored_hash(factory, "gulruh")
    assert new != old and stronger.verify(new, "SirliParol123")


def test_password_service_rejects_garbage_hash():
    assert FAST_PASSWORDS.verify("bu-hash-emas", "x") is False
