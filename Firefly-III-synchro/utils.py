import pandas as pd
from datetime import datetime, date
import math
import logging
from models import Transaction, Account  # Assuming models.py is in the same directory
from typing import List
from firefly_api import FireflyIIIAPI
from kresus import Kresus
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


def get_local_transaction(filename: str = "accountabilityGood.xlsm"):
    """
    Reads and processes transaction data from a specified Excel file.

    Args:
        filename (str): The path to the Excel file containing transaction data.

    Returns:
        List[Transaction]: A list of Transaction objects parsed from the Excel file.
    """

    local_transaction_list: List[Transaction] = []
    global df_transactions
    df_transactions = pd.read_excel(
        filename,
        sheet_name="Transactions",
        header=2,
        engine="openpyxl",
    )
    df_transactions.fillna("")
    local_list_accounts = get_local_account()
    for index, row in df_transactions.iterrows():
        logger.debug(f"{row=}")
        name_local_transaction: List[str] = [
            account.name for account in local_list_accounts
        ]

        if row["Destination"] not in name_local_transaction:
            local_transaction_type = "withdrawal"
        elif row["Source"] not in name_local_transaction:
            local_transaction_type = "deposit"
        elif (
            row["Source"] in name_local_transaction
            and row["Destination"] in name_local_transaction
        ):
            local_transaction_type = "transfer"
        else:
            raise ValueError("Transaction type could not be detected.")

        local_transaction_list.append(
            Transaction(
                date=row["Date"],
                amount=row["Montant"],
                description=row["Libellé"],
                source_name=row["Source"],
                destination_name=row["Destination"],
                type=local_transaction_type,
                transaction_id=row["FireflyID"]
                if not math.isnan(row["FireflyID"])
                else None,
            )
        )

    return local_transaction_list


def get_local_account(filename: str = "accountabilityGood.xlsm"):
    """
    Reads and processes account data from a specified Excel file.

    Args:
        filename (str): The path to the Excel file containing account data.

    Returns:
        List[Account]: A list of Account objects parsed from the Excel file.
    """
    local_list_accounts: List[Account] = []
    df_accounts = pd.read_excel(
        filename, sheet_name="Comptes", header=2, engine="openpyxl"
    )

    for index, row in df_accounts.iterrows():
        logger.debug(row["Nom"])
        if row["Type"] != "" and row["Type"] != "Fake":
            local_list_accounts.append(Account(name=row["Nom"], account_type="asset"))

    return local_list_accounts


def check_missing_transactions(
    local_transactions: List[Transaction], transactions_list: List[Transaction]
) -> List[Transaction]:
    """
    Identifies transactions that are present in the local dataset but missing in the external dataset.

    Args:
        local_transactions (List[Transaction]): The list of transactions from the local dataset.
        transactions_list (List[Transaction]): The list of transactions from the external dataset.

    Returns:
        List[Transaction]: A list of transactions that are missing in the external dataset.
    """
    missing_transactions: List[Transaction] = []
    for local_transaction in local_transactions:
        if (
            local_transaction.transaction_id is None
            and local_transaction not in transactions_list
        ):
            missing_transactions.append(local_transaction)
    return missing_transactions


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
                logger.debug(
                    f"{local_transaction.type=} && {transaction.type=} : {local_transaction.type == transaction.type}"
                )
                logger.debug(
                    f"{local_transaction.amount=} && {transaction.amount=} : {math.isclose(local_transaction.amount, transaction.amount, abs_tol=0.001)}"
                )
                logger.debug(
                    f"{local_transaction.date=} && {transaction.date=} : {local_transaction.date == transaction.date}"
                )
                logger.debug(
                    f"{local_transaction.source_name=} && {transaction.source_name=} : {local_transaction.source_name == transaction.source_name}"
                )
                logger.debug(
                    f"{local_transaction.destination_name=} && {transaction.destination_name=} : {local_transaction.destination_name == transaction.destination_name}"
                )
                logger.debug(
                    f"{local_transaction.description=} && {transaction.description=} : {Transaction._compare_descriptions(local_transaction, transaction, 50) if local_transaction.type != 'transfer' else True}\n"
                )
                match_found = True
                break
        if not match_found:
            missing_transactions.append(local_transaction)
            logger.info(f"{local_transaction.date=}")
            logger.info(f"{local_transaction.amount=}")
            logger.info(f"{local_transaction.source_name=}")
            logger.info(f"{local_transaction.destination_name=}")
            logger.info(f"{local_transaction.description=}\n")

    return missing_transactions


def add_missing_transactions(
    firefly_api: FireflyIIIAPI, missing_transactions: List[Transaction]
):
    """
    Adds missing transactions to an external dataset using the Firefly III API.

    Args:
        firefly_api (FireflyIIIAPI): An instance of the FireflyIIIAPI class.
        missing_transactions (List[Transaction]): A list of transactions to be added.
    """

    for missing_transaction in missing_transactions:
        transaction_data = {
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [
                {
                    "type": missing_transaction.type,
                    "date": missing_transaction.date.strftime("%Y-%m-%d"),
                    "amount": str(missing_transaction.amount),
                    "description": str(missing_transaction.description),
                    "source_name": missing_transaction.source_name,
                    "destination_name": missing_transaction.destination_name,
                    "category_name": "",
                    "interest_date": "",
                    "book_date": "",
                    "process_date": "",
                    "due_date": "",
                    "payment_date": "",
                    "invoice_date": "",
                    "internal_reference": "",
                    "notes": "",
                    "external_url": "",
                }
            ],
        }
        logger.info(transaction_data)
        firefly_api.store_transaction(transaction_data=transaction_data)


def dump_transaction_to_csv(transactions_list: List[Transaction], filename: str):
    """
    Exports a list of transactions to a CSV file.

    Args:
        transactions_list (List[Transaction]): A list of transactions to be exported.
        filename (str): The path to the output CSV file.
    """
    df_transactions = pd.DataFrame(
        [
            {
                "Date": transaction.date,
                "FireflyID": transaction.transaction_id,
                "Type": transaction.type,
                "Libellé": transaction.description,
                "Montant": transaction.amount,
                "Source": transaction.source_name,
                "Destination": transaction.destination_name,
            }
            for transaction in transactions_list
        ]
    )

    df_transactions.to_csv(filename, index=False)


def dump_account_to_csv(accounts_list: List[Account], filename: str):
    """
    Exports a list of accounts to a CSV file.

    Args:
        accounts_list (List[Account]): A list of accounts to be exported.
        filename (str): The path to the output CSV file.
    """
    df_accounts = pd.DataFrame(
        [
            {"Nom": account.name, "Type": account.account_type}
            for account in accounts_list
        ]
    )

    df_accounts = df_accounts.sort_values(by=["Nom"])

    df_accounts.to_csv(filename, index=False)


def update_local_to_firefly( 
    firefly_api: FireflyIIIAPI,
    local_transactions: List[Transaction],
    transactions_list: List[Transaction],
):
    """
    Updates the local transaction dataset in Firefly III.

    Args:
        firefly_api (FireflyIIIAPI): An instance of the FireflyIIIAPI class.
        local_transactions (List[Transaction]): The list of local transactions.
        transactions_list (List[Transaction]): The list of transactions from Firefly III.
    """
    for local_transaction in local_transactions:
        for transaction in transactions_list:
            if local_transaction.transaction_id == transaction.transaction_id:
                if local_transaction != transaction:
                    updated_transaction_data = {
                        "apply_rules": True,
                        "fire_webhooks": True,
                        "transactions": [
                            {
                                "type": local_transaction.type,
                                "date": local_transaction.date.strftime("%Y-%m-%d"),
                                "amount": str(local_transaction.amount),
                                "description": str(local_transaction.description),
                                "source_name": local_transaction.source_name,
                                "source_type": "Asset account",
                                "source_id": "9",
                                "destination_name": local_transaction.destination_name,
                                'destination_id': '44', 'destination_name': 'Banque', 'destination_type': 'Expense account'
                            }
                        ],
                    }
                    logger.info("Updating transaction :")
                    logger.info(f"{local_transaction=}")

                    if local_transaction.type == transaction.type:
                        updated_transaction = firefly_api.update_transaction(
                            transaction_id=transaction.transaction_id,
                            updated_transaction_data=updated_transaction_data,
                        )
                    else:
                        # At this point, transaction type need to be change
                        # As there no API endoint, we need to delete and create a new transaction
                        firefly_api.delete_transaction(transaction.transaction_id)
                        updated_transaction = firefly_api.store_transaction(
                            transaction_data=updated_transaction_data
                        )

                    if updated_transaction != local_transaction:
                        logger.error("Something went wrong")
                        logger.error(f"{local_transaction=}")
                        logger.error(f"{local_transaction.__dict__=}")
                        logger.error(f"{updated_transaction=}")
                        logger.error(f"{updated_transaction.__dict__=}")
                        exit()
                    else:
                        # Dose not change id if transaction type were the same
                        # But update the transaction_id if transaction type were different
                        # See why in the above comment
                        local_transaction.transaction_id = (
                            updated_transaction.transaction_id
                        )


def update_kresus_to_firefly(firefly_api: FireflyIIIAPI, kresus: Kresus):
    """
    Updates Kresus data in Firefly III.

    Args:
        firefly_api (FireflyIIIAPI): An instance of the FireflyIIIAPI class.
        kresus (Kresus): An instance of the Kresus class.
    """
    firefly_transactions_list = firefly_api.list_transactions(
        start="2024-01-01", end=f"{date.today()}"
    )

    kresus._reconciliate_transaction()

    missing_transactions = check_kresus_missing_transactions(
        local_transactions=kresus.transaction_list,
        transactions_list=firefly_transactions_list,
    )
    logger.info(
        f"{len(missing_transactions)} missing transactions from Kresus({len(kresus.transaction_list)}) to Firefly({len(firefly_transactions_list)})"
    )

    if len(missing_transactions) > 0:
        logger.info(f"{missing_transactions[0].type=}")
        logger.info(f"{missing_transactions[0].amount=}")
        logger.info(f"{missing_transactions[0].date=}")
        logger.info(f"{missing_transactions[0].source_name=}")
        logger.info(f"{missing_transactions[0].destination_name=}")
        logger.info(f"{missing_transactions[0].description=}")
        for transaction in missing_transactions:
            logger.info(f"{transaction.type=}")
            logger.info(f"{transaction.amount=}")
            logger.info(f"{transaction.date=}")
            logger.info(f"{transaction.source_name=}")
            logger.info(f"{transaction.destination_name=}")
            logger.info(f"{transaction.description=}\n")
        while True:
            user_input = input(
                f"Do you want to add {len(missing_transactions)}missing transactions to Firefly ? (yes/no): "
            )
            if user_input.lower() in ["yes", "y"]:
                logger.info("Adding missing transactions ...")
                add_missing_transactions(firefly_api, missing_transactions)
                break
            elif user_input.lower() in ["no", "n"]:
                logger.info("Skipping missing transactions...")
                break
            else:
                logger.info("Invalid input. Please enter yes/no.")


def test_create_get_delete_fireflyapi(firefly_api: FireflyIIIAPI):
    """
    Tests the creation, retrieval, and deletion of transactions in Firefly III.

    Args:
        firefly_api (FireflyIIIAPI): An instance of the FireflyIIIAPI class.
    """
    transaction_data = {
        "apply_rules": True,
        "fire_webhooks": True,
        "transactions": [
            {
                "type": "transfer",
                "date": f"{date.today()}",
                "amount": "200",
                "description": "test_create_get_delete_fireflyapi from python",
                "source_name": "Crédit Agricole Courant",
                "destination_name": "Boursorama CTO",
                "category_name": "",
                "interest_date": "",
                "book_date": "",
                "process_date": "",
                "due_date": "",
                "payment_date": "",
                "invoice_date": "",
                "internal_reference": "",
                "notes": "Created from python",
                "external_url": "",
            }
        ],
    }

    new_transaction = firefly_api.store_transaction(transaction_data)

    if new_transaction:
        logger.info(f"Nouvelle transaction : {new_transaction}")
        transaction_in_db = firefly_api.get_transaction(new_transaction.transaction_id)
        logger.info(f"{(new_transaction == transaction_in_db)=}")

    updated_new_transaction_data = {
        "apply_rules": True,
        "fire_webhooks": True,
        "transactions": [
            {
                "type": "transfer",
                "date": f"{date.today()}",
                "amount": "500",
                "description": "test_create_get_delete_fireflyapi from python",
                "source_name": "Crédit Agricole Courant",
                "destination_name": "Boursorama CTO",
                "category_name": "",
                "interest_date": "",
                "book_date": "",
                "process_date": "",
                "due_date": "",
                "payment_date": "",
                "invoice_date": "",
                "internal_reference": "",
                "notes": "Updated from python",
                "external_url": "",
            }
        ],
    }

    update_transaction = firefly_api.update_transaction(new_transaction.transaction_id, updated_new_transaction_data)
    updated_new_transaction = Transaction(**updated_new_transaction_data["transactions"][0])

    logger.info(f"{(update_transaction == updated_new_transaction)=}")

    transactions_list = firefly_api.list_transactions(
        start=f"{date.today() - relativedelta(months=1)}", end=f"{date.today()}"
    )

    if update_transaction in transactions_list:
        logger.info("Nouvelle transaction dans la liste des transactions")
        logger.info("Deletion de la transaction")
        deleted_transaction = firefly_api.delete_transaction(
            update_transaction.transaction_id
        )
        logger.info(f"transaction {update_transaction} deleted")
    else:
        logger.error("Nouvelle transaction n'est pas dans la liste des transactions")
        raise Exception("Nouvelle transaction n'est pas dans la liste des transactions")
    transactions_list = firefly_api.list_transactions(
        start=f"{date.today() - relativedelta(months=1)}", end=f"{date.today()}"
    )

    if update_transaction not in transactions_list:
        logger.info("Nouvelle transaction n'est plus dans la liste des transactions")


def check_kersus_firefly_accout(firefly_api: FireflyIIIAPI, kresus: Kresus):
    """
    Compares account balances in Kresus with those in Firefly III.

    Args:
        firefly_api (FireflyIIIAPI): An instance of the FireflyIIIAPI class.
        kresus (Kresus): An instance of the Kresus class.
    """
    fault_account : list[str] = []
    for kresus_account in kresus.list_accounts_to_sync:
        for firefly_account in firefly_api.list_accounts():
            if kresus_account.name == firefly_account.name:
                if kresus_account.current_balance != firefly_account.current_balance:
                    logger.info(
                        f"Account '{kresus_account.name}' balance is not up to date : {kresus_account.current_balance=} == {firefly_account.current_balance=} : {kresus_account.current_balance == firefly_account.current_balance} "
                    )
    if len(fault_account) > 0:
        logger.info(f"{len(fault_account)} accounts are not up to date")
        logger.info(f"list of faulty account : {fault_account}")
    else:
        logger.info(f"All account are up to date, great !")