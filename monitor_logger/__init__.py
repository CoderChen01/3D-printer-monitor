import logging

import configs


_logger = logging.getLogger(configs.LOGGER_NAME)
_logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('monitor.log', mode='w')
fh.setLevel(logging.ERROR)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formater = logging.Formatter('%(asctime)s %(name)s'
                             ' %(levelname)s %(message)s')
fh.setFormatter(formater)
ch.setFormatter(formater)
_logger.addHandler(fh)
_logger.addHandler(ch)
