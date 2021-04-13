import configs
from monitor_logger.logger import get_logger
from tools import visualize_box_mask

logger = get_logger()


def local_handler(frame, result):
    last_bad_image = visualize_box_mask(frame, result, configs.PREDICT_LABELS)
    last_bad_image.save('last_bad_image.jpg', quality=95)
    logger.info('handlers.local_handler: %s', 'save last image as last_bad_image.jpg')
    