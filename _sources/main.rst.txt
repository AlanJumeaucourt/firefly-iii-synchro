.. _main:

Main script
===========

The `main` module serves as the entry point of the Firefly III Synchronization Tool. It orchestrates various components of the application, managing the flow of operations from initialization to execution.

Overview
--------

The main module initializes key components such as the Firefly III API wrapper and the Kresus instance. It handles the entire workflow, including testing the Firefly API, fetching and processing data from Kresus, synchronizing data with Firefly III, and updating local data.

Workflow
--------

The workflow in the `main` module includes:

- Setting up logging for the application.
- Loading environment variables from a `.env` file or falling back to default values.
- Initializing the `FireflyIIIAPI` with configuration details.
- Performing a full test of the Firefly API.
- Initializing the `Kresus` instance and checking Kresus data against Firefly III.
- Parsing account and transaction data from Kresus.
- Updating local data and synchronizing it with Firefly III.
- Optionally, exporting transaction data to a CSV file.

Functions
---------

The main script primarily focuses on orchestrating the application flow:

.. autofunction:: main



Example Usage
-------------

The main script is executed to run the application:

.. code-block:: python

    if __name__ == "__main__":
        main()

This command initiates the various functionalities encapsulated within the `main` function, leveraging the different modules and classes of the application.

Configuration
-------------

The script uses variables for configuration, loaded from a `.env` file then from environment (prefixed with `F3S_`) . It falls back to default values if these variables are not set:

In the .env file :

- `FIREBASE_URL`: The base URL of the Firefly III instance.
- `API_TOKEN`: The API token for Firefly III.

If you want to use environment variables instead, prefixe them with `F3S_` :

.. code-block:: bash

    export F3S_FIREBASE_URL = 'https://your-firefly-instance.com/api/v1'


These variables are essential for the initialization and operation of the `FireflyIIIAPI`.

Note
----

The `main` module is crucial for understanding the overall flow and execution of the application. It combines various aspects of the tool into a coherent workflow, demonstrating how they interact in a real-world scenario.
