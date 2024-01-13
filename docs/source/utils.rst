.. _firefly-iii-api-script:

Firefly III API Script
======================

This script provides an interface to interact with the Firefly III API. It includes classes and functions for managing accounts and transactions, integrating with Firefly III, and handling local data. 


Functions
---------

.. autofunction:: get_local_transaction

.. autofunction:: get_local_account

.. autofunction:: check_missing_transactions

.. autofunction:: check_kresus_missing_transactions

.. autofunction:: add_missing_transactions

.. autofunction:: dump_transaction_to_csv

.. autofunction:: dump_account_to_csv

.. autofunction:: update_local_to_firefly

.. autofunction:: update_kresus_to_firefly

.. autofunction:: test_create_get_delete_fireflyapi

.. autofunction:: check_kersus_firefly_accout

Usage
-----

This script can be used to synchronize local financial data with a Firefly III instance. It supports operations like listing accounts, adding transactions, updating existing records, and reconciling data between different sources. 

The script includes a test function `test_create_get_delete_fireflyapi` to demonstrate the creation, retrieval, and deletion of transactions through the Firefly III API.

Examples
--------

Here are some examples of how you might use this script:

1. Synchronize transactions from Kresus to Firefly III:

   .. code-block:: python

       kresus = Kresus()
       kresus.get_all_kresus()
       kresus.parse_account()
       kresus.parse_transactions(date="2024-01-01")
       update_kresus_to_firefly()

2. Update local transactions in Firefly III:

   .. code-block:: python

       local_transactions = get_local_transaction()
       firefly_transactions = firefly_api.list_transactions()
       update_local_to_firefly(local_transactions, firefly_transactions)

3. Add missing transactions to Firefly III:

   .. code-block:: python

       local_transactions = get_local_transaction()
       firefly_transactions = firefly_api.list_transactions()
       missing_transactions = check_missing_transactions(local_transactions, firefly_transactions)
       add_missing_transactions(missing_transactions)

Dependencies
------------

- requests
- pandas
- datetime
- logging
- fuzzywuzzy
- concurrent.futures

Note
----

This script is designed to work with Firefly III API and assumes access to a local Excel file for account and transaction data. Adjustments may be needed based on your specific setup and Firefly III API version.

