from datetime import datetime
import math
import logging
from fuzzywuzzy import fuzz
import pandas as pd
import re

logger = logging.getLogger(__name__)


class Account:
    """
    Represents a financial account.

    Attributes:
        name (str): The name of the account.
        account_type (str, optional): The type of the account. Defaults to "asset".
        account_id (int, optional): The ID of the account.
        created_at (str, optional): The creation date of the account.
        updated_at (str, optional): The last update date of the account.
        active (bool, optional): Indicates if the account is active.
        order (int, optional): The order of the account.
        currency_code (str, optional): The currency code of the account.
        currency_symbol (str, optional): The currency symbol of the account.
        currency_decimal_places (int, optional): The number of decimal places for the currency.
        current_balance (float, optional): The current balance of the account. Defaults to 0.
        current_balance_date (str, optional): The date of the current balance.
        notes (str, optional): Additional notes for the account.
        monthly_payment_date (str, optional): The date of the monthly payment.
        credit_card_type (str, optional): The type of credit card.
        account_number (str, optional): The account number.
        iban (str, optional): The International Bank Account Number (IBAN).
        bic (str, optional): The Bank Identifier Code (BIC).
        virtual_balance (float, optional): The virtual balance of the account.
        opening_balance (float, optional): The opening balance of the account.
        opening_balance_date (str, optional): The date of the opening balance.
        liability_type (str, optional): The type of liability.
        liability_direction (str, optional): The direction of the liability.
        interest (float, optional): The interest rate of the account.
        interest_period (str, optional): The period of interest calculation.
        current_debt (float, optional): The current debt of the account.
        include_net_worth (bool, optional): Indicates if the account is included in net worth calculations.
        longitude (float, optional): The longitude coordinate of the account.
        latitude (float, optional): The latitude coordinate of the account.
        zoom_level (int, optional): The zoom level of the account.
    """

    def __init__(
        self,
        name: str,
        account_type: str = "asset",
        account_id: int = None,
        created_at: str = None,
        updated_at: str = None,
        active: bool = None,
        order: int = None,
        currency_code: str = None,
        currency_symbol: str = None,
        currency_decimal_places: int = None,
        current_balance: float = 0,
        current_balance_date: str = None,
        notes: str = None,
        monthly_payment_date: str = None,
        credit_card_type: str = None,
        account_number: str = None,
        iban: str = None,
        bic: str = None,
        virtual_balance: float = None,
        opening_balance: float = None,
        opening_balance_date: str = None,
        liability_type: str = None,
        liability_direction: str = None,
        interest: float = None,
        interest_period: str = None,
        current_debt: float = None,
        include_net_worth: bool = None,
        longitude: float = None,
        latitude: float = None,
        zoom_level: int = None,
    ):
        self.name = name
        self.account_type = account_type
        self.account_id = account_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.active = active
        self.order = order
        self.currency_code = currency_code
        self.currency_symbol = currency_symbol
        self.currency_decimal_places = currency_decimal_places
        self.current_balance = float(current_balance)
        self.current_balance_date = current_balance_date
        self.notes = notes
        self.monthly_payment_date = monthly_payment_date
        self.credit_card_type = credit_card_type
        self.account_number = account_number
        self.iban = iban
        self.bic = bic
        self.virtual_balance = virtual_balance
        self.opening_balance = opening_balance
        self.opening_balance_date = opening_balance_date
        self.liability_type = liability_type
        self.liability_direction = liability_direction
        self.interest = interest
        self.interest_period = interest_period
        self.current_debt = current_debt
        self.include_net_worth = include_net_worth
        self.longitude = longitude
        self.latitude = latitude
        self.zoom_level = zoom_level

    def __str__(self):
        return f"Account {self.account_type:<17} Name: {self.name:<30}"

    def __hash__(self):
        # Hash function combining hash of relevant attributes
        return hash((self.account_type, self.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, Account):
            return self.__hash__() == other.__hash__()
        else:
            return False


class Transaction:
    """
    Represents a financial transaction.

    Args:
        date (str or pd.Timestamp): The date of the transaction.
        amount (float): The amount of the transaction.
        type (str, optional): The type of the transaction. Defaults to "".
        description (str, optional): The description of the transaction. Defaults to "".
        transaction_id (int, optional): The ID of the transaction. Defaults to None.
        bill_id (int, optional): The ID of the bill associated with the transaction. Defaults to None.
        bill_name (str, optional): The name of the bill associated with the transaction. Defaults to None.
        book_date (str, optional): The book date of the transaction. Defaults to None.
        budget_id (int, optional): The ID of the budget associated with the transaction. Defaults to None.
        budget_name (str, optional): The name of the budget associated with the transaction. Defaults to None.
        bunq_payment_id (int, optional): The ID of the bunq payment associated with the transaction. Defaults to None.
        category_id (int, optional): The ID of the category associated with the transaction. Defaults to None.
        category_name (str, optional): The name of the category associated with the transaction. Defaults to None.
        currency_code (str, optional): The currency code of the transaction. Defaults to None.
        currency_decimal_places (int, optional): The decimal places of the currency. Defaults to None.
        currency_id (int, optional): The ID of the currency. Defaults to None.
        currency_name (str, optional): The name of the currency. Defaults to None.
        currency_symbol (str, optional): The symbol of the currency. Defaults to None.
        destination_iban (str, optional): The IBAN of the destination. Defaults to None.
        destination_id (int, optional): The ID of the destination. Defaults to None.
        destination_name (str, optional): The name of the destination. Defaults to None.
        destination_type (str, optional): The type of the destination. Defaults to None.
        due_date (str, optional): The due date of the transaction. Defaults to None.
        external_id (str, optional): The external ID of the transaction. Defaults to None.
        external_url (str, optional): The external URL of the transaction. Defaults to None.
        foreign_amount (float, optional): The foreign amount of the transaction. Defaults to None.
        foreign_currency_code (str, optional): The foreign currency code of the transaction. Defaults to None.
        foreign_currency_decimal_places (int, optional): The decimal places of the foreign currency. Defaults to None.
        foreign_currency_id (int, optional): The ID of the foreign currency. Defaults to None.
        foreign_currency_symbol (str, optional): The symbol of the foreign currency. Defaults to None.
        has_attachments (bool, optional): Indicates if the transaction has attachments. Defaults to None.
        import_hash_v2 (str, optional): The import hash of the transaction. Defaults to None.
        interest_date (str, optional): The interest date of the transaction. Defaults to None.
        internal_reference (str, optional): The internal reference of the transaction. Defaults to None.
        invoice_date (str, optional): The invoice date of the transaction. Defaults to None.
        latitude (float, optional): The latitude of the transaction. Defaults to None.
        longitude (float, optional): The longitude of the transaction. Defaults to None.
        notes (str, optional): The notes of the transaction. Defaults to None.
        order (int, optional): The order of the transaction. Defaults to None.
        original_source (str, optional): The original source of the transaction. Defaults to None.
        payment_date (str, optional): The payment date of the transaction. Defaults to None.
        process_date (str, optional): The process date of the transaction. Defaults to None.
        reconciled (bool, optional): Indicates if the transaction is reconciled. Defaults to None.
        recurrence_count (int, optional): The recurrence count of the transaction. Defaults to None.
        recurrence_id (int, optional): The recurrence ID of the transaction. Defaults to None.
        recurrence_total (int, optional): The recurrence total of the transaction. Defaults to None.
        sepa_batch_id (int, optional): The SEPA batch ID of the transaction. Defaults to None.
        sepa_cc (str, optional): The SEPA CC of the transaction. Defaults to None.
        sepa_ci (str, optional): The SEPA CI of the transaction. Defaults to None.
        sepa_country (str, optional): The SEPA country of the transaction. Defaults to None.
        sepa_ct_id (str, optional): The SEPA CT ID of the transaction. Defaults to None.
        sepa_ct_op (str, optional): The SEPA CT OP of the transaction. Defaults to None.
        sepa_db (str, optional): The SEPA DB of the transaction. Defaults to None.
        sepa_ep (str, optional): The SEPA EP of the transaction. Defaults to None.
        source_iban (str, optional): The IBAN of the source. Defaults to None.
        source_id (int, optional): The ID of the source. Defaults to None.
        source_name (str, optional): The name of the source. Defaults to None.
        source_type (str, optional): The type of the source. Defaults to None.
        tags (str, optional): The tags of the transaction. Defaults to None.
        transaction_journal_id (int, optional): The ID of the transaction journal. Defaults to None.
        user (str, optional): The user associated with the transaction. Defaults to None.
        zoom_level (int, optional): The zoom level of the transaction. Defaults to None.

    Attributes:
        transaction_id (int): The ID of the transaction.
        amount (float): The amount of the transaction.
        type (str): The type of the transaction.
        description (str): The description of the transaction.
        date (datetime.date): The date of the transaction.
        ...

    Methods:
        __str__(): Returns a string representation of the transaction.
        __hash__(): Returns the hash value of the transaction.
        custom_normalized_score(str1, str2): Calculates the custom normalized score between two strings.
        _rm_date(input_string): Removes the date from the input string.
        _cleaned_description(description): Cleans the description by removing extra repetitions and specific strings.
        _compare_descriptions(other, threshold): Compares the descriptions of two transactions and returns True if they match.
        __eq__(other): Checks if two transactions are equal.

    """

    def __init__(
        self,
        date,
        amount,
        type: str = "",
        description: str = "",
        transaction_id=None,
        bill_id=None,
        bill_name=None,
        book_date=None,
        budget_id=None,
        budget_name=None,
        bunq_payment_id=None,
        category_id=None,
        category_name=None,
        currency_code=None,
        currency_decimal_places=None,
        currency_id=None,
        currency_name=None,
        currency_symbol=None,
        destination_iban=None,
        destination_id=None,
        destination_name=None,
        destination_type=None,
        due_date=None,
        external_id=None,
        external_url=None,
        foreign_amount=None,
        foreign_currency_code=None,
        foreign_currency_decimal_places=None,
        foreign_currency_id=None,
        foreign_currency_symbol=None,
        has_attachments=None,
        import_hash_v2=None,
        interest_date=None,
        internal_reference=None,
        invoice_date=None,
        latitude=None,
        longitude=None,
        notes=None,
        order=None,
        original_source=None,
        payment_date=None,
        process_date=None,
        reconciled=None,
        recurrence_count=None,
        recurrence_id=None,
        recurrence_total=None,
        sepa_batch_id=None,
        sepa_cc=None,
        sepa_ci=None,
        sepa_country=None,
        sepa_ct_id=None,
        sepa_ct_op=None,
        sepa_db=None,
        sepa_ep=None,
        source_iban=None,
        source_id=None,
        source_name=None,
        source_type=None,
        tags=None,
        transaction_journal_id=None,
        user=None,
        zoom_level=None,
    ):
        self.transaction_id = int(transaction_id) if transaction_id else None
        self.amount = float(amount)
        self.type = type
        self.bill_id = bill_id
        self.bill_name = bill_name
        self.book_date = book_date
        self.budget_id = budget_id
        self.budget_name = budget_name
        self.bunq_payment_id = bunq_payment_id
        self.category_id = category_id
        self.category_name = category_name
        self.currency_code = currency_code
        self.currency_decimal_places = currency_decimal_places
        self.currency_id = currency_id
        self.currency_name = currency_name
        self.currency_symbol = currency_symbol
        if isinstance(date, str):
            try:
                self.date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                self.date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").date()
        elif isinstance(date, pd.Timestamp):
            self.date = date.to_pydatetime().date()
        else:
            logger.error(f"Invalid date format during transaction creation: =\n{date=}")
            raise ValueError(
                f"Invalid date format during transaction creation: =\n{date=}"
            )
        self.description = description if description else ""
        self.destination_iban = destination_iban
        self.destination_id = destination_id
        self.destination_name = destination_name
        self.destination_type = destination_type
        self.due_date = due_date
        self.external_id = external_id
        self.external_url = external_url
        self.foreign_amount = foreign_amount
        self.foreign_currency_code = foreign_currency_code
        self.foreign_currency_decimal_places = foreign_currency_decimal_places
        self.foreign_currency_id = foreign_currency_id
        self.foreign_currency_symbol = foreign_currency_symbol
        self.has_attachments = has_attachments
        self.import_hash_v2 = import_hash_v2
        self.interest_date = interest_date
        self.internal_reference = internal_reference
        self.invoice_date = invoice_date
        self.latitude = latitude
        self.longitude = longitude
        self.notes = notes
        self.order = order
        self.original_source = original_source
        self.payment_date = payment_date
        self.process_date = process_date
        self.reconciled = reconciled
        self.recurrence_count = recurrence_count
        self.recurrence_id = recurrence_id
        self.recurrence_total = recurrence_total
        self.sepa_batch_id = sepa_batch_id
        self.sepa_cc = sepa_cc
        self.sepa_ci = sepa_ci
        self.sepa_country = sepa_country
        self.sepa_ct_id = sepa_ct_id
        self.sepa_ct_op = sepa_ct_op
        self.sepa_db = sepa_db
        self.sepa_ep = sepa_ep
        self.source_iban = source_iban
        self.source_id = source_id
        self.source_name = source_name
        self.source_type = source_type
        self.tags = tags
        self.transaction_journal_id = transaction_journal_id
        self.transaction_type = type
        self.user = user
        self.zoom_level = zoom_level

    def __str__(self):
        if self.transaction_id:
            return f"Transaction ID: {self.transaction_id:<5} Type: {str(self.transaction_type):<17} Amount: {str(self.amount) + str(self.currency_symbol)} Date: {str(self.date):<10} Description: {str(self.description):<30}"
        else:
            return f"Type: {str(self.transaction_type):<17} Amount: {str(self.amount) + str(self.currency_symbol)} Date: {str(self.date):<10} Description: {str(self.description):<30}"

    def __hash__(self):
        # Hash function combining hash of relevant attributes
        return hash(
            (
                self.type,
                round(self.amount, 2),  # Using round for hashing floats
                self.date,
                self.source_name,
                self.destination_name,
            )
        )

    def custom_normalized_score(self, str1, str2):
        # Example of normalization: remove extra repetitions
        # This is a simple example, you might need a more sophisticated approach
        # Use different fuzzywuzzy methods
        score1 = fuzz.ratio(str1, str2)
        score2 = fuzz.partial_ratio(str1, str2)
        score3 = fuzz.token_sort_ratio(str1, str2)

        # Combine scores (example, you can modify the logic)
        final_score = max(score1, score2, score3)
        return final_score

    def _rm_date(self, input_string):
        pattern = r"(.+?)(\d{2}/\d{2})?$"
        return re.sub(pattern, r"\1", input_string)

    def _cleaned_description(self, description):
        return self._rm_date(
            "".join(description.split()).replace("PAIEMENTPARCARTE", "")
        ).replace("AVOIR CARTE", "")

    def _compare_descriptions(self, other: "Transaction", threshold: int = 95):
        self_desc = self._cleaned_description(str(self.description))
        other_desc = self._cleaned_description(str(other.description))

        logger.debug(f"Cleaned Descriptions: {self_desc}, {other_desc}")
        logger.debug(
            f"Fuzzy Match Score: {self.custom_normalized_score(self_desc, other_desc)}\n"
        )

        result = self.custom_normalized_score(self_desc, other_desc) >= threshold
        logger.debug(f"Result: {result}")
        return result

    def __eq__(self, other) -> bool:
        if isinstance(other, Transaction):
            if self.date != other.date or not math.isclose(
                self.amount, other.amount, abs_tol=0.01
            ):
                return False

            if not self._compare_descriptions(other):
                logger.debug(
                    f"Type: {self.type} == {other.type}: {self.type == other.type}"
                )
                logger.debug(
                    f"Amount: {self.amount} ~ {other.amount}: {math.isclose(self.amount, other.amount, abs_tol=0.01)}"
                )
                logger.debug(f"Date: {self.date} == {other.date}")
                logger.debug(
                    f"Source: {self.source_name} == {other.source_name}: {self.source_name == other.source_name}"
                )
                logger.debug(
                    f"Destination: {self.destination_name} == {other.destination_name}: {self.destination_name == other.destination_name}"
                )

                return False

            return self.__hash__() == other.__hash__()

        return False
