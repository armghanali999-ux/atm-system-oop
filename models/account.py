from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING

from .status import AccountStatus
from exceptions.exceptions import (
    AccountInactiveError,
    DailyLimitExceededError,
    InsufficientBalanceError,
    InvalidAmountError,
    InvalidPINError,
)
from .deposit_transaction import DepositTransaction
from .transaction_base import Transaction
from .transfer_transaction import TransferTransaction
from .withdrawal_transaction import WithdrawalTransaction

if TYPE_CHECKING:
    from .customer import Customer


class Account(ABC):
    def __init__(self, account_number: str, account_holder: Customer, opening_balance: int, pin: str) -> None:
        if opening_balance < 0:
            raise InvalidAmountError("Opening balance cannot be negative.")
        self.account_number = account_number
        self.account_holder = account_holder
        self.__balance = opening_balance
        self.__pin = ""
        self.__status = AccountStatus.ACTIVE
        self.__transactions: list[Transaction] = []
        self.__daily_withdrawals: dict[date, int] = {}
        self.__daily_transfers: dict[date, int] = {}
        self._set_pin(pin)

    @property
    def balance(self) -> int:
        return self.__balance

    @property
    def status(self) -> AccountStatus:
        return self.__status

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        return tuple(self.__transactions)

    @property
    @abstractmethod
    def account_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def calculate_withdrawal_limit(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def available_funds(self) -> int:
        raise NotImplementedError

    @property
    def withdrawal_fee(self) -> int:
        return 50

    @property
    def transfer_fee(self) -> int:
        return 100

    @property
    def daily_withdrawal_limit(self) -> int:
        return 100_000

    @property
    def daily_transfer_limit(self) -> int:
        return 200_000

    def _ensure_active(self) -> None:
        if self.__status is not AccountStatus.ACTIVE:
            raise AccountInactiveError("Account is not active.")

    @staticmethod
    def _validate_pin_format(pin: str) -> None:
        if len(pin) != 4 or not pin.isdigit() or len(set(pin)) == 1:
            raise InvalidPINError("PIN must contain four digits and cannot repeat one digit four times.")

    def _set_pin(self, pin: str) -> None:
        self._validate_pin_format(pin)
        self.__pin = pin

    def verify_pin(self, pin: str) -> bool:
        return self.__pin == pin

    def change_pin(self, old_pin: str, new_pin: str) -> None:
        self._ensure_active()
        if not self.verify_pin(old_pin):
            raise InvalidPINError("Current PIN is incorrect.")
        if old_pin == new_pin:
            raise InvalidPINError("New PIN must be different from the current PIN.")
        self._set_pin(new_pin)

    def set_status(self, status: AccountStatus) -> None:
        self.__status = status

    def check_balance(self) -> int:
        self._ensure_active()
        return self.__balance

    @staticmethod
    def _validate_positive_amount(amount: int) -> None:
        if amount <= 0:
            raise InvalidAmountError("Amount must be positive.")

    def deposit(self, amount: int) -> DepositTransaction:
        self._ensure_active()
        self._validate_positive_amount(amount)
        self.__balance += amount
        transaction = DepositTransaction(amount, self)
        self.__transactions.append(transaction)
        return transaction

    def validate_withdrawal(self, amount: int, on_date: date | None = None) -> None:
        self._ensure_active()
        self._validate_positive_amount(amount)
        if amount < 500:
            raise InvalidAmountError("Minimum withdrawal is Rs. 500.")
        if amount > self.calculate_withdrawal_limit():
            raise InvalidAmountError(
                f"Maximum withdrawal for this account is Rs. {self.calculate_withdrawal_limit():,}."
            )
        today = on_date or date.today()
        if self.__daily_withdrawals.get(today, 0) + amount > self.daily_withdrawal_limit:
            raise DailyLimitExceededError("Daily withdrawal limit would be exceeded.")
        if amount + self.withdrawal_fee > self.available_funds():
            raise InsufficientBalanceError("Insufficient available balance.")

    def withdraw(self, amount: int, on_date: date | None = None) -> WithdrawalTransaction:
        self.validate_withdrawal(amount, on_date)
        today = on_date or date.today()
        self.__balance -= amount + self.withdrawal_fee
        self.__daily_withdrawals[today] = self.__daily_withdrawals.get(today, 0) + amount
        transaction = WithdrawalTransaction(amount, self, self.withdrawal_fee)
        self.__transactions.append(transaction)
        return transaction

    def validate_transfer(self, amount: int, on_date: date | None = None) -> None:
        self._ensure_active()
        self._validate_positive_amount(amount)
        today = on_date or date.today()
        if self.__daily_transfers.get(today, 0) + amount > self.daily_transfer_limit:
            raise DailyLimitExceededError("Daily transfer limit would be exceeded.")
        if amount + self.transfer_fee > self.available_funds():
            raise InsufficientBalanceError("Insufficient available balance.")

    def debit_transfer(self, amount: int, receiver_number: str, on_date: date | None = None) -> TransferTransaction:
        self.validate_transfer(amount, on_date)
        today = on_date or date.today()
        self.__balance -= amount + self.transfer_fee
        self.__daily_transfers[today] = self.__daily_transfers.get(today, 0) + amount
        transaction = TransferTransaction(amount, self, receiver_number, False, self.transfer_fee)
        self.__transactions.append(transaction)
        return transaction

    def credit_transfer(self, amount: int, sender_number: str) -> TransferTransaction:
        self._ensure_active()
        self.__balance += amount
        transaction = TransferTransaction(amount, self, sender_number, True)
        self.__transactions.append(transaction)
        return transaction

    def mini_statement(self, count: int = 5) -> tuple[Transaction, ...]:
        self._ensure_active()
        return tuple(self.__transactions[-count:])
