import logging
from logging import Logger
import sys


def timed_named_logger(logger_name: str) -> Logger:
    formatter = logging.Formatter(
        fmt = f"[%(asctime)s] [%(levelname)s] [{logger_name}] %(message)s",
        datefmt = '%Y-%m-%d %H:%M:%S')
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.addHandler(screen_handler)
    return logger
