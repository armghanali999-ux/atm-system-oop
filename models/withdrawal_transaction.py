from __future__ import annotations

from typing import TYPE_CHECKING

from .transaction_base import Transaction

if TYPE_CHECKING:
    from .account import Account


class WithdrawalTransaction(Transaction):
    def __init__(self, amount: int, account: Account, fee: int = 0) -> None:
        super().__init__(amount, account)
        self.fee = fee

    @property
    def transaction_type(self) -> str:
        return "WITHDRAWAL"

    @property
    def signed_amount(self) -> int:
        return -(self.amount + self.fee)
