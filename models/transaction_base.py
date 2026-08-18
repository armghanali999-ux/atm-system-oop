from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from itertools import count
from typing import TYPE_CHECKING

from .status import TransactionStatus

if TYPE_CHECKING:
    from .account import Account


_transaction_sequence = count(1001)


class Transaction(ABC):
    def __init__(
        self,
        amount: int,
        account: Account,
        status: TransactionStatus = TransactionStatus.SUCCESS,
        timestamp: datetime | None = None,
    ) -> None:
        self.transaction_id = f"TXN-{next(_transaction_sequence)}"
        self.amount = amount
        self.timestamp = timestamp or datetime.now()
        self.account = account
        self.status = status

    @property
    @abstractmethod
    def transaction_type(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def signed_amount(self) -> int:
        raise NotImplementedError

    def statement_line(self) -> str:
        sign = "+" if self.signed_amount >= 0 else "-"
        return (
            f"{self.timestamp:%d-%b %H:%M}  {self.transaction_type:<12} "
            f"{sign}Rs. {abs(self.signed_amount):,}  {self.transaction_id}"
        )
