import logging
import inspect


class CustomFormatter(logging.Formatter):
    """Custom formatter for logging, providing a more detailed log format."""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def _get_function_name(self):
        """Retrieve the name of the function that called the logger."""
        # Inspect the stack and find the name of the caller function
        stack = inspect.stack()
        # stack[2] is the caller of the logging function ('info', 'error', etc.)
        # Return the name of the function where the logging call was made.
        # print(stack)
        function_name = stack[9].function
        if function_name == "<module>":
            function_name = stack[8].function
        return function_name

    FORMATS = {
        logging.DEBUG: grey
        + "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s (%(filename)s:%(lineno)d)"
        + reset,
        logging.INFO: grey
        + "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s (%(filename)s:%(lineno)d)"
        + reset,
        logging.WARNING: yellow
        + "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s (%(filename)s:%(lineno)d)"
        + reset,
        logging.ERROR: red
        + "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s (%(filename)s:%(lineno)d)"
        + reset,
        logging.CRITICAL: bold_red
        + "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s (%(filename)s:%(lineno)d)"
        + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        record.funcName = self._get_function_name()
        return formatter.format(record)


def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
    logger.propagate = False


# Example usage
if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging is configured.")
