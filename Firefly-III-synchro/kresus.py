import logging
from typing import List, Any
import requests
from datetime import datetime
from models import Account, Transaction
import inspect
import aiohttp

logger = logging.getLogger(__name__)


class Kresus:
    def __init__(self, api_url) -> None:
        self.data: Any = {}
        self.list_accounts_to_sync: list[Account] = []
        self.transaction_list: list[Transaction] = []
        logger.info("Kresus instance created")
        self.api_url = api_url

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
    
    async def get_all_kresus(self):
        function_name = inspect.currentframe().f_code.co_name

        async with self.session.get(self.api_url) as response:
            if response.status == 200:
                logger.info("Request of all kresus data successful")
                self.data = await response.json()
            else:
                logger.error(f"{function_name} : Request failed with status code {response.status}")
                raise Exception(f"{function_name} : Request failed with status code {response.status}")


            # self.data format of list from kresus :
            # [{
            #     "type": "account-type.loan",      # account-type.checking, account-type.pea, account-type.market
            #     "customLabel": None,
            #     "iban": None,
            #     "currency": "EUR",
            #     "excludeFromBalance": False,
            #     "balance": -10818.3,
            #     "id": 10,
            #     "userId": 1,
            #     "accessId": 1,
            #     "vendorAccountId": "10001710222",
            #     "importDate": "2024-01-04T11:30:32.471Z",
            #     "initialBalance": -12546.63,
            #     "lastCheckDate": "2024-07-05T03:35:48.587Z",
            #     "label": "Prêt etudiant",
            # }]


    def parse_account(self):
        csv_accounts: list[str] = [
            "Crédit Agricole Courant",
            "Crédit Agricole LEP",
            "Crédit Agricole Livret Jeune",
            "Crédit Agricole LDDS",
            "Boursorama Courant",
            "Boursorama CTO",
            "Boursorama Espèce CTO",
            "Boursorama PEA",
            "Boursorama Espèce PEA",
            "Edenred Ticket restaurant",
            "Lydia Courant",
            "Lendermarket P2P",
            "Twino P2P",
            "Miimosa P2P",
            "Raizers P2P",
            "Wiseed P2P",
            "Abeille Vie Assurance Vie",
            "BienPreter P2P",
            "LouveInvest SCPI",
            "Robocash P2P",
            "Fortuneo Courant",
            "Fortuneo CTO",
            "Fortuneo Espèce CTO",
            "Yuzu Crypto",
            "Natixis PEG",
            "Natixis PERCO",
        ]

        account_excluded: List[str] = ["Boursorama CTO", "Boursorama PEA"]

        accounts = self.data["accounts"]
        for account in accounts:
            # account format from kresus :
            # {'type': 'account-type.savings',
            #  'customLabel': 'Crédit Agricole LEP',
            #  'iban': None, 'currency': 'EUR',
            #  'excludeFromBalance': False,
            #  'balance': 10486.16, 'id': 3,
            #  'userId': 1, 'accessId': 1,
            #  'vendorAccountId': '36127791516',
            #  'importDate': '2024-01-04T11:30:32.471Z',
            #  'initialBalance': 7700, 'lastCheckDate':
            #  '2024-01-11T12:53:22.973Z',
            #  'label': 'Livret Epargne Populaire'}
            for csv_account in csv_accounts:
                if account["customLabel"] == csv_account:
                    self.list_accounts_to_sync.append(
                        Account(
                            name=account["customLabel"],
                            account_id=account["id"],
                            current_balance=float(account["balance"]),
                            current_balance_date=account["importDate"],
                        )
                    )
                    break

        logger.info(
            f"Number of account to synchronize from kresus : {len(self.list_accounts_to_sync)}"
        )

    def parse_transactions(self, date):
        transactions = self.data["transactions"]
        for transaction in transactions:
            # transaction format from kresus :
            # {'category': None,
            #  'categoryId': None,
            #  'type': 'type.card',
            #  'customLabel': None,
            #  'budgetDate': None,
            #  'debitDate': '2024-01-08T00:00:00.000Z',
            #  'createdByUser': False,
            #  'isUserDefinedType': False,
            #  'isRecurrentTransaction': False,
            #  'id': 959,
            #  'userId': 1,
            #  'accountId': 6,
            #  'label': 'CARTE 05/01 AU DELICE DU BUR VILLEURBANNE',
            #  'rawLabel': 'CARTE 05/01 AU DELICE DU BUR VILLEURBANNE',
            #  'date': '2024-01-05T00:00:00.000Z',
            #  'importDate': '2024-01-11T12:53:36.970Z',
            #  'amount': -12.5}

            if transaction["amount"] < 0:
                transaction_type = "withdrawal"
            elif transaction["amount"] > 0:
                transaction_type = "deposit"
            else:
                logger.error(f"Transaction type could not be detected.")
                raise ValueError("Transaction type could not be detected.")

            def get_account_name_from_id(id):
                for kresus_account in self.list_accounts_to_sync:
                    if id == kresus_account.account_id:
                        logger.debug(
                            f"{kresus_account.account_id} associated to {kresus_account.name}"
                        )
                        return kresus_account.name
                logger.error(f"Account name could not be found for id {id}")
                raise ValueError(f"Account name could not be found for id {id}")

            if datetime.strptime(
                transaction["debitDate"][:10], "%Y-%m-%d"
            ) >= datetime.strptime(date, "%Y-%m-%d"):
                transaction = Transaction(
                    date=transaction["debitDate"][:10],
                    amount=abs(transaction["amount"]),
                    description=transaction["label"],
                    source_name=(
                        get_account_name_from_id(transaction["accountId"])
                        if transaction["amount"] < 0
                        else "Fake Fake"
                    ),
                    destination_name=(
                        get_account_name_from_id(transaction["accountId"])
                        if transaction["amount"] > 0
                        else "Fake Fake"
                    ),
                    type=transaction_type,
                )

                self.transaction_list.append(transaction)

        self.transaction_list.sort(key=lambda x: x.date)

    def reconciliate_transaction(self):
        for i, transaction in enumerate(self.transaction_list):
            if transaction.type == "withdrawal":
                for j, potential_match in enumerate(self.transaction_list):
                    if (
                        potential_match.type == "deposit"
                        and transaction.amount == potential_match.amount
                        and transaction.date == potential_match.date
                        and transaction.source_name != potential_match.source_name
                        and transaction.destination_name
                        != potential_match.destination_name
                    ):
                        if transaction.source_name == potential_match.destination_name:
                            logger.warning(
                                "Edge case while reconciliate transaction: transaction.source_name == potential_match.destination_name, skipping... Possible an aller-retour transaction in the same day. Will ignore both transactions."
                            )
                            self.transaction_list.remove(transaction)
                            self.transaction_list.remove(potential_match)
                            break

                        # Reconcile these transactions as a transfer
                        logger.info(
                            f"Reconciled: {transaction.description} with {potential_match.description}"
                        )

                        # Create a new transfer transaction
                        transfer_transaction = Transaction(
                            date=transaction.date.strftime("%Y-%m-%d"),
                            amount=transaction.amount,
                            type="transfer",
                            description=f"Transfer from {transaction.source_name} to {potential_match.destination_name}",
                            source_name=transaction.source_name,
                            destination_name=potential_match.destination_name,
                        )

                        self.transaction_list.remove(transaction)
                        self.transaction_list.remove(potential_match)
                        self.transaction_list.append(transfer_transaction)

                        break

    async def list_transactions(self, start_date) -> List[Transaction]:
        await self.get_all_kresus()
        self.parse_account()
        self.parse_transactions(start_date)
        self.reconciliate_transaction()
        return self.transaction_list

# Usage example:
async def main():
    async with Kresus("https://your-kresus-instance.com/api") as kresus:
        transactions = await kresus.list_transactions("2023-01-01")
        for transaction in transactions:
            print(transaction)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
