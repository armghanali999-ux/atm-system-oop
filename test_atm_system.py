import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from io import StringIO

from exceptions.exceptions import (
    AccountInactiveError,
    CardBlockedError,
    DailyLimitExceededError,
    InsufficientBalanceError,
    InvalidAccountError,
    InvalidAmountError,
    InvalidPINError,
    UnsupportedDenominationError,
)
from models import (
    AccountStatus,
    Card,
    CurrentAccount,
    Customer,
    SavingsAccount,
    TransactionStatus,
)
from services import ATM, Bank
from main import show_statement


class ATMSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bank = Bank("Test Bank")
        self.alice = Customer("C1", "Alice", "alice@example.com")
        self.bob = Customer("C2", "Bob", "bob@example.com")
        self.bank.add_customer(self.alice)
        self.bank.add_customer(self.bob)
        self.savings = SavingsAccount("S100", self.alice, 100_000, "2580")
        self.current = CurrentAccount("C100", self.alice, 10_000, "2580")
        self.receiver = SavingsAccount("S200", self.bob, 20_000, "7391")
        for account in (self.savings, self.current, self.receiver):
            self.bank.add_account(account)
        self.card = Card("CARD1", self.alice, ("S100", "C100"))
        self.bank.issue_card(self.card)
        self.atm = ATM(self.bank, {500: 10, 1000: 20, 5000: 10})

    def test_authentication_and_three_attempt_block(self) -> None:
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("CARD1", "0000", "S100")
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("CARD1", "0000", "S100")
        with self.assertRaises(CardBlockedError):
            self.atm.authenticate("CARD1", "0000", "S100")
        with self.assertRaises(CardBlockedError):
            self.atm.authenticate("CARD1", "2580", "S100")

    def test_successful_login_resets_failed_attempts(self) -> None:
        with self.assertRaises(InvalidPINError):
            self.atm.authenticate("CARD1", "1234", "S100")
        self.atm.authenticate("CARD1", "2580", "S100")
        self.assertEqual(self.card.failed_attempts, 0)

    def test_deposit_creates_transaction(self) -> None:
        session = self.atm.authenticate("CARD1", "2580", "S100")
        transaction = self.atm.deposit(session, 20_000)
        self.assertEqual(self.savings.balance, 120_000)
        self.assertEqual(transaction.signed_amount, 20_000)
        self.assertTrue(transaction.transaction_id.startswith("TXN-"))

    def test_invalid_deposit_is_rejected(self) -> None:
        with self.assertRaises(InvalidAmountError):
            self.savings.deposit(0)

    def test_savings_preserves_minimum_balance_and_fee(self) -> None:
        low_balance_savings = SavingsAccount("S300", self.alice, 55_000, "2580")
        with self.assertRaises(InsufficientBalanceError):
            low_balance_savings.withdraw(50_000)

    def test_current_account_uses_overdraft_polymorphically(self) -> None:
        self.assertEqual(self.current.available_funds(), 60_000)
        transaction = self.current.withdraw(20_000)
        self.assertEqual(self.current.balance, -10_025)
        self.assertEqual(transaction.fee, 25)

    def test_withdrawal_dispenses_notes_and_updates_atm_cash(self) -> None:
        session = self.atm.authenticate("CARD1", "2580", "S100")
        before = self.atm.total_cash
        _, notes = self.atm.withdraw(session, 7_500)
        self.assertEqual(sum(note * count for note, count in notes.items()), 7_500)
        self.assertEqual(self.atm.total_cash, before - 7_500)

    def test_unsupported_denomination_does_not_debit_account(self) -> None:
        odd_atm = ATM(self.bank, {1000: 1})
        session = odd_atm.authenticate("CARD1", "2580", "S100")
        before = self.savings.balance
        with self.assertRaises(UnsupportedDenominationError):
            odd_atm.withdraw(session, 500)
        self.assertEqual(self.savings.balance, before)

    def test_daily_withdrawal_limit_resets_on_new_day(self) -> None:
        first_day = date(2026, 8, 17)
        second_day = first_day + timedelta(days=1)
        self.current.deposit(200_000)
        self.current.withdraw(60_000, first_day)
        with self.assertRaises(DailyLimitExceededError):
            self.current.withdraw(50_000, first_day)
        self.current.withdraw(50_000, second_day)

    def test_transfer_creates_debit_and_credit_records(self) -> None:
        sender_before = self.savings.balance
        receiver_before = self.receiver.balance
        debit, credit = self.bank.transfer("S100", "S200", 20_000)
        self.assertEqual(self.savings.balance, sender_before - 20_100)
        self.assertEqual(self.receiver.balance, receiver_before + 20_000)
        self.assertEqual(debit.signed_amount, -20_100)
        self.assertEqual(credit.signed_amount, 20_000)

    def test_same_account_transfer_is_rejected(self) -> None:
        with self.assertRaises(InvalidAccountError):
            self.bank.transfer("S100", "S100", 1_000)

    def test_inactive_account_cannot_transact(self) -> None:
        self.savings.set_status(AccountStatus.BLOCKED)
        with self.assertRaises(AccountInactiveError):
            self.savings.deposit(1_000)

    def test_pin_security_and_change(self) -> None:
        with self.assertRaises(InvalidPINError):
            self.savings.change_pin("2580", "1111")
        self.savings.change_pin("2580", "4826")
        self.assertTrue(self.savings.verify_pin("4826"))

    def test_mini_statement_returns_last_five(self) -> None:
        for _ in range(7):
            self.savings.deposit(1_000)
        statement = self.savings.mini_statement()
        self.assertEqual(len(statement), 5)
        self.assertEqual(statement, self.savings.transactions[-5:])

    def test_customer_can_use_multiple_cards(self) -> None:
        second_card = Card("CARD2", self.alice, ("S100",))
        self.bank.issue_card(second_card)
        session = self.atm.authenticate("CARD2", "2580", "S100")
        self.assertEqual(len(self.alice.cards), 2)
        self.assertIs(session.card, second_card)

    def test_daily_transfer_limit_is_enforced(self) -> None:
        self.savings.deposit(250_000)
        self.bank.transfer("S100", "S200", 150_000)
        with self.assertRaises(DailyLimitExceededError):
            self.bank.transfer("S100", "S200", 60_000)

    def test_inactive_receiver_rejects_transfer_without_debit(self) -> None:
        self.receiver.set_status(AccountStatus.BLOCKED)
        original_balance = self.savings.balance
        with self.assertRaises(AccountInactiveError):
            self.bank.transfer("S100", "S200", 10_000)
        self.assertEqual(self.savings.balance, original_balance)

    def test_transaction_contains_required_metadata(self) -> None:
        transaction = self.savings.deposit(1_000)
        self.assertIsNotNone(transaction.timestamp)
        self.assertIs(transaction.account, self.savings)
        self.assertIs(transaction.status, TransactionStatus.SUCCESS)

    def test_balance_and_status_are_read_only_properties(self) -> None:
        with self.assertRaises(AttributeError):
            self.savings.balance = -50_000
        with self.assertRaises(AttributeError):
            self.card.status = "BLOCKED"

    def test_empty_mini_statement_displays_zero_row(self) -> None:
        session = self.atm.authenticate("CARD1", "2580", "S100")
        output = StringIO()
        with redirect_stdout(output):
            show_statement(session)
        statement = output.getvalue()
        self.assertIn("Date", statement)
        self.assertIn("Type", statement)
        self.assertIn("Amount", statement)
        self.assertIn("No transactions", statement)
        self.assertIn("Rs. 0", statement)

    def test_register_customer_first_account_and_card(self) -> None:
        customer = Customer("C3", "New Customer", "new@example.com")
        account = SavingsAccount("S300", customer, 10_000, "4826")
        card = Card("CARD3", customer, ("S300",))
        self.bank.register_customer_account(customer, account, card)

        self.assertIs(self.bank.get_customer("C3"), customer)
        self.assertIs(self.bank.get_account("S300"), account)
        session = self.atm.authenticate("CARD3", "4826", "S300")
        self.assertIs(session.account, account)

    def test_savings_account_requires_minimum_opening_balance(self) -> None:
        with self.assertRaises(InvalidAmountError):
            SavingsAccount("S400", self.alice, 4_999, "4826")

    def test_customer_ids_are_generated_sequentially(self) -> None:
        self.assertEqual(self.bank.generate_customer_id(), "CUST-001")
        self.bank.add_customer(Customer("CUST-001", "First", "first@example.com"))
        self.assertEqual(self.bank.generate_customer_id(), "CUST-002")

    def test_account_numbers_use_eight_digit_type_sequences(self) -> None:
        savings_number = self.bank.generate_account_number("Savings")
        current_number = self.bank.generate_account_number("Current")
        self.assertEqual(len(savings_number), 8)
        self.assertEqual(len(current_number), 8)
        self.assertTrue(savings_number.startswith("1"))
        self.assertTrue(current_number.startswith("2"))
        self.assertTrue(savings_number.isdigit())
        self.assertTrue(current_number.isdigit())


if __name__ == "__main__":
    unittest.main()
