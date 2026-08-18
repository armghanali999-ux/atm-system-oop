from .account import Account
from exceptions.exceptions import InvalidAmountError


class SavingsAccount(Account):
    minimum_balance = 5_000

    def __init__(self, account_number, account_holder, opening_balance, pin) -> None:
        if opening_balance < self.minimum_balance:
            raise InvalidAmountError("Savings opening balance must be at least Rs. 5,000.")
        super().__init__(account_number, account_holder, opening_balance, pin)

    @property
    def account_type(self) -> str:
        return "Savings"

    def calculate_withdrawal_limit(self) -> int:
        return 50_000

    def available_funds(self) -> int:
        return max(0, self.balance - self.minimum_balance)
