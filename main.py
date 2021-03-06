import logging
from uuid import uuid4

from monitors import LocalMonitor


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('monitor.log', mode='w')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formater = logging.Formatter('%(asctime)s %(name)s'
                             ' %(levelname)s %(message)s')
fh.setFormatter(formater)
ch.setFormatter(formater)

logger.addHandler(fh)
logger.addHandler(ch)

monitor = LocalMonitor(uuid4(), 200, 5, event_num=2)
monitor.run()