from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime, date
import logging
from fuzzywuzzy import fuzz
import re

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

@dataclass
class Transaction:
    date: date
    amount: float
    type: str = ""
    description: str = ""
    transaction_id: Optional[int] = None
    bill_id: Optional[int] = None
    bill_name: Optional[str] = None
    book_date: Optional[str] = None
    budget_id: Optional[int] = None
    budget_name: Optional[str] = None
    bunq_payment_id: Optional[int] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    currency_code: Optional[str] = None
    currency_decimal_places: Optional[int] = None
    currency_id: Optional[int] = None
    currency_name: Optional[str] = None
    currency_symbol: Optional[str] = None
    destination_iban: Optional[str] = None
    destination_id: Optional[int] = None
    destination_name: Optional[str] = None
    destination_type: Optional[str] = None
    due_date: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    foreign_amount: Optional[float] = None
    foreign_currency_code: Optional[str] = None
    foreign_currency_decimal_places: Optional[int] = None
    foreign_currency_id: Optional[int] = None
    foreign_currency_symbol: Optional[str] = None
    has_attachments: Optional[bool] = None
    import_hash_v2: Optional[str] = None
    interest_date: Optional[str] = None
    internal_reference: Optional[str] = None
    invoice_date: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    order: Optional[int] = None
    original_source: Optional[str] = None
    payment_date: Optional[str] = None
    process_date: Optional[str] = None
    reconciled: Optional[bool] = None
    recurrence_count: Optional[int] = None
    recurrence_id: Optional[int] = None
    recurrence_total: Optional[int] = None
    sepa_batch_id: Optional[int] = None
    sepa_cc: Optional[str] = None
    sepa_ci: Optional[str] = None
    sepa_country: Optional[str] = None
    sepa_ct_id: Optional[str] = None
    sepa_ct_op: Optional[str] = None
    sepa_db: Optional[str] = None
    sepa_ep: Optional[str] = None
    source_iban: Optional[str] = None
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    transaction_journal_id: Optional[int] = None
    user: Optional[str] = None
    zoom_level: Optional[int] = None

    def __post_init__(self):
        if isinstance(self.date, str):
            try:
                self.date = datetime.strptime(self.date, "%Y-%m-%d").date()
            except ValueError:
                self.date = datetime.strptime(self.date, "%Y-%m-%dT%H:%M:%S%z").date()
        elif not isinstance(self.date, date):
            raise ValueError(f"Invalid date format: {self.date}")

    def __str__(self) -> str:
        if self.transaction_id:
            return f"Transaction ID: {self.transaction_id:<5} Type: {self.type:<17} Amount: {self.amount}{self.currency_symbol or ''} Date: {self.date!s:<10} Description: {self.description:<30}"
        else:
            return f"| Type: {self.type:<10} Amount: {self.amount:<6} Date: {self.date!s:<10} Description: {self.description:<40} |"

    def __hash__(self) -> int:
        return hash((self.type, round(self.amount, 2), self.date, self.source_name, self.destination_name))

    @staticmethod
    def custom_normalized_score(str1: str, str2: str) -> float:
        score1 = fuzz.ratio(str1, str2)
        score2 = fuzz.partial_ratio(str1, str2)
        score3 = fuzz.token_sort_ratio(str1, str2)
        return max(score1, score2, score3)

    @staticmethod
    def _rm_date(input_string: str) -> str:
        pattern = r"(.+?)(\d{2}/\d{2})?$"
        return re.sub(pattern, r"\1", input_string)

    def _cleaned_description(self) -> str:
        return self._rm_date("".join(self.description.split()).replace("PAIEMENTPARCARTE", "")).replace("AVOIR CARTE", "")

    def compare_descriptions(self, other: 'Transaction', threshold: int = 95) -> bool:
        self_desc = self._cleaned_description()
        other_desc = other._cleaned_description()

        logger.debug(f"Cleaned Descriptions: {self_desc}, {other_desc}")
        score = self.custom_normalized_score(self_desc, other_desc)
        logger.debug(f"Fuzzy Match Score: {score}")

        result = score >= threshold
        logger.debug(f"Result: {result}")
        return result

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return False
        
        if self.date != other.date or not abs(self.amount - other.amount) < 0.01:
            return False

        if not self.compare_descriptions(other):
            logger.debug(f"Type: {self.type} == {other.type}: {self.type == other.type}")
            logger.debug(f"Amount: {self.amount} ~ {other.amount}: {abs(self.amount - other.amount) < 0.01}")
            logger.debug(f"Date: {self.date} == {other.date}")
            logger.debug(f"Source: {self.source_name} == {other.source_name}: {self.source_name == other.source_name}")
            logger.debug(f"Destination: {self.destination_name} == {other.destination_name}: {self.destination_name == other.destination_name}")
            return False

        return self.__hash__() == other.__hash__()