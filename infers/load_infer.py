import importlib

import configs
from monitor_logger.logger import get_logger

logger = get_logger()


def get_infer():
    try:
        module = importlib.import_module(configs.INFER)
    except Exception:
        logger.error('infers.load_infer.get_infer: %s',
                     'The Infer parameter can only be paddle_inference_infer'
                     ' or paddlelite_infer!')
        return
    return importlib.import_module(configs.INFER)
