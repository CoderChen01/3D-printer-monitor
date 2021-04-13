import time

import configs
from monitor_logger.logger import get_logger
from infers.load_infer import get_infer
from handlers import local_handler
from tools import GoodVideoCpature
from .monitors import Monitor

logger = get_logger()


__all__ = ['LocalMonitor',]


class LocalMonitor(Monitor):
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5,
                 event_num=5):
        super(LocalMonitor, self).__init__(uuid,
                                           all_time,
                                           inspection_interval,
                                           failure_num)
        self.event_num = event_num

    def run(self):
        return self._run_monitor()

    def _handler(self):
        event_num = 0
        infer = get_infer()
        if not infer:
            self.set_run_status(False)
            return
        predictor = infer.Detector()
        start_time = time.time()
        while True:
            if time.time() - start_time >= self.all_time:
                self.set_run_status(False)
                return
            if not self.get_run_status():
                return
            if event_num == self.event_num:
                logger.info('LocalMonitor._handler: %s',
                            'When the number of detection'
                            ' events exceeds the predetermined threshold,'
                            ' the switch is automatically turned off')
                local_handler(frame, result)
                self.set_run_status(False)
                event_num = 0
                self._shutdown()
                return
            data = self.shared_queue.get()
            frame = data['frame']
            current_time = data['current_time']
            logger.info('LocalMonitor._handler: %s',
                         'predict at ' + current_time)
            result = predictor.predict(frame)
            if result.get('num', 0) <= self.failure_num:
                logger.info('LocalMonitor._handler: %s',
                             'good work. event num: %d/%d failure num: %d/%d' % (event_num,
                                                                                  self.event_num,
                                                                                  result.get('num', 0),
                                                                                  self.failure_num))
                continue
            event_num += 1
            logger.info('LocalMonitor._handler: %s',
                             'bad work!!! event num: %d/%d failure num: %d/%d' % (event_num,
                                                                                  self.event_num,
                                                                                  result.get('num', 0),
                                                                                  self.failure_num))
