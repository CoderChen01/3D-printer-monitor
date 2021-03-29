import logging

import configs

def get_logger():
    return logging.getLogger(configs.LOGGER_NAME)
