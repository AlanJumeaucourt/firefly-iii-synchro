from __future__ import annotations

import logging
from typing import List, Any, Dict, Optional
import aiohttp
from datetime import datetime
from models import Account, Transaction

logger = logging.getLogger(__name__)


class KresusError(Exception):
    """Base exception for Kresus-related errors."""


class Kresus:
    def __init__(self, api_url: str) -> None:
        self.api_url = api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.data: Dict[str, Any] = {}
        self.accounts: List[Account] = []
        self.transactions: List[Transaction] = []

    async def __aenter__(self) -> Kresus:
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def get_all_kresus(self) -> None:
        if not self.session:
            raise KresusError(
                "Session not initialized. Use 'async with' to create a session."
            )

        async with self.session.get(self.api_url) as response:
            if response.status == 200:
                logger.info("Request of all kresus data successful")
                self.data = await response.json()
            else:
                error_msg = f"Request failed with status code {response.status}"
                logger.error(error_msg)
                raise KresusError(error_msg)

    def parse_accounts(self) -> None:
        csv_accounts = [
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

        accounts_to_exclude = ["Boursorama CTO", "Boursorama PEA"]

        self.accounts = [
            Account(
                name=account["customLabel"],
                account_id=account["id"],
                current_balance=float(account["balance"]),
                current_balance_date=account["importDate"],
            )
            for account in self.data.get("accounts", [])
            if account["customLabel"] in csv_accounts
            and account["customLabel"] not in accounts_to_exclude
        ]

        logger.info(
            f"Number of accounts to synchronize from kresus: {len(self.accounts)}"
        )

    def parse_transactions(self, start_date: str) -> None:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        self.transactions = []
        for transaction in self.data.get("transactions", []):
            transaction_date = datetime.strptime(
                transaction["debitDate"][:10], "%Y-%m-%d"
            ).date()
            if transaction_date >= start_date:
                transaction_type = (
                    "withdrawal" if transaction["amount"] < 0 else "deposit"
                )
                account_name = next(
                    (
                        acc.name
                        for acc in self.accounts
                        if acc.account_id == transaction["accountId"]
                    ),
                    None,
                )

                if account_name:
                    self.transactions.append(
                        Transaction(
                            date=transaction_date,
                            amount=abs(transaction["amount"]),
                            description=transaction["label"],
                            source_name=(
                                account_name
                                if transaction["amount"] < 0
                                else "Fake Fake"
                            ),
                            destination_name=(
                                account_name
                                if transaction["amount"] > 0
                                else "Fake Fake"
                            ),
                            type=transaction_type,
                        )
                    )

        self.transactions.sort(key=lambda x: x.date)

    def reconcile_transactions(self) -> None:
        reconciled_transactions = []
        for i, transaction in enumerate(self.transactions):
            if not transaction:
                break

            if transaction.type == "withdrawal":
                for j, potential_match in enumerate(
                    self.transactions[i + 1 :], start=i + 1
                ):
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
                                "Edge case: transaction.source_name == potential_match.destination_name. Skipping..."
                            )
                            continue

                        logger.info(
                            f"Reconciled: {transaction.description} with {potential_match.description}"
                        )

                        reconciled_transactions.append(
                            Transaction(
                                date=transaction.date,
                                amount=transaction.amount,
                                type="transfer",
                                description=f"Transfer from {transaction.source_name} to {potential_match.destination_name}",
                                source_name=transaction.source_name,
                                destination_name=potential_match.destination_name,
                            )
                        )

                        self.transactions[i] = self.transactions[j] = None
                        break

        self.transactions = [
            t for t in self.transactions if t is not None
        ] + reconciled_transactions
        self.transactions.sort(key=lambda x: x.date)

    async def list_transactions(self, start_date: str) -> List[Transaction]:
        await self.get_all_kresus()
        self.parse_accounts()
        self.parse_transactions(start_date)
        self.reconcile_transactions()
        return self.transactions


# Usage example:
async def main():
    async with Kresus("https://your-kresus-instance.com/api") as kresus:
        transactions = await kresus.list_transactions("2023-01-01")
        for transaction in transactions:
            print(transaction)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
