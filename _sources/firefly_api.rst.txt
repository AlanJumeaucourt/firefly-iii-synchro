.. _firefly-api:

Firefly III API Wrapper
=======================

The `firefly_api` module provides a Python wrapper for the Firefly III API, encapsulating all the interactions with the Firefly III server. This includes functionalities for managing accounts, transactions, and other related data.

FireflyIIIAPI Class
-------------------

The `FireflyIIIAPI` class is the core of the `firefly_api` module. It offers various methods to interact with the Firefly III API, such as retrieving account information, listing transactions, and updating data on the server.

.. autoclass:: firefly_api.FireflyIIIAPI
    :members:

Usage
-----

To use the `FireflyIIIAPI` class, initialize it with the base URL of your Firefly III instance and the API token. Once initialized, you can call its methods to perform various operations with the Firefly III server.

Example::

    from firefly_api import FireflyIIIAPI

    # Initialize the API wrapper
    api = FireflyIIIAPI(base_url="https://your-firefly-instance.com/api/v1", api_token="your_api_token")

    # Fetching account data
    accounts = api.list_accounts()

    # Listing transactions for a specific period
    transactions = api.list_transactions(start="2024-01-01", end="2024-01-31")

This setup allows for seamless integration with Firefly III, enabling the application to manage financial data effectively.

