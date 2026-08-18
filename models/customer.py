from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .account import Account
    from .card import Card


class Customer:
    def __init__(self, customer_id: str, name: str, contact: str) -> None:
        self.customer_id = customer_id
        self.name = name
        self.contact = contact
        self.__accounts: dict[str, Account] = {}
        self.__cards: dict[str, Card] = {}

    @property
    def accounts(self) -> tuple[Account, ...]:
        return tuple(self.__accounts.values())

    @property
    def cards(self) -> tuple[Card, ...]:
        return tuple(self.__cards.values())

    def add_account(self, account: Account) -> None:
        self.__accounts[account.account_number] = account

    def add_card(self, card: Card) -> None:
        self.__cards[card.card_number] = card

    def get_account(self, account_number: str) -> Account | None:
        return self.__accounts.get(account_number)
