from .account import Account


class CurrentAccount(Account):
    overdraft_limit = 50_000

    @property
    def account_type(self) -> str:
        return "Current"

    def calculate_withdrawal_limit(self) -> int:
        return 75_000

    def available_funds(self) -> int:
        return self.balance + self.overdraft_limit

    @property
    def withdrawal_fee(self) -> int:
        return 25

    @property
    def transfer_fee(self) -> int:
        return 50
