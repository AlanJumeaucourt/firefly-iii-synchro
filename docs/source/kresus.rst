.. _kresus:

Kresus Integration
==================

The `kresus` module in the Firefly III Synchronization Tool is designed to handle data obtained from Kresus, a personal finance management tool. It provides functionalities for parsing and processing financial data from Kresus.

Kresus Class
------------

The `Kresus` class is the main component of this module. It offers methods to retrieve, parse, and process accounts and transactions data from Kresus, facilitating their integration with the Firefly III system.

.. autoclass:: kresus.Kresus
    :members:

Usage
-----

The `Kresus` class is used to interact with Kresus data. After initializing an instance, you can fetch, parse, and process data from Kresus, preparing it for synchronization with Firefly III or other operations within the application.

Example::

    from kresus import Kresus

    # Initialize Kresus instance
    kresus = Kresus()

    # Fetch and process data from Kresus
    kresus.get_all_kresus()
    kresus.parse_account()
    kresus.parse_transactions(date="2024-01-01")

    # The data can now be used for further processing or synchronization

This setup allows for effective management and synchronization of financial data from Kresus in the application.

