from __future__ import annotations

from typing import TYPE_CHECKING

from .transaction_base import Transaction

if TYPE_CHECKING:
    from .account import Account


class TransferTransaction(Transaction):
    def __init__(
        self,
        amount: int,
        account: Account,
        other_account_number: str,
        is_credit: bool,
        fee: int = 0,
    ) -> None:
        super().__init__(amount, account)
        self.other_account_number = other_account_number
        self.is_credit = is_credit
        self.fee = fee

    @property
    def transaction_type(self) -> str:
        return "TRANSFER IN" if self.is_credit else "TRANSFER OUT"

    @property
    def signed_amount(self) -> int:
        return self.amount if self.is_credit else -(self.amount + self.fee)
