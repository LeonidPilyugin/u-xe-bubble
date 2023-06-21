import time
from logging import getLogger
from logging import Logger
from logging import FileHandler
from logging import Formatter
from config import Config



def create_logger(config: Config, type_: str) -> Logger:
    """Creates logger"""
    
    TYPE_PROPERTY_ = {
        "main": config.MAIN_LOG_PATH,
        "analysis": config.ANALYSIS_LOG_PATH,
    }
    
    logger = getLogger(f"{config.SIMULATION_NAME}.{type_}")
    
    logger.setLevel(config.LOG_MODE)
    
    handler = FileHandler(TYPE_PROPERTY_[type_])
    handler.setFormatter(Formatter(fmt=config.LOG_FORMAT))
    logger.addHandler(handler)
    
    return logger


def time_ns(func, *args, **kwargs):
    """Returns time function execution took"""
    
    t = time.time_ns()
    result = func(*args, **kwargs)
    t = time.time_ns() - t
    
    return t, result
