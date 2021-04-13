import importlib

import configs
from monitor_logger.logger import get_logger


logger = get_logger()


def get_controller():
    controller_module, controller = configs.CONTROLLER.rsplit('.', 1)
    try:
        controller_class = getattr(importlib.import_module(controller_module), controller)
    except (AttributeError, ModuleNotFoundError):
        logger.error('controllers.get_controllers: %s', 'not found class')
    return controller_class()
