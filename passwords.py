"""Parollarni Argon2 bilan hash qilish (xavfsiz saqlash)."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


class PasswordService:
    """Argon2id: har bir hash uchun tasodifiy tuz (salt) avtomatik qo'shiladi."""

    def __init__(self, hasher: PasswordHasher | None = None) -> None:
        self._hasher = hasher or PasswordHasher()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        return self._hasher.check_needs_rehash(password_hash)
