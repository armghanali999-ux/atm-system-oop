from .transaction_base import Transaction


class DepositTransaction(Transaction):
    @property
    def transaction_type(self) -> str:
        return "DEPOSIT"

    @property
    def signed_amount(self) -> int:
        return self.amount
