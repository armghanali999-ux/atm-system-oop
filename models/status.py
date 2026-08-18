from enum import Enum


class AccountStatus(Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"


class CardStatus(Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class TransactionStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
