from logging import getLogger, Logger, FileHandler, Formatter
import time
import functools
import datetime
from config import Config

def create_logger(config: Config) -> Logger:
    logger = getLogger(config.SIMULATION_NAME)
    logger.setLevel(config.LOG_MODE)
    handler = FileHandler(config.COMMON_LOG_PATH)
    handler.setFormatter(Formatter(fmt=config.LOG_FORMAT))
    logger.addHandler(handler)
    return logger

def time_ns(func, *args, **kwargs):
    t = time.time_ns()
    result = func(*args, **kwargs)
    t = time.time_ns() - t
    return t, result
