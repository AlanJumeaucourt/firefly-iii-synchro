import logging
from typing import List
from datetime import date
from dateutil.relativedelta import relativedelta
from abc import ABC, abstractmethod

from firefly_api import FireflyIIIAPI
from kresus import Kresus
from models import Transaction, Account
from logging_config import setup_logging
from dotenv import load_dotenv
import os
import math

logger = logging.getLogger(__name__)

setup_logging()


class FinancialSyncManager:
    def __init__(self, firefly_api: FireflyIIIAPI, kresus: Kresus):
        self.firefly_api = firefly_api
        self.kresus = kresus

    def sync_kresus_to_firefly(self, start_date: str) -> bool:
        self.kresus.parse_transactions(date=start_date)
        firefly_transactions = self.firefly_api.list_transactions(
            start=start_date, end=str(date.today())
        )
        missing_transactions = self._check_missing_transactions(
            self.kresus.transaction_list, firefly_transactions
        )

        if missing_transactions:
            self._log_missing_transactions(missing_transactions)
            if self._confirm_add_transactions(len(missing_transactions)):
                self._add_missing_transactions(missing_transactions)
                return True
        return False

    def check_account_balances(self):
        kresus_accounts = self.kresus.list_accounts_to_sync
        firefly_accounts = self.firefly_api.list_accounts()
        mismatched_accounts = self._compare_account_balances(
            kresus_accounts, firefly_accounts
        )
        self._log_account_balance_results(mismatched_accounts)

    def _check_missing_transactions(
        self,
        local_transactions: List[Transaction],
        distant_transaction: List[Transaction],
    ) -> List[Transaction]:
        missing_transactions: List[Transaction] = []

        for local_transaction in local_transactions:
            match_found = False
            for transaction in distant_transaction:
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

    def _add_missing_transactions(self, missing_transactions: List[Transaction]):
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
            self.firefly_api.store_transaction(transaction_data=transaction_data)

    def _compare_account_balances(
        self, kresus_accounts: List[Account], firefly_accounts: List[Account]
    ) -> List[str]:
        fault_account: list[str] = []
        for kresus_account in kresus_accounts:
            for firefly_account in self.firefly_api.list_accounts():
                if kresus_account.name == firefly_account.name:
                    if (
                        kresus_account.current_balance
                        != firefly_account.current_balance
                    ):
                        logger.info(
                            f"Account '{kresus_account.name}' balance is not up to date : {kresus_account.current_balance=} == {firefly_account.current_balance=} : {kresus_account.current_balance == firefly_account.current_balance} "
                        )
        return fault_account

    def _log_missing_transactions(self, missing_transactions: List[Transaction]):
        for transaction in missing_transactions:
            logger.info(f"Missing transaction: {transaction}")

    def _confirm_add_transactions(self, count: int) -> bool:
        return input(
            f"Do you want to add {count} missing transactions to Firefly? (yes/no): "
        ).lower() in ["yes", "y"]

    def _log_account_balance_results(self, mismatched_accounts: List[str]):
        if mismatched_accounts:
            logger.info(f"{len(mismatched_accounts)} accounts are not up to date")
            logger.info(f"List of mismatched accounts: {mismatched_accounts}")
        else:
            logger.info("All accounts are up to date")


class APITester(ABC):
    @abstractmethod
    def test_api(self):
        pass


class FireflyAPITester(APITester):
    def __init__(self, firefly_api: FireflyIIIAPI):
        self.firefly_api = firefly_api

    def test_api(self):
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

        new_transaction = self.firefly_api.store_transaction(transaction_data)

        if new_transaction:
            logger.info(f"Nouvelle transaction : {new_transaction}")
            transaction_in_db = self.firefly_api.get_transaction(
                new_transaction.transaction_id
            )
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

        update_transaction = self.firefly_api.update_transaction(
            new_transaction.transaction_id, updated_new_transaction_data
        )
        updated_new_transaction = Transaction(
            **updated_new_transaction_data["transactions"][0]
        )

        logger.info(f"{(update_transaction == updated_new_transaction)=}")

        transactions_list = self.firefly_api.list_transactions(
            start=f"{date.today() - relativedelta(months=1)}", end=f"{date.today()}"
        )

        if update_transaction in transactions_list:
            logger.info("Nouvelle transaction dans la liste des transactions")
            logger.info("Deletion de la transaction")
            deleted_transaction = self.firefly_api.delete_transaction(
                update_transaction.transaction_id
            )
            logger.info(f"transaction {update_transaction} deleted")
        else:
            logger.error(
                "Nouvelle transaction n'est pas dans la liste des transactions"
            )
            raise Exception(
                "Nouvelle transaction n'est pas dans la liste des transactions"
            )
        transactions_list = self.firefly_api.list_transactions(
            start=f"{date.today() - relativedelta(months=1)}", end=f"{date.today()}"
        )

        if update_transaction not in transactions_list:
            logger.info(
                "Nouvelle transaction n'est plus dans la liste des transactions"
            )


class ConfigLoader:
    @staticmethod
    def load_env_var(var_name: str) -> str:
        var = os.getenv(var_name)
        if var is None:
            raise EnvironmentError(f"{var_name} environment variable is not set")
        return var

    @staticmethod
    def load_config():
        load_dotenv()
        return {
            "firefly_api_url": ConfigLoader.load_env_var("FIREFLY_API_URL"),
            "firefly_api_token": ConfigLoader.load_env_var("FIREFLY_API_TOKEN"),
            "kresus_api_url": ConfigLoader.load_env_var("KRESUS_API_URL"),
            "start_date": ConfigLoader.load_env_var("START_DATE"),
        }


def main():
    try:
        config = ConfigLoader.load_config()
        logger.info(f"Configuration loaded: {config}")

        firefly_api = FireflyIIIAPI(
            config["firefly_api_url"], config["firefly_api_token"]
        )
        kresus = Kresus(config["kresus_api_url"])

        api_tester = FireflyAPITester(firefly_api)
        api_tester.test_api()
        sync_manager = FinancialSyncManager(firefly_api, kresus)

        kresus.get_all_kresus()
        kresus.parse_account()
        sync_manager.check_account_balances()

        transactions_added = sync_manager.sync_kresus_to_firefly(config["start_date"])
        logger.info(f"Transactions added: {transactions_added}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e


if __name__ == "__main__":
    main()
