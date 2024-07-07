import logging
import inspect
from typing import Dict, Any, List
from functools import lru_cache
import os

class ColorFormatter(logging.Formatter):
    """
    Custom color formatter for logging, providing a more detailed and colorful log format.
    """
    COLORS = {
        'DEBUG': '\033[94m',  # Light Blue
        'INFO': '\033[92m',   # Light Green
        'WARNING': '\033[93m', # Yellow
        'ERROR': '\033[91m',  # Light Red
        'CRITICAL': '\033[1;91m', # Bold Red
    }
    RESET = '\033[0m'

    def __init__(self, fmt: str):
        super().__init__(fmt)

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.COLORS.get(record.levelname, self.RESET) + self._fmt + self.RESET
        formatter = logging.Formatter(log_fmt)
        record.funcName = self.get_function_name()
        return formatter.format(record)

    @staticmethod
    @lru_cache(maxsize=128)
    def get_function_name() -> str:
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

def setup_logging(
    level: int = logging.INFO,
    log_file: str = None,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
) -> None:
    """
    Set up logging configuration.

    Args:
        level (int): The logging level. Defaults to logging.INFO.
        log_file (str, optional): Path to a log file. If provided, logs will be written to this file.
        format_string (str, optional): Custom format string for log messages.

    Returns:
        None
    """
    handlers: List[logging.Handler] = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter(format_string))
    handlers.append(console_handler)

    # File handler (if log_file is provided)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Disable propagation to prevent duplicate logs
    logging.getLogger().propagate = False

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    return logging.getLogger(name)

# Example usage
if __name__ == "__main__":
    setup_logging(level=logging.DEBUG, log_file="app.log")
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")