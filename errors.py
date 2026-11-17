"""Domen xatoliklari."""


class DomainError(Exception):
    """Barcha biznes xatoliklarning asosiy sinfi."""


class EntityNotFoundError(DomainError):
    pass


class InsufficientStockError(DomainError):
    pass


class InsufficientFundsError(DomainError):
    pass


class PaymentError(DomainError):
    pass


class DuplicateUserError(DomainError):
    pass


class WeakPasswordError(DomainError):
    pass


class InvalidInputError(DomainError):
    pass
