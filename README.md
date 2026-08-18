# ATM System - Class-Based OOP Assignment

A console-based ATM system implemented in Python using classes and object-oriented programming.

## Project Structure

```text
ATM System/
|-- exceptions/       Custom ATM exception classes
|-- models/           Accounts, cards, customers, sessions and transactions
|-- services/         ATM and bank coordination/business services
|-- console/          Reusable demo-data setup
|-- main.py           Console application entry point
|-- test_atm_system.py
`-- README.md
```

## Run

Python 3.10 or newer is required. No third-party packages are needed.

```powershell
python main.py
```

The banking main menu provides:

1. ATM access
2. New customer, first account, and first card registration
3. Additional account creation for an existing customer
4. Additional card issuance linked to one or more accounts
5. Customer account and card details

The original seven-option ATM menu remains available through **Use ATM**.

Customer IDs are generated sequentially (`CUST-001`, `CUST-002`, ...).
Account numbers are generated automatically as unique eight-digit values:

- Savings accounts start with `1`
- Current accounts start with `2`

Demo customer credentials:

| Card number | PIN | Accounts |
|---|---:|---|
| `4242424242424242` | `2580` | `10002345` Savings, `20002345` Current |
| `4000000000000002` | `2580` | `10002345` Savings (Armaghan's second card) |
| `5555555555554444` | `7391` | `10006789` Savings |

To transfer money from Ali's account, use Sara's account number `10006789`.

## Test

```powershell
python -m unittest -v
```

## Assignment Coverage

- Abstract `Account` and `Transaction` base classes in separate model modules
- `SavingsAccount` and `CurrentAccount` inheritance with polymorphic limits, funds, and fees
- Deposit, withdrawal, transfer, balance, PIN change, and last-five mini statement
- Three-attempt card blocking and account/card status validation
- Private balance, PIN, status, transaction history, and cash inventory
- Minimum/per-transaction/daily withdrawal rules and daily transfer tracking
- ATM note inventory and exact denomination selection
- Separate sender debit and receiver credit transfer records
- Multiple accounts and multiple cards per customer
- Interactive customer registration, account creation, and card issuance
- Custom exceptions for individual business failures
- Generated transaction IDs and timestamps
