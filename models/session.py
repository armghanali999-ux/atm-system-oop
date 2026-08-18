from dataclasses import dataclass

from .account import Account
from .card import Card


@dataclass(frozen=True)
class Session:
    card: Card
    account: Account
