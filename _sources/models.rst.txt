.. _models:

Data Models
===========

The `models` module contains essential data structures used in the Firefly III Synchronization Tool. This module defines the `Account` and `Transaction` classes, which model the financial data handled by the application.

Account
-------

The `Account` class represents a financial account. It includes various attributes such as account type, balance, currency, and other relevant details.

.. autoclass:: models.Account
    :members:

Transaction
-----------

The `Transaction` class represents a financial transaction. It includes details like the transaction date, amount, type (deposit, withdrawal, transfer), and related account information.

.. autoclass:: models.Transaction
    :members:

Usage
-----

These models are used throughout the application to represent and manipulate financial data. They provide a structured way to handle financial information, facilitating interactions with the Firefly III API and local data processing.

Example::

    from models import Account, Transaction

    # Creating an account instance
    account = Account(name="Checking Account", account_type="asset", current_balance=1000.0)

    # Creating a transaction instance
    transaction = Transaction(date="2024-01-01", amount=150.0, type="deposit", description="Salary")

These instances can then be used in various parts of the application, such as syncing data with Firefly III, processing local data, or generating reports.

