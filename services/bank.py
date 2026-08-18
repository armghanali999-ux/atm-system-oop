from exceptions.exceptions import InvalidAccountError, InvalidCustomerError
from models.account import Account
from models.card import Card
from models.customer import Customer
from models.transaction_base import Transaction


class Bank:
    def __init__(self, name: str) -> None:
        self.name = name
        self.__customers: dict[str, Customer] = {}
        self.__accounts: dict[str, Account] = {}
        self.__cards: dict[str, Card] = {}

    def add_customer(self, customer: Customer) -> None:
        if customer.customer_id in self.__customers:
            raise InvalidCustomerError("Customer ID already exists.")
        self.__customers[customer.customer_id] = customer

    def register_customer_account(self, customer: Customer, account: Account, card: Card) -> None:
        """Register a new customer, first account, and first card as one operation."""
        if customer.customer_id in self.__customers:
            raise InvalidCustomerError("Customer ID already exists.")
        if account.account_number in self.__accounts:
            raise InvalidAccountError("Account number already exists.")
        if card.card_number in self.__cards:
            raise InvalidAccountError("Card number already exists.")
        if account.account_holder is not customer or card.customer is not customer:
            raise InvalidCustomerError("Account and card must belong to the new customer.")
        if card.account_numbers != (account.account_number,):
            raise InvalidAccountError("First card must link to the customer's first account.")

        self.__customers[customer.customer_id] = customer
        self.__accounts[account.account_number] = account
        customer.add_account(account)
        self.__cards[card.card_number] = card
        customer.add_card(card)

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self.__customers[customer_id]
        except KeyError as exc:
            raise InvalidCustomerError("Customer does not exist.") from exc

    def generate_customer_id(self) -> str:
        numbers = [
            int(customer_id[5:])
            for customer_id in self.__customers
            if customer_id.startswith("CUST-") and customer_id[5:].isdigit()
        ]
        return f"CUST-{max(numbers, default=0) + 1:03d}"

    def generate_account_number(self, account_type: str) -> str:
        prefixes = {"Savings": "1", "Current": "2"}
        if account_type not in prefixes:
            raise InvalidAccountError("Unsupported account type.")
        prefix = prefixes[account_type]
        numbers = [
            int(account_number)
            for account_number in self.__accounts
            if len(account_number) == 8
            and account_number.isdigit()
            and account_number.startswith(prefix)
        ]
        first_number = int(prefix + "0000001")
        next_number = max(numbers, default=first_number - 1) + 1
        if next_number > int(prefix + "9999999"):
            raise InvalidAccountError(f"No {account_type} account numbers are available.")
        return f"{next_number:08d}"

    def add_account(self, account: Account) -> None:
        if account.account_number in self.__accounts:
            raise InvalidAccountError("Account number already exists.")
        self.__accounts[account.account_number] = account
        account.account_holder.add_account(account)

    def issue_card(self, card: Card) -> None:
        if card.card_number in self.__cards:
            raise InvalidAccountError("Card number already exists.")
        if not card.account_numbers:
            raise InvalidAccountError("A card must be linked to at least one account.")
        for account_number in card.account_numbers:
            account = self.get_account(account_number)
            if account.account_holder is not card.customer:
                raise InvalidAccountError("Card cannot link another customer's account.")
        self.__cards[card.card_number] = card
        card.customer.add_card(card)

    def get_account(self, account_number: str) -> Account:
        try:
            return self.__accounts[account_number]
        except KeyError as exc:
            raise InvalidAccountError("Account does not exist.") from exc

    def get_card(self, card_number: str) -> Card:
        try:
            return self.__cards[card_number]
        except KeyError as exc:
            raise InvalidAccountError("Card does not exist.") from exc

    def transfer(self, sender_number: str, receiver_number: str, amount: int) -> tuple[Transaction, Transaction]:
        if sender_number == receiver_number:
            raise InvalidAccountError("Sender and receiver accounts must be different.")
        sender = self.get_account(sender_number)
        receiver = self.get_account(receiver_number)
        sender.validate_transfer(amount)
        receiver._ensure_active()
        debit = sender.debit_transfer(amount, receiver_number)
        credit = receiver.credit_transfer(amount, sender_number)
        return debit, credit
