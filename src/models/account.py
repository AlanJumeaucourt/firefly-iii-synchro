from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Account:
    name: str
    account_type: str = "asset"
    account_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    active: bool = True
    order: Optional[int] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    currency_decimal_places: Optional[int] = None
    current_balance: float = 0.0
    current_balance_date: Optional[str] = None
    notes: Optional[str] = None
    monthly_payment_date: Optional[str] = None
    credit_card_type: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    virtual_balance: Optional[float] = None
    opening_balance: Optional[float] = None
    opening_balance_date: Optional[str] = None
    liability_type: Optional[str] = None
    liability_direction: Optional[str] = None
    interest: Optional[float] = None
    interest_period: Optional[str] = None
    current_debt: Optional[float] = None
    include_net_worth: bool = True
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    zoom_level: Optional[int] = None

    def __str__(self) -> str:
        return f"Account {self.account_type:<17} Name: {self.name:<30}"

    def __hash__(self) -> int:
        return hash((self.account_type, self.name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return False
        return self.__hash__() == other.__hash__()
