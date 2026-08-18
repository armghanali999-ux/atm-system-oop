from models.card import Card
from models.current_account import CurrentAccount
from models.customer import Customer
from models.savings_account import SavingsAccount
from services.atm import ATM
from services.bank import Bank


def build_demo_atm() -> ATM:
    bank = Bank("OOP Bank")
    ali = Customer("CUST-001", "Armaghan Ali", "ali@example.com")
    sara = Customer("CUST-002", "Sara Ahmed", "+92-300-1234567")
    bank.add_customer(ali)
    bank.add_customer(sara)

    accounts = (
        SavingsAccount("10002345", ali, 100_000, "2580"),
        CurrentAccount("20002345", ali, 40_000, "2580"),
        SavingsAccount("10006789", sara, 25_000, "7391"),
    )
    for account in accounts:
        bank.add_account(account)

    bank.issue_card(Card("4242424242424242", ali, ("10002345", "20002345")))
    bank.issue_card(Card("4000000000000002", ali, ("10002345",)))
    bank.issue_card(Card("5555555555554444", sara, ("10006789",)))
    return ATM(bank, {500: 20, 1000: 30, 5000: 10})
