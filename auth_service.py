"""Ro'yxatdan o'tish va kirish: parol hash'i, kiritishni tekshirish, SQL Injection'dan himoya."""
from __future__ import annotations

import re

from sqlalchemy.exc import IntegrityError

from app.errors import DuplicateUserError, InvalidInputError, WeakPasswordError
from app.models import User
from app.security.passwords import PasswordService

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")
MIN_PASSWORD_LENGTH = 8


class AuthService:
    def __init__(self, uow_factory, passwords: PasswordService | None = None) -> None:
        self._uow_factory = uow_factory
        self._passwords = passwords or PasswordService()
        # Foydalanuvchi topilmaganda ham bir xil vaqt sarflash uchun (timing hujumiga qarshi)
        self._dummy_hash = self._passwords.hash("dummy-password-for-timing")

    def register(self, username: str, password: str) -> int:
        if not USERNAME_RE.fullmatch(username):
            raise InvalidInputError("Login 3-50 ta harf, raqam yoki _ . - belgilaridan iborat bo'lsin")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(f"Parol kamida {MIN_PASSWORD_LENGTH} ta belgidan iborat bo'lsin")
        with self._uow_factory() as uow:
            if uow.users.find_by_username(username) is not None:
                raise DuplicateUserError(f"'{username}' band")
            user = uow.users.create(
                User(username=username, password_hash=self._passwords.hash(password))
            )
            try:
                uow.commit()
            except IntegrityError as exc:  # poyga holati: bir vaqtda ro'yxatdan o'tish
                raise DuplicateUserError(f"'{username}' band") from exc
            return user.id

    def login(self, username: str, password: str) -> bool:
        with self._uow_factory() as uow:
            user = uow.users.find_by_username(username)  # parametrlangan so'rov
            if user is None:
                self._passwords.verify(self._dummy_hash, password)
                return False
            ok = self._passwords.verify(user.password_hash, password)
            if ok and self._passwords.needs_rehash(user.password_hash):
                user.password_hash = self._passwords.hash(password)
                uow.users.update(user)
                uow.commit()
            return ok
