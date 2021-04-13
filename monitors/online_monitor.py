import time

import configs
from monitor_logger.logger import get_logger
from infers.load_infer import get_infer
from handlers import local_handler
from tools import GoodVideoCpature
from .monitors import Monitor

logger = get_logger()


__all__ = ['OnlineMonitor',]


class OnlineMonitor(Monitor):
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 alarm_num=3,
                 alarm_interval=2):
        super(OnlineMonitor, self).__init__(uuid,
                                            all_time,
                                            inspection_interval,
                                            failure_num)
        self.alarm_num = alarm_num
        self.alarm_interval = alarm_interval * 60

    def run(self):
        pass

    def _handler(self):
        pass
