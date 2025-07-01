"""Logging module"""

import logging
import sys
from typing import Optional

class ColorFormatter(logging.Formatter):
    # Define color codes for different log levels
    COLORS = {
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',   # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',   # Red
        'CRITICAL': '\033[1;41m',  # Red background
    }

    RESET = '\033[0m'

    def format(self, record):
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)

LOGGING_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


DebugLevels = ["DEBUG", "INFO", "WARNING", "ERROR"]
DebugLevelType = str


def get_logger(
    name: Optional[str] = None, level: DebugLevelType = "DEBUG"
) -> logging.Logger:
    """
    Creates and configures a logger for logging messages.

    Parameters:
        name (Optional[str]): The name of the logger. Defaults to None.
        level (DebugLevel): The logging level. Defaults to DebugLevel.DEBUG.

    Returns:
        logging.Logger: The configured logger object.
    """
    logger = logging.getLogger(name=name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColorFormatter(LOGGING_FORMATTER)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not level or level not in DebugLevels:
        logger.warning(
            "Invalid logging level %s. Setting logging level to DEBUG.", level
        )
        level = "DEBUG"

    logger.setLevel(level=level)
    return logger