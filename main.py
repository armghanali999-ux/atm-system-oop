from exceptions.exceptions import ATMError
from models import Card, CurrentAccount, Customer, SavingsAccount, Session
from services import ATM, Bank


def build_demo_atm() -> ATM:
    bank = Bank("OOP Bank")
    ali = Customer("CUST-001", "Armaghan Ali", "ali@example.com")
    sara = Customer("CUST-002", "Sara Ahmed", "+92-300-1234567")
    bank.add_customer(ali)
    bank.add_customer(sara)

    savings = SavingsAccount("10002345", ali, 100_000, "2580")
    current = CurrentAccount("20002345", ali, 40_000, "2580")
    receiver = SavingsAccount("10006789", sara, 25_000, "7391")
    for account in (savings, current, receiver):
        bank.add_account(account)

    bank.issue_card(Card("4242424242424242", ali, ("10002345", "20002345")))
    bank.issue_card(Card("4000000000000002", ali, ("10002345",)))
    bank.issue_card(Card("5555555555554444", sara, ("10006789",)))
    return ATM(bank, {500: 20, 1000: 30, 5000: 10})


def read_positive_integer(prompt: str) -> int:
    value = input(prompt).strip().replace(",", "")
    if not value.isdigit():
        raise ValueError("Please enter a whole number.")
    return int(value)


def read_required(prompt: str) -> str:
    value = input(prompt).strip()
    if not value:
        raise ValueError("This value is required.")
    return value


def build_account(bank: Bank, customer: Customer):
    print("1. Savings Account")
    print("2. Current Account")
    account_type = input("Choose account type: ").strip()
    if account_type == "1":
        account_class = SavingsAccount
        type_name = "Savings"
    elif account_type == "2":
        account_class = CurrentAccount
        type_name = "Current"
    else:
        raise ValueError("Invalid account type.")
    account_number = bank.generate_account_number(type_name)
    print(f"Generated account number: {account_number}")
    opening_balance = read_positive_integer("Opening balance: Rs. ")
    pin = input("Create 4-digit PIN: ").strip()
    confirm_pin = input("Confirm PIN: ").strip()
    if pin != confirm_pin:
        raise ValueError("PIN confirmation does not match.")
    return account_class(account_number, customer, opening_balance, pin)


def register_customer(atm: ATM) -> None:
    print("\n========== CREATE CUSTOMER & ACCOUNT ==========")
    customer_id = atm.bank.generate_customer_id()
    print(f"Generated customer ID: {customer_id}")
    customer = Customer(
        customer_id,
        read_required("Full name: "),
        read_required("Phone or email: "),
    )
    account = build_account(atm.bank, customer)
    card_number = read_required("New card number: ")
    card = Card(card_number, customer, (account.account_number,))
    atm.bank.register_customer_account(customer, account, card)
    print("Customer, account, and ATM card created successfully.")
    print(f"Account: {account.account_number} ({account.account_type})")
    print(f"Card: {card.card_number}")


def add_account(atm: ATM) -> None:
    print("\n========== ADD BANK ACCOUNT ==========")
    customer = atm.bank.get_customer(read_required("Customer ID: "))
    account = build_account(atm.bank, customer)
    atm.bank.add_account(account)
    print(f"Account {account.account_number} created for {customer.name}.")
    print("Use 'Issue Additional Card' to create a card linked to this account.")


def issue_card(atm: ATM) -> None:
    print("\n========== ISSUE ADDITIONAL CARD ==========")
    customer = atm.bank.get_customer(read_required("Customer ID: "))
    if not customer.accounts:
        raise ValueError("Customer has no accounts to link.")
    print("Available accounts:")
    for index, account in enumerate(customer.accounts, 1):
        print(f"{index}. {account.account_number} ({account.account_type})")
    raw_choices = read_required("Account choices (comma-separated): ")
    try:
        choices = {int(value.strip()) for value in raw_choices.split(",")}
    except ValueError as exc:
        raise ValueError("Account choices must be numbers.") from exc
    if not choices or any(choice < 1 or choice > len(customer.accounts) for choice in choices):
        raise ValueError("Invalid account selection.")
    account_numbers = tuple(customer.accounts[index - 1].account_number for index in sorted(choices))
    card = Card(read_required("New card number: "), customer, account_numbers)
    atm.bank.issue_card(card)
    print(f"Card {card.card_number} issued and linked successfully.")


def view_customer(atm: ATM) -> None:
    print("\n========== CUSTOMER DETAILS ==========")
    customer = atm.bank.get_customer(read_required("Customer ID: "))
    print(f"Customer ID: {customer.customer_id}")
    print(f"Name:        {customer.name}")
    print(f"Contact:     {customer.contact}")
    print("Accounts:")
    if not customer.accounts:
        print("  None")
    for account in customer.accounts:
        print(
            f"  {account.account_number} | {account.account_type} | "
            f"{account.status.value} | Rs. {account.balance:,}"
        )
    print("Cards:")
    if not customer.cards:
        print("  None")
    for card in customer.cards:
        linked = ", ".join(card.account_numbers)
        print(f"  {card.card_number} | {card.status.value} | Accounts: {linked}")


def choose_account(atm: ATM, card_number: str) -> str:
    card = atm.bank.get_card(card_number)
    print("\nLinked accounts:")
    for index, number in enumerate(card.account_numbers, 1):
        account = atm.bank.get_account(number)
        print(f"{index}. {number} ({account.account_type})")
    choice = read_positive_integer("Choose account: ")
    if choice < 1 or choice > len(card.account_numbers):
        raise ValueError("Invalid account selection.")
    return card.account_numbers[choice - 1]


def authenticate(atm: ATM) -> Session:
    print("\n========== INSERT CARD ==========")
    card_number = input("Card number: ").strip()
    account_number = choose_account(atm, card_number)
    while True:
        pin = input("Enter PIN: ").strip()
        try:
            return atm.authenticate(card_number, pin, account_number)
        except ATMError as error:
            print(f"Error: {error}")
            if "blocked" in str(error).lower():
                raise


def print_receipt(title: str, transaction_id: str, amount: int, balance: int) -> None:
    print(f"\n{title}")
    print("-" * 40)
    print(f"Amount:         Rs. {amount:,}")
    print(f"Transaction ID: {transaction_id}")
    print(f"New Balance:    Rs. {balance:,}")


def show_statement(session: Session) -> None:
    print("\n========== MINI STATEMENT ==========")
    print(f"Account: {session.account.account_number}")
    print(f"{'Date':<14}{'Type':<18}{'Amount':>18}")
    print("-" * 50)
    transactions = session.account.mini_statement()
    if not transactions:
        print(f"{'--':<14}{'No transactions':<18}{'Rs. 0':>18}")
    else:
        for transaction in transactions:
            sign = "+" if transaction.signed_amount >= 0 else "-"
            amount = f"{sign}Rs. {abs(transaction.signed_amount):,}"
            print(
                f"{transaction.timestamp:%d-%b %H:%M}  "
                f"{transaction.transaction_type.title():<18}{amount:>18}"
            )
    print("-" * 50)
    print(f"Current Balance: Rs. {session.account.balance:,}")


def run_menu(atm: ATM, session: Session) -> None:
    while True:
        print("""
====== ATM ======
1. Check Balance
2. Deposit
3. Withdraw
4. Transfer Money
5. Change PIN
6. Mini Statement
7. Exit""")
        choice = input("Select an option: ").strip()
        try:
            if choice == "1":
                print(f"Available balance: Rs. {session.account.check_balance():,}")
            elif choice == "2":
                amount = read_positive_integer("Deposit amount: Rs. ")
                transaction = atm.deposit(session, amount)
                print_receipt("Deposit successful", transaction.transaction_id, amount, session.account.balance)
            elif choice == "3":
                amount = read_positive_integer("Withdrawal amount: Rs. ")
                transaction, notes = atm.withdraw(session, amount)
                print_receipt("Withdrawal successful", transaction.transaction_id, amount, session.account.balance)
                print("Cash dispensed: " + ", ".join(f"Rs. {d:,} x {q}" for d, q in sorted(notes.items(), reverse=True)))
            elif choice == "4":
                receiver = input("Receiver account number: ").strip()
                amount = read_positive_integer("Transfer amount: Rs. ")
                debit, _ = atm.transfer(session, receiver, amount)
                print_receipt("Transfer successful", debit.transaction_id, amount, session.account.balance)
            elif choice == "5":
                old_pin = input("Current PIN: ").strip()
                new_pin = input("New PIN: ").strip()
                session.account.change_pin(old_pin, new_pin)
                print("PIN changed successfully.")
            elif choice == "6":
                show_statement(session)
            elif choice == "7":
                print("Card ejected. Thank you for using OOP Bank ATM.")
                return
            else:
                print("Invalid menu option.")
        except (ATMError, ValueError) as error:
            print(f"Error: {error}")


def main() -> None:
    atm = build_demo_atm()
    while True:
        print("""
========== OOP BANKING SYSTEM ==========
1. Use ATM
2. Create Customer and First Account
3. Add Account to Existing Customer
4. Issue Additional Card
5. View Customer Accounts and Cards
6. Exit""")
        choice = input("Select an option: ").strip()
        try:
            if choice == "1":
                session = authenticate(atm)
                print(f"\nWelcome, {session.card.customer.name}.")
                run_menu(atm, session)
            elif choice == "2":
                register_customer(atm)
            elif choice == "3":
                add_account(atm)
            elif choice == "4":
                issue_card(atm)
            elif choice == "5":
                view_customer(atm)
            elif choice == "6":
                print("Thank you for using OOP Banking System.")
                return
            else:
                print("Invalid menu option.")
        except (ATMError, ValueError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()
