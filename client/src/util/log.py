"""Helper module for logging-specific functionality"""

import os
import logging
from logging import Logger
import sys

def structure_logger(logger_name: str, logger: Logger):
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    formatter = logging.Formatter(
        fmt=f"[%(asctime)s.%(msecs)03d] [%(levelname)s] [{logger_name}] %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S')
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger.setLevel(log_level)
    logger.addHandler(screen_handler)


# Custom logger
def timed_named_logger(logger_name: str) -> Logger:
    """Create an opinionated, timestamped, named, formatted Logger instance"""
    logger = logging.getLogger(logger_name)
    if not logger.hasHandlers():
        structure_logger(logger_name, logger)
    return logger
