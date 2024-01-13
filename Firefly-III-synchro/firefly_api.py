import requests
import logging
from datetime import date
import concurrent.futures
from models import Account, Transaction  # Assuming models.py is in the same directory
from typing import List

logger = logging.getLogger(__name__)


class FireflyIIIAPI:
    """
    A wrapper class for interacting with the Firefly III API.
    Provides methods to list, create, update, and delete accounts and transactions.
    """

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the FireflyIIIAPI instance with the Firefly III base URL and API token.

        Args:
            base_url (str): The base URL of the Firefly III instance.
            api_token (str): The API token for authenticating requests.
        """
        self.base_url = base_url
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        logger.info(f"FireflyIIIAPI initialized with base URL {base_url}")

    def get_about_info(self):
        """
        Retrieves information about the Firefly III instance.

        Returns:
            dict: A dictionary containing about information if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/about"
        try:
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to get about info: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to get about info: {e} with status code {response.status_code} && {response.text}"
            )

    def _list_accounts(
        self, limit=50, page=1, date=None, account_type=None, trace_id=None
    ):
        """
        Internal method to list accounts with pagination and optional filtering.

        Args:
            limit (int): The number of results per page.
            page (int): The page number to retrieve.
            date (str, optional): Date filter for accounts.
            account_type (str, optional): Type of accounts to filter.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            dict: A dictionary containing account data if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/accounts"
        params = {"limit": limit, "page": page}

        if date:
            params["date"] = date

        if account_type:
            params["type"] = account_type

        headers = self.headers.copy()
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.get(endpoint, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to list accounts: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to list accounts: {e} with status code {response.status_code} && {response.text}"
            )

    def _process_list_accounts_response(self, response) -> List[Account]:
        """
        Processes the response from the list accounts request and converts it into a list of Account objects.

        Args:
            response (dict): The response from the list accounts request.

        Returns:
            List[Account]: A list of Account objects.
        """
        accounts_list: List[Account] = []
        if response is not None:
            if isinstance(response["data"], list):
                for account_data in response["data"]:
                    attributes = account_data.get("attributes", {})
                    valid_attributes = {
                        k: v
                        for k, v in attributes.items()
                        if k in Account.__init__.__code__.co_varnames
                    }
                    accounts_list.append(
                        Account(
                            account_id=account_data["id"],
                            account_type=account_data["type"],
                            **valid_attributes,
                        )
                    )
            else:
                attributes = response["data"]["attributes"]["transactions"][0]
                valid_attributes = {
                    k: v
                    for k, v in attributes.items()
                    if k in Account.__init__.__code__.co_varnames
                }
                logger.debug(f"{response['data']=}")
                accounts_list.append(
                    Account(
                        account_id=response["data"]["id"],
                        account_type=response["data"]["type"],
                        name=response["data"]["name"] ** valid_attributes,
                    )
                )

        return accounts_list

    def list_accounts(self, date=None, account_type=None) -> List[Account]:
        """
        Lists accounts from the Firefly III instance with optional filtering.

        Args:
            date (str, optional): Date filter for accounts.
            account_type (str, optional): Type of accounts to filter.

        Returns:
            List[Account]: A list of Account objects.
        """
        accounts_list = []

        # Liste des types de compte valides
        valid_account_types = [
            "all",
            "asset",
            "cash",
            "expense",
            "revenue",
            "special",
            "hidden",
            "liability",
            "liabilities",
            "Default account",
            "Cash account",
            "Asset account",
            "Expense account",
            "Revenue account",
            "Initial balance account",
            "Beneficiary account",
            "Import account",
            "Reconciliation account",
            "Loan",
            "Debt",
            "Mortgage",
        ]

        # Vérifie si le type de compte spécifié est valide
        if account_type and account_type not in valid_account_types:
            raise ValueError(
                "Invalid account type. Please provide a valid account type."
            )

        response = self._list_accounts(date=date, account_type=account_type)

        if response is not None:
            accounts_list += self._process_list_accounts_response(response)

            total_pages = response["meta"]["pagination"]["total_pages"]
            for i in range(1, total_pages):
                response = self._list_accounts(
                    page=i + 1, date=date, account_type=account_type
                )
                if response is not None:
                    accounts_list += self._process_list_accounts_response(response)

        accounts_list.sort(key=lambda x: x.account_id)
        return accounts_list

    def _list_transactions(
        self,
        limit=1000,
        page=1,
        start=None,
        end=None,
        transaction_type=None,
        trace_id=None,
    ):
        """
        Internal method to list transactions with pagination and optional filtering.

        Args:
            limit (int): The number of results per page.
            page (int): The page number to retrieve.
            start (str, optional): Start date for filtering transactions.
            end (str, optional): End date for filtering transactions.
            transaction_type (str, optional): Type of transactions to filter.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            dict: A dictionary containing transaction data if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/transactions"
        params = {"limit": limit, "page": page}

        if start:
            params["start"] = start

        if end:
            params["end"] = end

        if transaction_type:
            params["type"] = transaction_type

        headers = self.headers.copy()
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.get(endpoint, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(
                f"Failing to list transactions: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to list transactions: {e} with status code {response.status_code} && {response.text}"
            )

    def _process_list_transactions_response(self, response) -> List[Transaction]:
        """
        Processes the response from the list transactions request and converts it into a list of Transaction objects.

        Args:
            response (dict): The response from the list transactions request.

        Returns:
            List[Transaction]: A list of Transaction objects.
        """
        transactions_list: List[Transaction] = []
        if response is not None:
            if isinstance(response["data"], list):
                for transaction_data in response["data"]:
                    logger.debug(f"{transaction_data=}")
                    logger.debug(
                        f"{transaction_data['attributes']['transactions'][0]=}"
                    )
                    attributes = transaction_data["attributes"]["transactions"][0]
                    valid_attributes = {
                        k: v
                        for k, v in attributes.items()
                        if k in Transaction.__init__.__code__.co_varnames
                    }
                    logger.debug(f"{valid_attributes=}")
                    transactions_list.append(
                        Transaction(
                            transaction_id=transaction_data["id"], **valid_attributes
                        )
                    )
                    # exit()
            else:
                attributes = response["data"]["attributes"]["transactions"][0]
                valid_attributes = {
                    k: v
                    for k, v in attributes.items()
                    if k in Transaction.__init__.__code__.co_varnames
                }
                logger.debug(f"{valid_attributes=}")
                transactions_list.append(
                    Transaction(
                        transaction_id=response["data"]["id"], **valid_attributes
                    )
                )

        return transactions_list

    def list_transactions(
        self, start=None, end=None, transaction_type=None
    ) -> List[Transaction]:
        """
        Lists transactions from the Firefly III instance with optional filtering.

        Args:
            start (str, optional): Start date for filtering transactions.
            end (str, optional): End date for filtering transactions.
            transaction_type (str, optional): Type of transactions to filter.

        Returns:
            List[Transaction]: A list of Transaction objects.
        """
        transactions_list = []
        valid_transaction_types = [...]  # List of valid transaction types

        # Validate transaction type
        if transaction_type and transaction_type not in valid_transaction_types:
            raise ValueError(
                "Invalid transaction type. Please provide a valid transaction type."
            )

        response = self._list_transactions(
            start=start, end=end, transaction_type=transaction_type
        )

        if response is not None:
            transactions_list += self._process_list_transactions_response(response)

            total_pages = response["meta"]["pagination"]["total_pages"]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_page = {
                    executor.submit(
                        self._list_transactions,
                        page=i + 1,
                        start=start,
                        end=end,
                        transaction_type=transaction_type,
                    ): i
                    + 1
                    for i in range(1, total_pages)
                }
                for future in concurrent.futures.as_completed(future_to_page):
                    page = future_to_page[future]
                    try:
                        response = future.result()
                        if response is not None:
                            transactions_list += (
                                self._process_list_transactions_response(response)
                            )
                    except Exception as e:
                        logger.error(
                            f"Failing to list transactions: {e} with status code {response.status_code} && {response.text}"
                        )
                        raise Exception(
                            f"Error retrieving transactions for page {page}: {e}"
                        )

        transactions_list.sort(key=lambda x: x.transaction_id)
        return transactions_list

    def store_transaction(self, transaction_data, trace_id=None):
        """
        Stores a new transaction in the Firefly III instance.

        Args:
            transaction_data (dict): Data of the transaction to be stored.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            Transaction: The stored Transaction object if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/transactions"
        headers = self.headers.copy()

        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.post(endpoint, headers=headers, json=transaction_data)
            logger.debug(response.text)
            if response.status_code == 200:
                return self._process_list_transactions_response(response.json())[0]
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to store transaction: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to store transaction: {e} with status code {response.status_code} && {response.text}"
            )

    def get_transaction(self, transaction_id, trace_id=None):
        """
        Retrieves a specific transaction by its ID from the Firefly III instance.

        Args:
            transaction_id (int): The ID of the transaction to retrieve.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            Transaction: The requested Transaction object if found, else raises an exception.
        """
        endpoint = f"{self.base_url}/transactions/{transaction_id}"
        headers = self.headers.copy()

        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                return self._process_list_transactions_response(response.json())[0]
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to get transaction: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to get transaction: {e} with status code {response.status_code} && {response.text}"
            )

    def delete_transaction(self, transaction_id, trace_id=None):
        """
        Deletes a specific transaction by its ID from the Firefly III instance.

        Args:
            transaction_id (int): The ID of the transaction to delete.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            str: A confirmation message if the transaction is successfully deleted, else raises an exception.
        """
        endpoint = f"{self.base_url}/transactions/{transaction_id}"
        headers = self.headers.copy()

        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.delete(endpoint, headers=headers)
            if response.status_code == 204:
                return "Transaction deleted."
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to delete transaction: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to delete transaction: {e} with status code {response.status_code} && {response.text}"
            )

    def store_account(self, account_data, trace_id=None):
        """
        Stores a new account in the Firefly III instance.

        Args:
            account_data (dict): Data of the account to be stored.
            trace_id (str, optional): Trace ID for the request.

        Returns:
            Account: The stored Account object if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/accounts/store"
        headers = self.headers.copy()

        if trace_id:
            headers["X-Trace-Id"] = trace_id

        try:
            response = requests.post(endpoint, headers=headers, json=account_data)
            if response.status_code == 200:
                logger.info(response)
                logger.info(f"{response.text=}")
                return self._process_list_accounts_response(response.json())[0]
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to store account: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to store account: {e} with status code {response.status_code} && {response.text}"
            )

    def update_transaction(self, transaction_id, updated_transaction_data):
        """
        Updates a specific transaction by its ID in the Firefly III instance.

        Args:
            transaction_id (int): The ID of the transaction to update.
            updated_transaction_data (dict): The new data for updating the transaction.

        Returns:
            Transaction: The updated Transaction object if successful, else raises an exception.
        """
        endpoint = f"{self.base_url}/transactions/{transaction_id}"
        headers = self.headers

        try:
            response = requests.put(
                endpoint, headers=headers, json=updated_transaction_data
            )
            if response.status_code == 200:
                return self._process_list_transactions_response(response.json())[0]
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                f"Failing to update transaction: {e} with status code {response.status_code} && {response.text}"
            )
            raise Exception(
                f"Failing to update transaction: {e} with status code {response.status_code} && {response.text}"
            )
