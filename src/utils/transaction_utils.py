import math
from typing import List
from models.transaction import Transaction


def check_kresus_missing_transactions(
    local_transactions: List[Transaction], transactions_list: List[Transaction]
) -> List[Transaction]:
    """
    Compares Kresus transactions with those in an external dataset to identify missing transactions.

    Args:
        local_transactions (List[Transaction]): Transactions obtained from Kresus.
        transactions_list (List[Transaction]): Transactions from the external dataset.

    Returns:
        List[Transaction]: Transactions that are present in Kresus but missing in the external dataset.
    """
    missing_transactions: List[Transaction] = []

    for local_transaction in local_transactions:
        match_found = False

        for transaction in transactions_list:
            if (
                local_transaction.date == transaction.date
                and math.isclose(
                    local_transaction.amount, transaction.amount, abs_tol=0.001
                )
                and (
                    (local_transaction.source_name == transaction.source_name)
                    or (
                        local_transaction.destination_name
                        == transaction.destination_name
                    )
                )
            ):
                match_found = True
                break
        if not match_found:
            missing_transactions.append(local_transaction)

    return missing_transactions
