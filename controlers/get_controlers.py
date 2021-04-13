import importlib

import configs
from monitor_logger.logger import get_logger


logger = get_logger()


def get_controler():
    controler_module, controler = configs.CONTROLER.rsplit('.', 1)
    try:
        controler_class = getattr(importlib.import_module(controler_module), controler)
    except (AttributeError, ModuleNotFoundError):
        logger.error('controlers.get_controlers: %s', 'not found class')
    return controler_class()
