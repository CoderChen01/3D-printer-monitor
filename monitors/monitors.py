import time
from datetime import datetime
import threading
import multiprocessing as mp

import cv2

import configs
from monitor_logger.logger import get_logger
from controlers import get_controlers
from infers.load_infer import get_infer
from handlers import local_handler
from tools import GoodVideoCpature

logger = get_logger()


class Monitor:
    def __init__(self,
                 uuid,
                 all_time,
                 inspection_interval=10,
                 failure_num=5):
        self._boot()
        self.uuid = uuid
        self.all_time = all_time * 60
        self.inspection_interval = inspection_interval * 60
        self.failure_num = failure_num
        self.shared_queue = mp.Queue()
        self._is_run = mp.Value('i', 0)

    def run(self):
        raise NotImplementedError('You must implement run method')

    def _handler(self):
        raise NotImplementedError('You must implement handler method')

    def _detector(self):
        capture = GoodVideoCpature.create(configs.CAMERA_FILE)
        capture.start_read()
        if not capture.is_started():
            EXIT = -1
            logger.error('Monitor._detector: %s',
                         'Can\'t turn on the camera')
            capture.stop_read()
            capture.release()
            self.set_run_status(False)
            return
        logger.info('Monitor._detector: %s',
                    'Start monitor...')
        start_time = time.time()
        while True:
            if time.time() - start_time >= self.all_time:
                capture.stop_read()
                capture.release()
                self.set_run_status(False)
                return
            if not self.get_run_status():
                capture.stop_read()
                capture.release()
                return
            retval, frame = capture.read_latest_frame()
            if not retval:
                logger.warning('Monitor._detector: %s',
                               'No frame was read')
                continue
            logger.info('Monitor._detector: %s', 'get a frame')
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.shared_queue.put({
                'frame': frame,
                'current_time': current_time
            })
            time.sleep(self.inspection_interval)

    @staticmethod
    def _shutdown():
        controlers = get_controlers()
        controler.shutdown()
        controlers.close()

    @staticmethod
    def _boot():
        controlers = get_controlers()
        controler.shutdown()
        controlers.close()

    def _run_monitor(self):
        self.set_run_status(True)
        d = mp.Process(target=self._detector)
        h = mp.Process(target=self._handler)
        d.start()
        h.start()
        return d, h

    def set_run_status(self, is_run):
        if is_run:
            self._is_run.value = 1
        else:
            self._is_run.value = 0

    def get_run_status(self):
        return self._is_run.value


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
