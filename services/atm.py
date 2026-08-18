from models.status import CardStatus
from exceptions.exceptions import (
    CardBlockedError,
    InsufficientATMFundsError,
    InvalidAccountError,
    InvalidAmountError,
    InvalidPINError,
    UnsupportedDenominationError,
)
from models.deposit_transaction import DepositTransaction
from models.session import Session
from models.transaction_base import Transaction
from models.withdrawal_transaction import WithdrawalTransaction
from .bank import Bank


class ATM:
    def __init__(self, bank: Bank, cash_inventory: dict[int, int]) -> None:
        if any(denomination <= 0 or notes < 0 for denomination, notes in cash_inventory.items()):
            raise InvalidAmountError("ATM cash inventory is invalid.")
        self.bank = bank
        self.__cash_inventory = dict(cash_inventory)

    @property
    def cash_inventory(self) -> dict[int, int]:
        return dict(self.__cash_inventory)

    @property
    def total_cash(self) -> int:
        return sum(value * count for value, count in self.__cash_inventory.items())

    def authenticate(self, card_number: str, pin: str, account_number: str) -> Session:
        card = self.bank.get_card(card_number)
        if card.status is CardStatus.BLOCKED:
            raise CardBlockedError("Card is blocked. Contact the bank.")
        if account_number not in card.account_numbers:
            raise InvalidAccountError("Account is not linked to this card.")
        account = self.bank.get_account(account_number)
        account._ensure_active()
        if not account.verify_pin(pin):
            card.record_failed_attempt()
            if card.status is CardStatus.BLOCKED:
                raise CardBlockedError("Three incorrect PIN attempts. Card is now blocked.")
            raise InvalidPINError(f"Incorrect PIN. {3 - card.failed_attempts} attempt(s) remaining.")
        card.reset_attempts()
        return Session(card, account)

    def _find_note_combination(self, amount: int) -> dict[int, int] | None:
        denominations = sorted(self.__cash_inventory, reverse=True)

        def search(index: int, remaining: int) -> dict[int, int] | None:
            if remaining == 0:
                return {}
            if index == len(denominations):
                return None
            denomination = denominations[index]
            maximum = min(self.__cash_inventory[denomination], remaining // denomination)
            for quantity in range(maximum, -1, -1):
                result = search(index + 1, remaining - quantity * denomination)
                if result is not None:
                    if quantity:
                        result[denomination] = quantity
                    return result
            return None

        return search(0, amount)

    def withdraw(self, session: Session, amount: int) -> tuple[WithdrawalTransaction, dict[int, int]]:
        session.account.validate_withdrawal(amount)
        if amount > self.total_cash:
            raise InsufficientATMFundsError("ATM has insufficient cash. Please try another amount.")
        notes = self._find_note_combination(amount)
        if notes is None:
            raise UnsupportedDenominationError("Requested amount cannot be dispensed with available denominations.")
        transaction = session.account.withdraw(amount)
        for denomination, quantity in notes.items():
            self.__cash_inventory[denomination] -= quantity
        return transaction, notes

    def deposit(self, session: Session, amount: int) -> DepositTransaction:
        return session.account.deposit(amount)

    def transfer(self, session: Session, receiver_number: str, amount: int) -> tuple[Transaction, Transaction]:
        return self.bank.transfer(session.account.account_number, receiver_number, amount)
