.. _logging-config:

Logging Configuration
=====================

The `logging_config` module is responsible for setting up and configuring logging across the Firefly III Synchronization Tool. It defines a custom logging formatter and a setup function to initialize logging with the desired settings.

CustomFormatter
---------------

The `CustomFormatter` class in the `logging_config` module provides a custom logging formatter. This formatter adds color coding and additional formatting to make log messages more readable and distinguishable based on their level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

.. autoclass:: logging_config.CustomFormatter
    :members:

setup_logging
-------------

The `setup_logging` function configures the global logging level and applies the custom formatter to all log messages. This function should be called at the beginning of the script to ensure that all subsequent logging follows the configured format.

.. autofunction:: logging_config.setup_logging

Usage
-----

To use the logging configuration in your application, import the `setup_logging` function from the `logging_config` module and call it at the start of your application. Then, create logger instances in each module using `logging.getLogger(__name__)`.

Example::

    from logging_config import setup_logging

    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Logging is configured and ready to use.")

This setup will apply the custom logging format across your application, making log messages consistent and more informative.

