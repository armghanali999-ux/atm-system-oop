from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from .status import CardStatus

if TYPE_CHECKING:
    from .customer import Customer


class Card:
    def __init__(self, card_number: str, customer: Customer, account_numbers: Iterable[str]) -> None:
        self.card_number = card_number
        self.customer = customer
        self.account_numbers = tuple(account_numbers)
        self.__status = CardStatus.ACTIVE
        self.__failed_attempts = 0

    @property
    def status(self) -> CardStatus:
        return self.__status

    @property
    def failed_attempts(self) -> int:
        return self.__failed_attempts

    def record_failed_attempt(self) -> None:
        self.__failed_attempts += 1
        if self.__failed_attempts >= 3:
            self.__status = CardStatus.BLOCKED

    def reset_attempts(self) -> None:
        self.__failed_attempts = 0

    def block(self) -> None:
        self.__status = CardStatus.BLOCKED
