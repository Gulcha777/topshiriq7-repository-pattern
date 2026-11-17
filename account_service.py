"""Bank o'tkazmasi: ACID (atomiklik) namoyishi."""
from __future__ import annotations

from decimal import Decimal
from typing import Callable

from app.errors import EntityNotFoundError, InsufficientFundsError, InvalidInputError


class AccountService:
    def __init__(self, uow_factory, after_debit: Callable[[], None] | None = None) -> None:
        self._uow_factory = uow_factory
        # Sinov uchun: yechib olingandan keyin, qo'shilishidan oldin xatolik kiritish nuqtasi
        self._after_debit = after_debit

    def transfer(self, from_id: int, to_id: int, amount: Decimal) -> None:
        amount = Decimal(amount)
        if amount <= 0:
            raise InvalidInputError("Summa musbat bo'lishi kerak")
        if from_id == to_id:
            raise InvalidInputError("Hisoblar har xil bo'lishi kerak")
        with self._uow_factory() as uow:
            # Bir xil tartibda qulflash (kichik id birinchi): deadlock xavfini kamaytiradi
            first, second = sorted((from_id, to_id))
            accounts = {i: uow.accounts.get_by_id_for_update(i) for i in (first, second)}
            src, dst = accounts[from_id], accounts[to_id]
            if src is None or dst is None:
                raise EntityNotFoundError("Hisob topilmadi")
            if src.balance < amount:
                raise InsufficientFundsError(f"Mablag' yetarli emas: {src.balance} < {amount}")
            src.balance -= amount
            uow.accounts.update(src)
            if self._after_debit is not None:
                self._after_debit()
            dst.balance += amount
            uow.accounts.update(dst)
            uow.commit()
