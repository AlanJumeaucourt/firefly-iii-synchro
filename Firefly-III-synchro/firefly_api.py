from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime, date
import aiohttp
import logging
from models import Account, Transaction

logger = logging.getLogger(__name__)

class FireflyAPIError(Exception):
    """Base exception for Firefly III API errors."""

@dataclass
class PaginatedResponse:
    data: List[Dict[str, Any]]
    total_pages: int

class FireflyIIIAPI:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> FireflyIIIAPI:
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        if not self.session:
            raise FireflyAPIError("Session not initialized. Use 'async with' to create a session.")
        
        url = f"{self.api_url}/{endpoint}"
        
        # Filter out None values from params
        if 'params' in kwargs:
            kwargs['params'] = {k: v for k, v in kwargs['params'].items() if v is not None}
        
        async with self.session.request(method, url, **kwargs) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise FireflyAPIError(f"API request failed: {response.status} - {await response.text()}")

    async def get_about_info(self) -> Dict[str, Any]:
        return await self._make_request("GET", "about")

    async def _get_paginated_data(self, endpoint: str, params: Dict[str, Any]) -> PaginatedResponse:
        response = await self._make_request("GET", endpoint, params=params)
        return PaginatedResponse(
            data=response["data"],
            total_pages=response["meta"]["pagination"]["total_pages"]
        )

    async def list_accounts(self, date: Optional[str] = None, account_type: Optional[str] = None) -> List[Account]:
        params = {"date": date, "type": account_type}
        accounts = []

        async for page in self._paginate("accounts", params):
            accounts.extend(self._process_account_data(page.data))

        return sorted(accounts, key=lambda x: x.account_id or 0)

    async def list_transactions(self, start: Optional[str] = None, end: Optional[str] = None, transaction_type: Optional[str] = None) -> List[Transaction]:
        params = {"start": start, "end": end, "type": transaction_type}
        transactions = []

        async for page in self._paginate("transactions", params):
            transactions.extend(self._process_transaction_data(page.data))

        return sorted(transactions, key=lambda x: x.transaction_id or 0)

    async def _paginate(self, endpoint: str, params: Dict[str, Any]) -> AsyncGenerator[PaginatedResponse, None]:
        page = 1
        while True:
            params["page"] = page
            response = await self._get_paginated_data(endpoint, params)
            yield response
            if page >= response.total_pages:
                break
            page += 1

    def _process_account_data(self, data: List[Dict[str, Any]]) -> List[Account]:
        return [Account(**self._extract_account_attributes(item)) for item in data]

    def _process_transaction_data(self, data: List[Dict[str, Any]]) -> List[Transaction]:
        return [Transaction(**self._extract_transaction_attributes(item)) for item in data]

    def _extract_account_attributes(self, item: Dict[str, Any]) -> Dict[str, Any]:
        attributes = item["attributes"]
        return {
            "account_id": item["id"],
            "account_type": item["type"],
            **{k: v for k, v in attributes.items() if k in Account.__annotations__ and v is not None}
        }

    def _extract_transaction_attributes(self, item: Dict[str, Any]) -> Dict[str, Any]:
        attributes = item.get("attributes", {})
        if "transactions" in attributes:
            attributes = attributes["transactions"][0]
        
        # Ensure date and amount are properly extracted
        transaction_date = datetime.fromisoformat(attributes['date']).date()
        amount = float(attributes['amount'])

        result = {
            "transaction_id": item.get("id"),
            "date": transaction_date,
            "amount": amount,
            "type": attributes.get('type'),
            "description": attributes.get('description'),
            "source_name": attributes.get('source_name'),
            "destination_name": attributes.get('destination_name'),
        }

        # Add other attributes that exist in Transaction.__annotations__
        for k, v in attributes.items():
            if k in Transaction.__annotations__ and k not in result:
                result[k] = v

        return result

    async def store_transaction(self, transaction: Transaction) -> Transaction:
        data = {
            "transactions": [{
                "type": transaction.type,
                "date": transaction.date.isoformat(),
                "amount": str(transaction.amount),
                "description": transaction.description,
                "source_name": transaction.source_name,
                "destination_name": transaction.destination_name,
            }]
        }
        # Remove None values
        data["transactions"][0] = {k: v for k, v in data["transactions"][0].items() if v is not None}
        response = await self._make_request("POST", "transactions", json=data)
        
        logger.info(f"Store transaction response: {response}")
        
        if isinstance(response["data"], list):
            return self._process_transaction_data(response["data"])[0]
        else:
            return self._process_transaction_data([response["data"]])[0]

    async def get_transaction(self, transaction_id: int) -> Transaction:
        response = await self._make_request("GET", f"transactions/{transaction_id}")
        return self._process_transaction_data(response["data"])[0]

    async def update_transaction(self, transaction: Transaction) -> Transaction:
        data = {
            "transactions": [{
                "type": transaction.type,
                "date": transaction.date.isoformat(),
                "amount": str(transaction.amount),
                "description": transaction.description,
                "source_name": transaction.source_name,
                "destination_name": transaction.destination_name,
            }]
        }
        # Remove None values
        data["transactions"][0] = {k: v for k, v in data["transactions"][0].items() if v is not None}
        response = await self._make_request("PUT", f"transactions/{transaction.transaction_id}", json=data)
        return self._process_transaction_data(response["data"])[0]

    async def delete_transaction(self, transaction_id: int) -> None:
        await self._make_request("DELETE", f"transactions/{transaction_id}")

# Usage example:
async def main():
    async with FireflyIIIAPI("https://your-firefly-instance.com/api", "your-api-token") as api:
        accounts = await api.list_accounts()
        for account in accounts:
            print(account)

        transactions = await api.list_transactions(start="2023-01-01", end="2023-12-31")
        for transaction in transactions:
            print(transaction)

if __name__ == "__main__":
    asyncio.run(main())